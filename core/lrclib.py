# -*- coding: utf-8 -*-
"""
LRCLIB API Lyrics Search Client with 503 Anti-Crash & Exponential Backoff Harness.
Retrieves time-synchronized (LRC) and plain lyrics with multi-candidate artist/title resolution.
"""
import time
import re
from typing import Optional, Tuple, List, Dict, Any
import requests
from .alsong import clean_search_term
from .lyrics_detector import is_romanized_korean_lyrics, has_hangul

LRCLIB_GET_URL = "https://lrclib.net/api/get"
LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"
LRCLIB_HEADERS = {
    "User-Agent": "ytmusic-dl/1.3.6 (https://github.com/L-Jack-00/ytmusic-dl)",
    "Accept": "application/json",
}


def _request_with_retry(
    url: str,
    params: Dict[str, Any],
    timeout: int = 5,
    max_retries: int = 3
) -> Optional[Any]:
    """
    HTTP 503 (Server Overloaded), 429 (Rate Limit) 및 일시적 네트워크 에러 발생 시
    지수 백오프(Exponential Backoff)를 적용하여 최대 max_retries회 안전하게 재시도합니다.
    """
    delay = 0.8
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=LRCLIB_HEADERS, timeout=timeout)
            if resp.status_code == 200:
                try:
                    return resp.json()
                except Exception:
                    return None
            elif resp.status_code in (429, 500, 502, 503, 504, 521):
                # 일시적 과부하 또는 레이트리밋: 대기 후 재시도
                time.sleep(delay)
                delay *= 1.8
                continue
            elif resp.status_code == 404:
                return None
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            time.sleep(delay)
            delay *= 1.8
            continue

    return None


def get_artist_search_candidates(artist: str) -> List[str]:
    """
    한글/영문 병기 또는 부가 정보가 포함된 아티스트명에서
    가사 DB 검색 성공률을 극대화하기 위한 정제 후보 목록을 추출합니다.
    예:
      '긱스 Geeks' -> ['긱스 Geeks', '긱스', 'Geeks']
      '에픽하이 (Epik High)' -> ['에픽하이 (Epik High)', '에픽하이', 'Epik High']
      '다이나믹 듀오 - Dynamicduo' -> ['다이나믹 듀오', 'Dynamicduo']
    """
    if not artist:
        return []

    candidates: List[str] = []
    raw = artist.strip()
    if raw:
        candidates.append(raw)

    # 1. 괄호 내용 분리: '에픽하이 (Epik High)' -> '에픽하이', 'Epik High'
    bracket_match = re.search(r'^(.*?)\s*[\(\[\{](.+?)[\)\]\}]\s*$', raw)
    if bracket_match:
        main_part = bracket_match.group(1).strip()
        inner_part = bracket_match.group(2).strip()
        if main_part:
            candidates.append(main_part)
        if inner_part:
            candidates.append(inner_part)

    # 2. 구분자(- / , &) 분리: 'Dynamicduo - 다이나믹 듀오'
    for sep in [' - ', ' / ', ', ', ' & ']:
        if sep in raw:
            for part in raw.split(sep):
                p = part.strip()
                if p and p not in candidates:
                    candidates.append(p)

    # 3. 한글+영문 공백 병기 분리: '긱스 Geeks' -> '긱스', 'Geeks'
    hangul_eng_match = re.match(r'^([가-힣\s]+)\s+([a-zA-Z0-9\s]+)$', raw)
    if hangul_eng_match:
        h_part = hangul_eng_match.group(1).strip()
        e_part = hangul_eng_match.group(2).strip()
        if h_part and h_part not in candidates:
            candidates.append(h_part)
        if e_part and e_part not in candidates:
            candidates.append(e_part)

    # 4. feat. / ft. 제거: '리쌍 (feat. Harim)' -> '리쌍'
    no_feat = re.sub(r'\s*[\(\[\{]?(?:feat\.?|ft\.?).*?[\)\]\}]?', '', raw, flags=re.IGNORECASE).strip()
    if no_feat and no_feat not in candidates:
        candidates.append(no_feat)

    # 중복 제거 및 빈 문자열 제외
    seen = set()
    unique_candidates = []
    for c in candidates:
        c_clean = c.strip()
        if c_clean and c_clean not in seen:
            seen.add(c_clean)
            unique_candidates.append(c_clean)

    return unique_candidates


def _score_lrclib_item(item: Dict[str, Any], require_korean: bool = False) -> int:
    """
    가사 적합도 점수 계산:
    - 로마자 가사 감지 시 즉시 탈락 (-1000)
    - 한국어 필수 모드에서 한글 부재 시 탈락 (-500)
    - 싱크 가사 우선 (+1000)
    - 한국어 가사 우선 (+500, 영문 로마자 발음 전사 대비 원문 한글 가사 선호)
    """
    synced = item.get("syncedLyrics") or ""
    plain = item.get("plainLyrics") or ""
    candidate_text = synced or plain
    if not candidate_text:
        return -1000

    # 1. 로마자 발음 가사 (Romanized) 엄격 기각
    if is_romanized_korean_lyrics(candidate_text):
        return -1000

    # 2. 한국어 가사 필수 요구 시 한글 미포함 가사 기각
    if require_korean and not has_hangul(candidate_text):
        return -500

    score = 0
    if synced:
        score += 1000
        if has_hangul(synced):
            score += 500
    elif plain:
        score += 100
        if has_hangul(plain):
            score += 50
    return score


def fetch_lrclib_lyrics(
    title: str,
    artist: str,
    album: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    timeout: int = 5,
    require_korean: bool = False
) -> Optional[Tuple[str, bool]]:
    """
    LRCLIB 공개 API를 통해 503 방어 하네스 및 다중 후보 탐색으로 싱크/일반 가사를 수집합니다.
    - require_korean=True: 한글 원문 가사만 허용하며 로마자 가사는 배제합니다.
    반환값: (가사 텍스트, 싱크 가사 여부[True=LRC, False=일반]) 또는 None
    """
    c_title = clean_search_term(title)
    artist_candidates = get_artist_search_candidates(artist)
    if not artist_candidates and artist:
        artist_candidates = [artist.strip()]

    # 1단계: 정밀 조회 시도 (/api/get)
    for a in artist_candidates:
        params: Dict[str, Any] = {
            "track_name": c_title or title,
            "artist_name": a,
        }
        if duration_seconds:
            params["duration"] = int(duration_seconds)

        data = _request_with_retry(LRCLIB_GET_URL, params=params, timeout=timeout, max_retries=2)
        if isinstance(data, dict):
            synced = data.get("syncedLyrics")
            plain = data.get("plainLyrics")
            if synced and len(synced.strip()) > 10:
                if not is_romanized_korean_lyrics(synced):
                    if not require_korean or has_hangul(synced):
                        return (synced.strip(), True)
            if plain and len(plain.strip()) > 10:
                if not is_romanized_korean_lyrics(plain):
                    if not require_korean or has_hangul(plain):
                        return (plain.strip(), False)

    # 2단계: 유연 검색 시도 (/api/search with track_name & artist_name)
    best_item = None
    best_score = -1

    for a in artist_candidates:
        search_params = {
            "track_name": c_title or title,
            "artist_name": a
        }
        results = _request_with_retry(LRCLIB_SEARCH_URL, params=search_params, timeout=timeout, max_retries=2)
        if isinstance(results, list) and results:
            for item in results:
                s = _score_lrclib_item(item, require_korean=require_korean)
                if s > best_score:
                    best_score = s
                    best_item = item
            if best_item and best_score >= 1500:
                # 싱크 가사이면서 한글 가사 매칭 완료
                break

    # 3단계: 전문 텍스트 쿼리 검색 (/api/search with q)
    if not best_item or best_score <= 0:
        for a in artist_candidates:
            query = f"{c_title} {a}".strip()
            results = _request_with_retry(LRCLIB_SEARCH_URL, params={"q": query}, timeout=timeout, max_retries=2)
            if isinstance(results, list) and results:
                for item in results:
                    s = _score_lrclib_item(item, require_korean=require_korean)
                    if s > best_score:
                        best_score = s
                        best_item = item
                if best_item and best_score >= 1000:
                    break

    if best_item and best_score > 0:
        synced = best_item.get("syncedLyrics")
        plain = best_item.get("plainLyrics")
        if synced and len(synced.strip()) > 10:
            return (synced.strip(), True)
        if plain and len(plain.strip()) > 10:
            return (plain.strip(), False)

    return None
