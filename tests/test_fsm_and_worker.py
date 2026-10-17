# -*- coding: utf-8 -*-
"""
Headless unit tests for DownloadState transitions, cancellation and options.
"""
import unittest
from core.types import DownloadState, DownloadOptions, TrackMetadata
from core.downloader import YoutubeMusicDownloader


class TestStateAndDownloader(unittest.TestCase):

    def test_download_states_enum_values(self):
        self.assertEqual(DownloadState.IDLE.value, "대기")
        self.assertEqual(DownloadState.SCANNING.value, "정보 분석 중")
        self.assertEqual(DownloadState.DOWNLOADING.value, "다운로드 중")
        self.assertEqual(DownloadState.CONVERTING.value, "음원 변환 중")
        self.assertEqual(DownloadState.FETCHING_LYRICS.value, "가사 수집 중")
        self.assertEqual(DownloadState.TAGGING.value, "태그 및 앨범아트 삽입 중")
        self.assertEqual(DownloadState.COMPLETED.value, "완료")
        self.assertEqual(DownloadState.CANCELLED.value, "작업 취소됨")
        self.assertEqual(DownloadState.ERROR.value, "오류 발생")

    def test_downloader_cancellation_flag(self):
        opts = DownloadOptions(output_dir="./test_out")
        downloader = YoutubeMusicDownloader(opts)
        self.assertFalse(downloader.is_cancelled())

        downloader.cancel()
        self.assertTrue(downloader.is_cancelled())

    def test_track_metadata_defaults(self):
        meta = TrackMetadata(title="Test Song", artist="Test Singer")
        self.assertEqual(meta.title, "Test Song")
        self.assertEqual(meta.artist, "Test Singer")
        self.assertEqual(meta.album, "")
        self.assertIsNone(meta.lyrics)
        self.assertFalse(meta.is_synced_lyrics)

    def test_filename_formatting_presets(self):
        from core.downloader import format_track_filename, sanitize_filename
        meta = TrackMetadata(
            title="밤편지",
            artist="아이유",
            album="Palette",
            track_number=8,
            total_tracks=10
        )

        # 1. 아티스트 - 곡명 (기본값)
        self.assertEqual(format_track_filename("artist_title", meta, 1, "m4a"), "아이유 - 밤편지.m4a")

        # 2. 곡명 - 아티스트
        self.assertEqual(format_track_filename("title_artist", meta, 1, "mp3"), "밤편지 - 아이유.mp3")

        # 3. 곡명 단독
        self.assertEqual(format_track_filename("title_only", meta, 1, "m4a"), "밤편지.m4a")

        # 4. 순번. 아티스트 - 곡명 (원본 앨범 트랙 번호 8번 반영)
        self.assertEqual(format_track_filename("num_artist_title", meta, 1, "mp3"), "08. 아이유 - 밤편지.mp3")

        # 5. 순번. 곡명 (원본 앨범 트랙 번호 8번 반영)
        self.assertEqual(format_track_filename("num_title", meta, 1, "m4a"), "08. 밤편지.m4a")

    def test_sanitize_filename_removes_illegal_characters(self):
        from core.downloader import sanitize_filename
        raw_name = 'AC/DC: "Back in Black"? *Special* <Track> | Part.1'
        cleaned = sanitize_filename(raw_name)
        self.assertEqual(cleaned, "ACDC Back in Black Special Track  Part.1")
        for bad_char in r'\/*?:"<>|':
            self.assertNotIn(bad_char, cleaned)

    def test_resolve_album_metadata_retrieves_album_and_track_number(self):
        from core.metadata_resolver import resolve_album_metadata
        res = resolve_album_metadata(title="Through the Night (밤편지)", artist="IU", album="Palette")
        self.assertIsInstance(res, dict)
        if res:
            self.assertEqual(res.get("track_number"), 8)
            self.assertEqual(res.get("total_tracks"), 10)
            self.assertEqual(res.get("album"), "Palette")


if __name__ == '__main__':
    unittest.main()
