# -*- coding: utf-8 -*-
"""
AlSong (알송) SOAP API High-Precision Lyrics Client.
Supports RSA-1024 client signature authentication (GetResembleLyric2),
millisecond-accurate timestamp normalization, and multi-candidate scoring.
"""
import re
import html
import time
import xml.etree.ElementTree as ET
from typing import Optional, Tuple, List
import requests
from .lyrics_detector import is_romanized_korean_lyrics, has_hangul


ALSONG_ENDPOINT = "http://lyrics.alsong.co.kr/alsongwebservice/service1.asmx"

# 알송 클라이언트 RSA-1024 인증 암호문 토큰
ALSONG_ENC_DATA = (
    "8456ec35caba5c981e705b0c5d76e4593e020ae5e3d469c75d1c6714b6b1244c"
    "0732f1f19cc32ee5123ef7de574fc8bc6d3b6bd38dd3c097f5a4a1aa1b438fea"
    "0e413baf8136d2d7d02bfcdcb2da4990df2f28675a3bd621f8234afa84fb4ee9"
    "caa8f853a5b06f884ea086fd3ed3b4c6e14f1efac5a4edbf6f6cb475445390b0"
)


def clean_search_term(term: str) -> str:
    """
    검색 정확도를 높이기 위해 제목이나 아티스트명에서
    불필요한 특수문자, 괄호 태그([MV], (Official Audio), feat. 등)를 정제합니다.
    """
    if not term:
        return ""
    # 대괄호, 중괄호 내용 제거 ([MV], [Official], etc.)
    cleaned = re.sub(r'\[.*?\]', '', term)
    # 소괄호 내용 중 일반적인 영상 태그 제거
    cleaned = re.sub(r'\((?:Official|Audio|Video|MV|Live|Remastered|feat\.?|ft\.?|with).*?\)', '', cleaned, flags=re.IGNORECASE)
    # 앞뒤 공백 및 연속 공백 정리
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned or term.strip()


def normalize_alsong_lrc(raw_text: str) -> Tuple[Optional[str], bool]:
    """
    알송 가사 텍스트의 <br> 태그를 개행으로 치환하고,
    [mm:ss:xx] 또는 [mm:ss.xx] 타임스탬프를 표준 [mm:ss.xx] 형식으로 정규화합니다.
    반환값: (정규화된 가사, 싱크 가사 여부)
    """
    if not raw_text or len(raw_text.strip()) < 5:
        return None, False

    text = raw_text.replace('<br>', '\n').replace('<BR>', '\n')
    text = html.unescape(text).strip()

    # 타임태그 정규식: [00:00:00] 또는 [00:00.00]
    time_tag_pattern = re.compile(r'\[(\d{1,2}):(\d{2})[:.](\d{2,3})\]')
    has_sync = bool(time_tag_pattern.search(text))

    if has_sync:
        def replace_tag(m):
            minutes = int(m.group(1))
            seconds = int(m.group(2))
            ms = m.group(3)[:2].ljust(2, '0')
            return f"[{minutes:02d}:{seconds:02d}.{ms}]"

        normalized_lrc = time_tag_pattern.sub(replace_tag, text)
        return normalized_lrc, True

    return text, False


def _post_alsong_with_retry(
    soap_body: str,
    headers: dict,
    timeout: int = 5,
    max_retries: int = 2
) -> Optional[requests.Response]:
    """
    네트워크 일시 지연, 타임아웃 및 서버 오류 발생 시 대기 후 지수 백오프(Exponential Backoff) 재시도를 수행합니다.
    """
    delay = 0.6
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                ALSONG_ENDPOINT,
                data=soap_body.encode("utf-8"),
                headers=headers,
                timeout=timeout
            )
            if resp.status_code == 200 and resp.text:
                return resp
            elif resp.status_code in (429, 500, 502, 503, 504):
                time.sleep(delay)
                delay *= 1.5
                continue
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            time.sleep(delay)
            delay *= 1.5
            continue
    return None


def fetch_alsong_lyrics(
    title: str,
    artist: str = "",
    timeout: int = 5
) -> Optional[Tuple[str, bool]]:
    """
    알송 서버에 곡명 및 아티스트명으로 싱크 가사를 요청합니다.
    SOAP 1.2 GetResembleLyric2 프로토콜을 사용하며 점수 기반 최적 가사를 선정합니다.
    성공 시 (가사 문자열, 싱크 가사 여부) 튜플을 반환합니다.
    """
    c_title = clean_search_term(title)
    c_artist = clean_search_term(artist)

    # 검색어 후보 쌍 생성 (정제 검색어 우선, 원본 보조)
    search_pairs: List[Tuple[str, str]] = [(c_title, c_artist)]
    if (c_title, c_artist) != (title.strip(), artist.strip()):
        search_pairs.append((title.strip(), artist.strip()))
    if c_artist:
        search_pairs.append((c_title, ""))  # 가수 없이 제목 단독 폴백

    headers = {
        "Accept-Charset": "utf-8",
        "Content-Type": "application/soap+xml; charset=utf-8",
        "User-Agent": "gSOAP/2.7",
        "SOAPAction": "ALSongWebServer/GetResembleLyric2"
    }

    for s_title, s_artist in search_pairs:
        if not s_title:
            continue

        soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://www.w3.org/2003/05/soap-envelope"
    xmlns:SOAP-ENC="http://www.w3.org/2003/05/soap-encoding"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:ns1="ALSongWebServer">
    <SOAP-ENV:Body>
        <ns1:GetResembleLyric2>
            <ns1:encData>{ALSONG_ENC_DATA}</ns1:encData>
            <ns1:stQuery>
                <ns1:strTitle>{html.escape(s_title)}</ns1:strTitle>
                <ns1:strArtistName>{html.escape(s_artist)}</ns1:strArtistName>
                <ns1:nCurPage>0</ns1:nCurPage>
            </ns1:stQuery>
        </ns1:GetResembleLyric2>
    </SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""

        try:
            resp = _post_alsong_with_retry(
                soap_body=soap_body,
                headers=headers,
                timeout=timeout,
                max_retries=2
            )
            if not resp or not resp.text:
                continue

            root = ET.fromstring(resp.text)
            candidates = []
            for elem in root.iter():
                tag = elem.tag.split("}")[-1]
                if tag == "ST_GET_RESEMBLELYRIC2_RETURN":
                    cand_t, cand_a, cand_l, is_word = "", "", "", "0"
                    for child in elem:
                        c_tag = child.tag.split("}")[-1]
                        if c_tag == "strTitle":
                            cand_t = child.text or ""
                        elif c_tag == "strArtistName":
                            cand_a = child.text or ""
                        elif c_tag == "strLyric":
                            cand_l = child.text or ""
                        elif c_tag == "strOnlyLyricWord":
                            is_word = child.text or "0"
                    if cand_l and len(cand_l.strip()) > 10:
                        candidates.append((cand_t, cand_a, cand_l, is_word))

            if not candidates:
                continue

            # 후보군 매칭 점수 채점 및 1순위 선정
            best_candidate = None
            best_score = -100

            norm_q_title = re.sub(r'[\s\W_]+', '', c_title.lower())
            norm_q_artist = re.sub(r'[\s\W_]+', '', c_artist.lower())

            for cand_t, cand_a, cand_l, is_word in candidates:
                score = 0
                norm_cand_t = re.sub(r'[\s\W_]+', '', cand_t.lower())
                norm_cand_a = re.sub(r'[\s\W_]+', '', cand_a.lower())

                # 1. 제목 일치도 점수
                if norm_cand_t == norm_q_title:
                    score += 50
                elif norm_q_title in norm_cand_t or norm_cand_t in norm_q_title:
                    score += 30

                # 2. 아티스트 일치도 점수
                if norm_q_artist:
                    if norm_cand_a == norm_q_artist:
                        score += 30
                    elif norm_q_artist in norm_cand_a or norm_cand_a in norm_q_artist:
                        score += 20

                # 3. 싱크 가사 보너스 가중치 (타임스탬프 유무)
                if "[" in cand_l and "]" in cand_l and re.search(r'\[\d{1,2}:\d{2}', cand_l):
                    score += 40
                if is_word == "0":
                    score += 10

                # 4. 언어 및 로마자 검증 점수
                if is_romanized_korean_lyrics(cand_l):
                    score -= 500
                elif has_hangul(cand_l):
                    score += 30

                if score > best_score:
                    best_score = score
                    best_candidate = (cand_t, cand_a, cand_l)

            if best_candidate:
                lrc_text, is_synced = normalize_alsong_lrc(best_candidate[2])
                if lrc_text:
                    return (lrc_text, is_synced)

        except Exception:
            continue

    return None
