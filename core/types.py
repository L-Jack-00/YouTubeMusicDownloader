# -*- coding: utf-8 -*-
"""
Type definitions and data structures for YouTube Music Downloader.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Callable


class DownloadState(Enum):
    """작업 진행 상태"""
    IDLE = "대기"
    SCANNING = "정보 분석 중"
    DOWNLOADING = "다운로드 중"
    CONVERTING = "음원 변환 중"
    FETCHING_LYRICS = "가사 수집 중"
    TAGGING = "태그 및 앨범아트 삽입 중"
    COMPLETED = "완료"
    CANCELLED = "작업 취소됨"
    ERROR = "오류 발생"


@dataclass
class TrackMetadata:
    """음원 메타데이터 모델"""
    title: str = ""
    artist: str = ""
    album: str = ""
    release_year: Optional[str] = None
    track_number: Optional[int] = None
    total_tracks: Optional[int] = None
    duration_seconds: Optional[int] = None
    thumbnail_url: Optional[str] = None
    source_url: str = ""
    lyrics: Optional[str] = None
    is_synced_lyrics: bool = False


@dataclass
class DownloadOptions:
    """다운로드 구성 옵션"""
    output_dir: str
    audio_format: str = "m4a"  # "m4a" (무손실 스트림 복사) 또는 "mp3" (320kbps 변환)
    mp3_bitrate: str = "320k"
    naming_format: str = "artist_title"  # "artist_title", "title_artist", "title_only", "num_artist_title", "num_title"
    embed_lyrics: bool = True
    save_lrc_file: bool = False
    crop_square_cover: bool = True
    # 쿠키 모드: "none", "browser", "file"
    cookie_mode: str = "none"
    browser_name: str = "chrome"
    cookie_file_path: Optional[str] = None


ProgressCallback = Callable[[DownloadState, float, str], None]
