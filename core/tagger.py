# -*- coding: utf-8 -*-
"""
Mutagen-based audio metadata and lyrics tagger supporting MP3 and M4A.
"""
import os
from typing import Optional
from mutagen.id3 import (
    ID3, TIT2, TPE1, TALB, TDRC, TRCK, APIC, USLT, ID3NoHeaderError
)
from mutagen.mp4 import MP4, MP4Cover
from .types import TrackMetadata


def tag_audio_file(
    audio_file_path: str,
    metadata: TrackMetadata,
    cover_image_bytes: Optional[bytes] = None,
    save_lrc_file: bool = False
) -> bool:
    """
    오디오 파일(MP3 또는 M4A)에 메타데이터, 가사, 앨범 아트를 임베딩합니다.
    """
    if not os.path.isfile(audio_file_path):
        return False

    ext = os.path.splitext(audio_file_path)[1].lower()

    # 옵션: .lrc 파일 별도 저장
    if save_lrc_file and metadata.lyrics:
        lrc_path = os.path.splitext(audio_file_path)[0] + ".lrc"
        try:
            with open(lrc_path, "w", encoding="utf-8") as lf:
                lf.write(metadata.lyrics)
        except Exception:
            pass

    if ext == ".mp3":
        return _tag_mp3(audio_file_path, metadata, cover_image_bytes)
    elif ext in (".m4a", ".mp4"):
        return _tag_m4a(audio_file_path, metadata, cover_image_bytes)

    return False


def _tag_mp3(
    file_path: str,
    metadata: TrackMetadata,
    cover_bytes: Optional[bytes]
) -> bool:
    try:
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()

        # 기본 태그
        if metadata.title:
            audio.add(TIT2(encoding=3, text=metadata.title))
        if metadata.artist:
            audio.add(TPE1(encoding=3, text=metadata.artist))
        if metadata.album:
            audio.add(TALB(encoding=3, text=metadata.album))
        if metadata.release_year:
            audio.add(TDRC(encoding=3, text=str(metadata.release_year)))

        if metadata.track_number is not None:
            if metadata.total_tracks:
                trck_str = f"{metadata.track_number}/{metadata.total_tracks}"
            else:
                trck_str = str(metadata.track_number)
            audio.add(TRCK(encoding=3, text=trck_str))

        # 가사 임베딩 (USLT)
        if metadata.lyrics:
            audio.delall("USLT")
            audio.add(USLT(encoding=3, lang="kor", desc="Lyrics", text=metadata.lyrics))

        # 앨범 커버 임베딩 (APIC)
        if cover_bytes:
            audio.delall("APIC")
            audio.add(APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,  # Cover (front)
                desc="Cover",
                data=cover_bytes
            ))

        audio.save(file_path, v2_version=3)
        return True
    except Exception:
        return False


def _tag_m4a(
    file_path: str,
    metadata: TrackMetadata,
    cover_bytes: Optional[bytes]
) -> bool:
    try:
        mp4 = MP4(file_path)
        if mp4.tags is None:
            mp4.add_tags()

        tags = mp4.tags

        if metadata.title:
            tags["\xa9nam"] = [metadata.title]
        if metadata.artist:
            tags["\xa9ART"] = [metadata.artist]
        if metadata.album:
            tags["\xa9alb"] = [metadata.album]
        if metadata.release_year:
            tags["\xa9day"] = [str(metadata.release_year)]

        if metadata.track_number is not None:
            total = metadata.total_tracks or 0
            tags["trkn"] = [(metadata.track_number, total)]

        # 가사 임베딩 (\xa9lyr)
        if metadata.lyrics:
            tags["\xa9lyr"] = [metadata.lyrics]

        # 앨범 커버 임베딩 (covr)
        if cover_bytes:
            tags["covr"] = [MP4Cover(cover_bytes, imageformat=MP4Cover.FORMAT_JPEG)]

        mp4.save()
        return True
    except Exception:
        return False
