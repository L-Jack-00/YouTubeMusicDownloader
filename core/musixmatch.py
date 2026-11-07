# -*- coding: utf-8 -*-
"""
Musixmatch Synced Lyrics Client with Anti-Crash & Exponential Backoff Harness.
Supports user token resolution, decoy response filtering, and LRC subtitle fetching.
"""
import os
import re
import time
from typing import Optional, Tuple, Dict, Any
import requests

from .alsong import clean_search_term
from .lyrics_detector import is_romanized_korean_lyrics, has_hangul


ROOT_URL = "https://apic-desktop.musixmatch.com/ws/1.1/"
APP_ID = "web-desktop-app-v1.0"

_cached_token: Optional[str] = None
_token_expiry: float = 0.0


def _request_musixmatch_with_retry(
    url: str,
    params: Dict[str, Any],
    headers: Dict[str, str],
    timeout: int = 4,
    max_retries: int = 2
) -> Optional[requests.Response]:
    """
    Musixmatch API 요청 시 타임아웃, 레이트 리밋(429), 서버 과부하(5xx) 발생 시
    지수 백오프(Exponential Backoff)를 적용하여 안전하게 재시도합니다.
    """
    delay = 0.6
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            elif resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(delay)
                delay *= 1.5
                continue
            elif resp.status_code in (401, 403, 404):
                return None
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            time.sleep(delay)
            delay *= 1.5
            continue
    return None


def _get_local_token() -> Optional[str]:
    """로컬 설정 파일 또는 환경 변수에서 Musixmatch 사용자 토큰 로드"""
    env_token = os.environ.get("MUSIXMATCH_USERTOKEN")
    if env_token and len(env_token.strip()) > 10:
        return env_token.strip()

    from .cookie_util import get_app_root_dir
    for fname in ("session_musixmatch_token.txt", "musixmatch_token.txt"):
        fpath = os.path.join(get_app_root_dir(), fname)
        if os.path.isfile(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as fp:
                    content = fp.read().strip()
                    if content and len(content) > 10 and not content.startswith("00000000"):
                        return content
            except Exception:
                pass
    return None


def get_musixmatch_token(timeout: int = 4) -> Optional[str]:
    """
    유효한 Musixmatch usertoken 획득 (지수 백오프 재시도 적용):
    1. 로컬 저장 토큰 확인
    2. 메모리 캐시 토큰 확인
    3. token.get API 요청 (더미 '000000...' 응답 시 무효 처리)
    """
    global _cached_token, _token_expiry

    local_tok = _get_local_token()
    if local_tok:
        return local_tok

    now = time.time()
    if _cached_token and now < _token_expiry:
        return _cached_token

    try:
        url = f"{ROOT_URL}token.get"
        params = {
            "app_id": APP_ID,
            "user_language": "en",
            "t": str(int(now * 1000))
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        r = _request_musixmatch_with_retry(url, params=params, headers=headers, timeout=timeout, max_retries=2)
        if r and r.status_code == 200:
            data = r.json()
            user_tok = data.get("message", {}).get("body", {}).get("user_token", "")
            # '00000000...' 더미 토큰 차단
            if user_tok and len(user_tok) > 10 and not set(user_tok) == {'0'}:
                _cached_token = user_tok
                _token_expiry = now + 600
                return user_tok
    except Exception:
        pass

    return None


def fetch_musixmatch_lyrics(
    title: str,
    artist: str = "",
    album: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    timeout: int = 5,
    require_korean: bool = False
) -> Optional[Tuple[str, bool]]:
    """
    Musixmatch API를 통해 실시간 싱크 가사(.lrc) 또는 일반 가사를 조회합니다.
    - require_korean=True: 한글 원문 가사만 허용하며 로마자 가사는 배제합니다.
    타임아웃 발생 시 지수 백오프 하네스가 대기 후 재시도합니다.
    성공 시 (가사 내용, 싱크 여부) 반환, 실패 시 None 반환.
    """
    token = get_musixmatch_token(timeout=timeout)
    if not token:
        return None

    c_title = clean_search_term(title)
    c_artist = clean_search_term(artist)
    if not c_title:
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        search_url = f"{ROOT_URL}track.search"
        search_params: Dict[str, Any] = {
            "app_id": APP_ID,
            "usertoken": token,
            "q_track": c_title,
            "page_size": 5,
            "page": 1,
            "s_track_rating": "desc",
            "t": str(int(time.time() * 1000))
        }
        if c_artist:
            search_params["q_artist"] = c_artist
        if duration_seconds and duration_seconds > 0:
            search_params["q_duration"] = duration_seconds

        r = _request_musixmatch_with_retry(search_url, params=search_params, headers=headers, timeout=timeout, max_retries=2)
        if not r or r.status_code != 200:
            return None

        body = r.json().get("message", {}).get("body", {})
        track_list = body.get("track_list", [])
        if not track_list:
            return None

        # 디코이 응답(예: 전혀 다른 곡 Casual 등) 필터링
        norm_q_title = re.sub(r'[\s\W_]+', '', c_title.lower())
        matched_track = None
        for item in track_list:
            trk = item.get("track", {})
            t_name = trk.get("track_name", "")
            norm_t = re.sub(r'[\s\W_]+', '', t_name.lower())
            if norm_q_title in norm_t or norm_t in norm_q_title:
                matched_track = trk
                break

        if not matched_track:
            return None

        track_id = matched_track.get("track_id")
        commontrack_id = matched_track.get("commontrack_id")
        has_subtitles = matched_track.get("has_subtitles", 0)

        # 1. 싱크 가사 조회 (track.subtitle.get)
        if has_subtitles and (track_id or commontrack_id):
            sub_url = f"{ROOT_URL}track.subtitle.get"
            sub_params: Dict[str, Any] = {
                "app_id": APP_ID,
                "usertoken": token,
                "subtitle_format": "lrc",
                "t": str(int(time.time() * 1000))
            }
            if commontrack_id:
                sub_params["commontrack_id"] = commontrack_id
            else:
                sub_params["track_id"] = track_id

            sr = _request_musixmatch_with_retry(sub_url, params=sub_params, headers=headers, timeout=timeout, max_retries=2)
            if sr and sr.status_code == 200:
                sbody = sr.json().get("message", {}).get("body", {})
                subtitle = sbody.get("subtitle", {})
                lrc_text = subtitle.get("subtitle_body")
                if lrc_text and len(lrc_text.strip()) > 10 and "[" in lrc_text:
                    if not is_romanized_korean_lyrics(lrc_text):
                        if not require_korean or has_hangul(lrc_text):
                            return (lrc_text.strip(), True)

        # 2. 일반 줄글 가사 폴백 (track.lyrics.get)
        if matched_track.get("has_lyrics", 0) and (track_id or commontrack_id):
            lyr_url = f"{ROOT_URL}track.lyrics.get"
            lyr_params: Dict[str, Any] = {
                "app_id": APP_ID,
                "usertoken": token,
                "t": str(int(time.time() * 1000))
            }
            if commontrack_id:
                lyr_params["commontrack_id"] = commontrack_id
            else:
                lyr_params["track_id"] = track_id

            lr = _request_musixmatch_with_retry(lyr_url, params=lyr_params, headers=headers, timeout=timeout, max_retries=2)
            if lr and lr.status_code == 200:
                lbody = lr.json().get("message", {}).get("body", {})
                lyrics = lbody.get("lyrics", {})
                plain_text = lyrics.get("lyrics_body")
                if plain_text and len(plain_text.strip()) > 10:
                    # Musixmatch 면책조항 문구 제거
                    cleaned_plain = re.sub(r'\*\*\*\*\*\*\* This Lyrics is NOT for Commercial use \*\*\*\*\*\*\*.*', '', plain_text, flags=re.DOTALL).strip()
                    if cleaned_plain and not is_romanized_korean_lyrics(cleaned_plain):
                        if not require_korean or has_hangul(cleaned_plain):
                            return (cleaned_plain, False)

    except Exception:
        pass

    return None
