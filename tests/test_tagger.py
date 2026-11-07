# -*- coding: utf-8 -*-
"""
Headless unit tests for MP3/M4A tagging and LRC generation.
"""
import os
import json
import tempfile
import unittest
from mutagen.id3 import ID3
from core.types import TrackMetadata
from core.tagger import tag_audio_file


class TestTagger(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_resolve_album_metadata_includes_genre(self):
        from unittest.mock import patch, MagicMock
        from core.metadata_resolver import resolve_album_metadata

        mock_payload = {
            "results": [{
                "trackName": "Supernova",
                "artistName": "aespa",
                "collectionName": "Armageddon - The 1st Album",
                "trackNumber": 1,
                "trackCount": 10,
                "releaseDate": "2024-05-27T07:00:00Z",
                "primaryGenreName": "K-Pop"
            }]
        }
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = json.dumps(mock_payload).encode('utf-8')
            mock_urlopen.return_value.__enter__.return_value = mock_resp

            resolved = resolve_album_metadata(title="Supernova", artist="aespa")
            self.assertEqual(resolved.get("genre"), "K-Pop")
            self.assertEqual(resolved.get("track_number"), 1)
            self.assertEqual(resolved.get("release_year"), "2024")

    def test_mp3_tagging_with_metadata_and_lyrics(self):
        # 유효한 최소 MP3 프레임 헤더 생성 (MPEG-1 Layer 3, 128kbps, 44.1kHz)
        mp3_path = os.path.join(self.temp_dir, "test_song.mp3")
        # Frame sync: 0xFF, 0xFB (MPEG 1 Layer 3, no CRC), 0x90 (128kbps, 44.1kHz), 0x00
        frame_header = b"\xff\xfb\x90\x00"
        frame_body = b"\x00" * 414
        with open(mp3_path, "wb") as f:
            for _ in range(10):
                f.write(frame_header + frame_body)

        meta = TrackMetadata(
            title="좋은 날",
            artist="아이유",
            album="Real",
            release_year="2010",
            track_number=3,
            total_tracks=6,
            genre="K-Pop",
            lyrics="[00:10.00]어쩌면 이렇게 하늘은 더 파란 건지\n[00:15.00]오늘따라 왜 바람은 또 완벽한지"
        )
        fake_cover = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00\xff\xd9"

        # 태깅 실행
        success = tag_audio_file(
            audio_file_path=mp3_path,
            metadata=meta,
            cover_image_bytes=fake_cover,
            save_lrc_file=True
        )
        self.assertTrue(success)

        # ID3 태그 검증
        id3 = ID3(mp3_path)
        self.assertEqual(id3.get("TIT2").text[0], "좋은 날")
        self.assertEqual(id3.get("TPE1").text[0], "아이유")
        self.assertEqual(id3.get("TALB").text[0], "Real")
        self.assertEqual(id3.get("TRCK").text[0], "3/6")
        self.assertIsNotNone(id3.get("TCON"))
        self.assertEqual(id3.get("TCON").text[0], "K-Pop")
        self.assertIn("좋은 날", id3.get("TIT2").text[0])
        self.assertTrue(len(id3.getall("USLT")) > 0)
        self.assertIn("어쩌면 이렇게", id3.getall("USLT")[0].text)
        self.assertTrue(len(id3.getall("APIC")) > 0)

        # .lrc 파일 생성 검증
        lrc_file = os.path.join(self.temp_dir, "test_song.lrc")
        self.assertTrue(os.path.isfile(lrc_file))
        with open(lrc_file, "r", encoding="utf-8") as lf:
            lrc_content = lf.read()
            self.assertIn("어쩌면 이렇게", lrc_content)


if __name__ == '__main__':
    unittest.main()
