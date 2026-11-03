# -*- coding: utf-8 -*-
"""
Headless unit tests for Google CDN & LRCLIB lyrics engine.
Tests WebVTT/SRT parsing, candidate artist resolution, LRCLIB 503 retry defense, and description lyrics extraction.
"""
import unittest
from core.alsong import clean_search_term
from core.lrclib import get_artist_search_candidates
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

    def test_parse_subtitles_without_timestamps_falls_back_to_plain_lyrics(self):
        sample_plain_sub = """WEBVTT
Kind: captions
Language: ko

이 밤 그날의 반딧불을
당신의 창 가까이 보낼게요
좋은 꿈 이길 바라요
"""
        lyrics, is_synced, source = parse_subtitles_to_lrc(sample_plain_sub)
        self.assertIsNotNone(lyrics)
        self.assertFalse(is_synced)
        self.assertEqual(source, "YouTube Subtitles (Plain)")
        self.assertIn("이 밤 그날의 반딧불을", lyrics)
        self.assertIn("당신의 창 가까이 보낼게요", lyrics)
        self.assertNotIn("WEBVTT", lyrics)
        self.assertNotIn("[00:", lyrics)

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

    def test_resolve_lyrics_subtitles_priority_over_lrclib(self):
        sample_vtt = """WEBVTT

00:00:10.000 --> 00:00:14.000
자막 가사입니다
"""
        lyrics, is_synced, source = resolve_lyrics(
            title="Officially Missing You",
            artist="긱스",
            embedded_subtitles=sample_vtt
        )
        self.assertEqual(source, "YouTube Subtitles (Synced)")
        self.assertTrue(is_synced)
        self.assertIn("[00:10.00] 자막 가사입니다", lyrics)

    def test_resolve_lyrics_lrclib_synced_matching(self):
        # 긱스 Officially Missing You -> LRCLIB 실시간 싱크 가사 정상 획득 검증
        lyrics, is_synced, source = resolve_lyrics(
            title="Officially Missing You",
            artist="긱스 Geeks",
            embedded_subtitles=None
        )
        self.assertIsNotNone(lyrics)
        self.assertTrue(is_synced)
        self.assertEqual(source, "LRCLIB (Synced)")
        self.assertIn("Grandline", lyrics)
        self.assertIn("[00:", lyrics)


if __name__ == '__main__':
    unittest.main()
