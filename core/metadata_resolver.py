# -*- coding: utf-8 -*-
"""
Album and Track Metadata Resolver
Fetches original album metadata (album title, track number, total tracks, release year)
via the public iTunes Search API.
"""
import urllib.request
import urllib.parse
import json
from typing import Optional, Dict, Any
from .alsong import clean_search_term


def resolve_album_metadata(
    title: str,
    artist: str,
    album: Optional[str] = None,
    timeout: float = 3.5
) -> Dict[str, Any]:
    """
    iTunes 검색 API를 통해 원본 앨범의 트랙 번호, 전체 트랙 수, 앨범명, 발매년도를 조회합니다.
    조회 실패 시 빈 딕셔너리를 반환합니다.
    """
    c_title = clean_search_term(title)
    c_artist = clean_search_term(artist)
    c_album = clean_search_term(album) if album else ""

    if not c_title:
        return {}

    # 검색 쿼리 후보 목록 구성 (1. 아티스트+앨범+곡명 -> 2. 아티스트+곡명 -> 3. 곡명 단독)
    queries = []
    if c_artist and c_album and c_album != c_title:
        queries.append(f"{c_artist} {c_album} {c_title}")
    if c_artist and c_artist != "Unknown Artist":
        queries.append(f"{c_artist} {c_title}")
    queries.append(c_title)

    for query in queries:
        try:
            encoded_query = urllib.parse.quote(query.strip())
            url = f"https://itunes.apple.com/search?term={encoded_query}&entity=song&limit=5"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    continue
                data = json.loads(response.read().decode("utf-8", errors="ignore"))
                results = data.get("results", [])
                if not results:
                    continue

                # 가장 일치하는 결과 탐색
                matched = None
                for res in results:
                    r_track = res.get("trackName", "").lower()
                    r_artist = res.get("artistName", "").lower()
                    # 제목이 포함되어 있는지 확인
                    if c_title.lower() in r_track or r_track in c_title.lower():
                        if not c_artist or c_artist.lower() in r_artist or r_artist in c_artist.lower():
                            matched = res
                            break
                if not matched and results:
                    matched = results[0]

                if matched:
                    track_number = matched.get("trackNumber")
                    track_count = matched.get("trackCount")
                    collection_name = matched.get("collectionName")
                    artist_name = matched.get("artistName")
                    release_date = matched.get("releaseDate")
                    release_year = release_date[:4] if release_date and len(release_date) >= 4 else None

                    return {
                        "track_number": track_number,
                        "total_tracks": track_count,
                        "album": collection_name,
                        "artist": artist_name,
                        "release_year": release_year
                    }
        except Exception:
            continue

    return {}
