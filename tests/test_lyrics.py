# -*- coding: utf-8 -*-
"""
Headless unit tests for Multi-Tier lyrics engine (AlSong -> LRCLIB -> Musixmatch -> Subtitles -> Description).
"""
import unittest
from unittest.mock import patch

from core.alsong import clean_search_term, normalize_alsong_lrc, fetch_alsong_lyrics, _post_alsong_with_retry
from core.lrclib import get_artist_search_candidates, _request_with_retry
from core.musixmatch import fetch_musixmatch_lyrics, _request_musixmatch_with_retry
from core.lyrics import (
    parse_subtitles_to_lrc,
    extract_lyrics_from_description,
    resolve_lyrics
)


class TestLyricsModule(unittest.TestCase):

    def test_clean_search_term_strips_brackets_and_tags(self):
        cases = [
            ("[MV] 아이유 - 밤편지 (Official Video)", "아이유 - 밤편지"),
            ("NewJeans - Hype Boy [Special Clip]", "NewJeans - Hype Boy"),
            ("Taylor Swift - Anti-Hero (Official Audio)", "Taylor Swift - Anti-Hero"),
            ("Song Title feat. Someone (Live)", "Song Title feat. Someone"),
            ("   Simple Title   ", "Simple Title"),
        ]
        for raw, expected in cases:
            cleaned = clean_search_term(raw)
            self.assertEqual(cleaned, expected, f"Failed cleaning: {raw} -> got '{cleaned}'")

    def test_get_artist_search_candidates(self):
        c1 = get_artist_search_candidates("긱스 Geeks")
        self.assertIn("긱스", c1)
        self.assertIn("Geeks", c1)

        c2 = get_artist_search_candidates("에픽하이 (Epik High)")
        self.assertIn("에픽하이", c2)
        self.assertIn("Epik High", c2)

        c3 = get_artist_search_candidates("Dynamicduo - 다이나믹 듀오")
        self.assertIn("Dynamicduo", c3)
        self.assertIn("다이나믹 듀오", c3)

        c4 = get_artist_search_candidates("리쌍 (feat. Harim)")
        self.assertIn("리쌍", c4)

    def test_normalize_alsong_lrc(self):
        raw = "[00:01:23]첫 번째 줄<br>[00:04.56]두 번째 줄<BR>[00:08:90]세 번째 줄"
        norm, is_synced = normalize_alsong_lrc(raw)
        self.assertTrue(is_synced)
        self.assertIn("[00:01.23]첫 번째 줄", norm)
        self.assertIn("[00:04.56]", norm)
        self.assertIn("[00:08.90]", norm)
        self.assertNotIn("<br>", norm)
        self.assertNotIn("<BR>", norm)

    def test_parse_subtitles_vtt_with_timestamps_to_synced_lrc(self):
        sample_vtt = """WEBVTT
Kind: captions
Language: ko

00:00:15.200 --> 00:00:19.500
<c>이 밤 그날의 반딧불을</c>

00:00:20.100 --> 00:00:24.000
당신의 창 가까이 보낼게요

00:01:05.450 --> 00:01:10.000
<b>사랑한다는 말이에요</b>
"""
        lyrics, is_synced, source = parse_subtitles_to_lrc(sample_vtt)
        self.assertIsNotNone(lyrics)
        self.assertTrue(is_synced)
        self.assertEqual(source, "YouTube Subtitles (Synced)")
        self.assertIn("[00:15.20] 이 밤 그날의 반딧불을", lyrics)
        self.assertIn("[00:20.10] 당신의 창 가까이 보낼게요", lyrics)
        self.assertIn("[01:05.45] 사랑한다는 말이에요", lyrics)
        self.assertNotIn("<c>", lyrics)
        self.assertNotIn("<b>", lyrics)

    def test_parse_subtitles_srt_format(self):
        sample_srt = """1
00:00:05,300 --> 00:00:08,200
첫 번째 소절입니다

2
00:00:09,000 --> 00:00:12,500
두 번째 소절입니다
"""
        lyrics, is_synced, source = parse_subtitles_to_lrc(sample_srt)
        self.assertIsNotNone(lyrics)
        self.assertTrue(is_synced)
        self.assertEqual(source, "YouTube Subtitles (Synced)")
        self.assertIn("[00:05.30] 첫 번째 소절입니다", lyrics)
        self.assertIn("[00:09.00] 두 번째 소절입니다", lyrics)

    def test_extract_lyrics_from_description(self):
        sample_desc = """
가수: 아이유 (IU)
앨범: 밤편지

[가사]
이 밤 그날의 반딧불을
당신의 창 가까이 보낼게요
음 좋은 꿈 이길 바라요

Credit:
작사: 아이유
작곡: 김제휘, 김희원
"""
        extracted = extract_lyrics_from_description(sample_desc)
        self.assertIsNotNone(extracted)
        self.assertIn("이 밤 그날의 반딧불을", extracted)
        self.assertIn("좋은 꿈 이길 바라요", extracted)
        self.assertNotIn("Credit:", extracted)
        self.assertNotIn("[가사]", extracted)

    def test_resolve_lyrics_tier1_alsong_priority(self):
        # 1순위: 알송에서 싱크 가사를 먼저 발견하면 AlSong (Synced) 반환
        with patch("core.lyrics.fetch_alsong_lyrics") as mock_alsong:
            mock_alsong.return_value = ("[00:01.00] 알송 싱크 가사", True)
            lyrics, is_synced, source = resolve_lyrics(
                title="기억을 걷는 시간",
                artist="넬",
                embedded_subtitles="dummy"
            )
            self.assertEqual(source, "AlSong (Synced)")
            self.assertTrue(is_synced)
            self.assertIn("알송 싱크 가사", lyrics)

    def test_resolve_lyrics_tier2_lrclib_when_alsong_misses(self):
        # 알송 실패 시 2순위 LRCLIB으로 정상 폴백
        with patch("core.lyrics.fetch_alsong_lyrics", return_value=None):
            with patch("core.lyrics.fetch_lrclib_lyrics") as mock_lrclib:
                mock_lrclib.return_value = ("[00:02.00] LRCLIB 싱크 가사", True)
                lyrics, is_synced, source = resolve_lyrics(
                    title="Shape of You",
                    artist="Ed Sheeran"
                )
                self.assertEqual(source, "LRCLIB (Synced)")
                self.assertTrue(is_synced)
                self.assertIn("LRCLIB 싱크 가사", lyrics)

    def test_resolve_lyrics_tier3_musixmatch_when_lrclib_misses(self):
        # 알송, LRCLIB 실패 시 3순위 Musixmatch로 정상 폴백
        with patch("core.lyrics.fetch_alsong_lyrics", return_value=None):
            with patch("core.lyrics.fetch_lrclib_lyrics", return_value=None):
                with patch("core.lyrics.fetch_musixmatch_lyrics") as mock_mxm:
                    mock_mxm.return_value = ("[00:03.00] Musixmatch 싱크 가사", True)
                    lyrics, is_synced, source = resolve_lyrics(
                        title="Some Global Song",
                        artist="Global Artist"
                    )
                    self.assertEqual(source, "Musixmatch (Synced)")
                    self.assertTrue(is_synced)
                    self.assertIn("Musixmatch 싱크 가사", lyrics)

    def test_resolve_lyrics_tier4_subtitles_when_apis_miss(self):
        # 1~3순위 API 실패 시 4순위 YouTube Subtitles로 정상 폴백
        sample_vtt = """WEBVTT
00:00:10.000 --> 00:00:14.000
유튜브 자막 가사
"""
        with patch("core.lyrics.fetch_alsong_lyrics", return_value=None):
            with patch("core.lyrics.fetch_lrclib_lyrics", return_value=None):
                with patch("core.lyrics.fetch_musixmatch_lyrics", return_value=None):
                    lyrics, is_synced, source = resolve_lyrics(
                        title="Unknown Indie Track",
                        artist="Indie",
                        embedded_subtitles=sample_vtt
                    )
                    self.assertEqual(source, "YouTube Subtitles (Synced)")
                    self.assertTrue(is_synced)
                    self.assertIn("[00:10.00] 유튜브 자막 가사", lyrics)

    def test_musixmatch_retry_on_timeout(self):
        # Musixmatch 타임아웃 및 503 발생 시 지수 백오프 재시도 검증
        import requests
        from unittest.mock import MagicMock
        with patch("requests.get") as mock_get:
            # 1차 시도 Timeout, 2차 시도 200 성공
            mock_success = MagicMock()
            mock_success.status_code = 200
            mock_get.side_effect = [requests.exceptions.Timeout("Read timed out"), mock_success]

            resp = _request_musixmatch_with_retry("http://fake", {}, {}, timeout=1, max_retries=2)
            self.assertIsNotNone(resp)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(mock_get.call_count, 2)

    def test_alsong_retry_on_timeout(self):
        # 알송 타임아웃 발생 시 재시도 검증
        import requests
        from unittest.mock import MagicMock
        with patch("requests.post") as mock_post:
            mock_success = MagicMock()
            mock_success.status_code = 200
            mock_success.text = "<xml>ok</xml>"
            mock_post.side_effect = [requests.exceptions.Timeout("Read timed out"), mock_success]

            resp = _post_alsong_with_retry("<xml/>", {}, timeout=1, max_retries=2)
            self.assertIsNotNone(resp)
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(mock_post.call_count, 2)


if __name__ == '__main__':
    unittest.main()
