# -*- coding: utf-8 -*-
"""
Unified lyrics resolver with 3-tier fallback strategy and multi-artist variant matching.
"""
import re
from typing import List, Optional, Tuple
from .alsong import fetch_alsong_lyrics
from .lrclib import fetch_lrclib_lyrics


def get_artist_search_candidates(artist: str) -> List[str]:
    """
    한영 병기, 괄호, 특수 구분자로 묶인 아티스트 문자열에서
    가사 검색 성공률을 극대화하기 위해 순차적으로 시도할 검색어 후보 리스트를 생성합니다.
    예:
    - '긱스 Geeks' -> ['긱스 Geeks', '긱스', 'Geeks']
    - '에픽하이 (EPIK HIGH)' -> ['에픽하이 (EPIK HIGH)', '에픽하이', 'EPIK HIGH']
    - 'Dynamicduo - 다이나믹 듀오' -> ['Dynamicduo - 다이나믹 듀오', 'Dynamicduo', '다이나믹 듀오']
    """
    if not artist:
        return []

    raw = artist.strip()
    candidates: List[str] = [raw]

    # 1. 괄호 내용 및 괄호 제외 분리: '에픽하이 (EPIK HIGH)' -> '에픽하이', 'EPIK HIGH'
    p_matches = re.findall(r'\(([^)]+)\)', raw)
    for p in p_matches:
        p_clean = p.strip()
        if p_clean and p_clean not in candidates:
            candidates.append(p_clean)

    without_p = re.sub(r'\(.*?\)', '', raw).strip()
    if without_p and without_p not in candidates:
        candidates.append(without_p)

    # 2. 구분자 분리 (-, /, &, ,)
    for delim in [' - ', ' / ', ' & ', ', ']:
        if delim in raw:
            for part in raw.split(delim):
                part_clean = part.strip()
                if part_clean and part_clean not in candidates:
                    candidates.append(part_clean)

    # 3. 한글/영문 병기 분리 (예: '긱스 Geeks' -> '긱스', 'Geeks')
    ko_parts = re.findall(r'[\uac00-\ud7a30-9]+', raw)
    if ko_parts:
        ko_str = ' '.join(ko_parts).strip()
        if ko_str and ko_str not in candidates:
            candidates.append(ko_str)

    en_parts = re.findall(r'[a-zA-Z0-9]+', raw)
    if en_parts:
        en_str = ' '.join(en_parts).strip()
        if en_str and en_str not in candidates:
            candidates.append(en_str)

    return candidates


def resolve_lyrics(
    title: str,
    artist: str,
    album: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    embedded_subtitles: Optional[str] = None
) -> Tuple[Optional[str], bool, str]:
    """
    3단계 우선순위 가사 수집 파이프라인 (아티스트 다각화 매칭 탑재):
    1단계: 영상 자체 제공 자막 (유튜브)
    2단계: 알송 SOAP API (국내 가요 최적화)
    3단계: LRCLIB API (해외 음원 및 글로벌 최적화)

    반환값: (가사 내용, 싱크 가사 여부, 제공 출처)
    """
    # 1단계: 내장 자막 확인
    if embedded_subtitles and len(embedded_subtitles.strip()) > 20:
        is_synced = "[" in embedded_subtitles and "]" in embedded_subtitles
        return (embedded_subtitles.strip(), is_synced, "YouTube Subtitles")

    artist_candidates = get_artist_search_candidates(artist)

    # 2단계: 알송 SOAP API (국내 가요 우선 탐색)
    for art in artist_candidates:
        try:
            alsong_res = fetch_alsong_lyrics(title, art)
            if alsong_res and len(alsong_res.strip()) > 10:
                is_synced = "[" in alsong_res and "]" in alsong_res
                return (alsong_res.strip(), is_synced, "AlSong")
        except Exception:
            pass

    # 3단계: LRCLIB API (글로벌/해외 음원 및 정밀 싱크)
    for art in artist_candidates:
        try:
            lrclib_res = fetch_lrclib_lyrics(title, art, album, duration_seconds)
            if lrclib_res and lrclib_res[0]:
                return (lrclib_res[0], lrclib_res[1], "LRCLIB")
        except Exception:
            pass

    return (None, False, "None")

