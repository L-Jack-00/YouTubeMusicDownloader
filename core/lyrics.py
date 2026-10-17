# -*- coding: utf-8 -*-
"""
Unified lyrics resolver with 3-tier fallback strategy.
"""
from typing import Optional, Tuple
from .alsong import fetch_alsong_lyrics
from .lrclib import fetch_lrclib_lyrics


def resolve_lyrics(
    title: str,
    artist: str,
    album: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    embedded_subtitles: Optional[str] = None
) -> Tuple[Optional[str], bool, str]:
    """
    3단계 우선순위 가사 수집 파이프라인:
    1단계: 영상 자체 제공 자막 (유튜브)
    2단계: 알송 SOAP API (국내 가요 최적화)
    3단계: LRCLIB API (해외 음원 및 글로벌 최적화)

    반환값: (가사 내용, 싱크 가사 여부, 제공 출처)
    """
    # 1단계: 내장 자막 확인
    if embedded_subtitles and len(embedded_subtitles.strip()) > 20:
        is_synced = "[" in embedded_subtitles and "]" in embedded_subtitles
        return (embedded_subtitles.strip(), is_synced, "YouTube Subtitles")

    # 2단계: 알송 SOAP API
    try:
        alsong_res = fetch_alsong_lyrics(title, artist)
        if alsong_res and len(alsong_res.strip()) > 10:
            is_synced = "[" in alsong_res and "]" in alsong_res
            return (alsong_res.strip(), is_synced, "AlSong")
    except Exception:
        pass

    # 3단계: LRCLIB API
    try:
        lrclib_res = fetch_lrclib_lyrics(title, artist, album, duration_seconds)
        if lrclib_res and lrclib_res[0]:
            return (lrclib_res[0], lrclib_res[1], "LRCLIB")
    except Exception:
        pass

    return (None, False, "None")
