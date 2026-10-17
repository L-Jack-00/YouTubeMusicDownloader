# -*- coding: utf-8 -*-
"""
LRCLIB API Lyrics Search Client
"""
from typing import Optional, Tuple
import requests
from .alsong import clean_search_term

LRCLIB_GET_URL = "https://lrclib.net/api/get"
LRCLIB_SEARCH_URL = "https://lrclib.net/api/search"


def fetch_lrclib_lyrics(
    title: str,
    artist: str,
    album: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    timeout: int = 5
) -> Optional[Tuple[str, bool]]:
    """
    LRCLIB 공개 API를 통해 가사를 검색합니다.
    반환값: (가사 텍스트, 싱크 가사 여부) 또는 None
    """
    c_title = clean_search_term(title)
    c_artist = clean_search_term(artist)

    headers = {
        "User-Agent": "YTMusicDownloader/1.0.0 (https://github.com/ytmusic-downloader)",
    }

    # 1. 정밀 조회 시도 (/api/get)
    params = {
        "track_name": c_title or title,
        "artist_name": c_artist or artist,
    }
    if album:
        params["album_name"] = album
    if duration_seconds:
        params["duration"] = int(duration_seconds)

    try:
        resp = requests.get(LRCLIB_GET_URL, params=params, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            synced = data.get("syncedLyrics")
            plain = data.get("plainLyrics")
            if synced:
                return (synced.strip(), True)
            if plain:
                return (plain.strip(), False)
    except Exception:
        pass

    # 2. 유연 검색 시도 (/api/search)
    try:
        search_query = f"{c_artist} {c_title}".strip()
        resp = requests.get(LRCLIB_SEARCH_URL, params={"q": search_query}, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            results = resp.json()
            if isinstance(results, list) and len(results) > 0:
                first = results[0]
                synced = first.get("syncedLyrics")
                plain = first.get("plainLyrics")
                if synced:
                    return (synced.strip(), True)
                if plain:
                    return (plain.strip(), False)
    except Exception:
        pass

    return None
