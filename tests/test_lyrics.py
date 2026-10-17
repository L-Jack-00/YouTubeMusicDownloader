# -*- coding: utf-8 -*-
"""
Headless unit tests for lyrics parsers and cleaning pipeline.
"""
import unittest
from core.alsong import clean_search_term, parse_alsong_xml
from core.lyrics import resolve_lyrics


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

    def test_parse_alsong_xml(self):
        sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Body>
    <SearchLyric2Response xmlns="http://tempuri.org/">
      <SearchLyric2Result>
        <strLyric>[00:15.20]이 밤 그날의 반딧불을&lt;br&gt;[00:20.10]당신의 창 가까이 보낼게요&lt;br&gt;[00:25.00]사랑한다는 말이에요&lt;br&gt;</strLyric>
      </SearchLyric2Result>
    </SearchLyric2Response>
  </soap:Body>
</soap:Envelope>""".encode('utf-8')
        parsed = parse_alsong_xml(sample_xml)
        self.assertIsNotNone(parsed)
        self.assertIn("반딧불을", parsed)
        self.assertIn("\n", parsed)
        self.assertNotIn("<br>", parsed)
        self.assertNotIn("&lt;br&gt;", parsed)

    def test_resolve_lyrics_prefers_subtitles_first(self):
        lyrics, is_synced, source = resolve_lyrics(
            title="테스트 곡",
            artist="테스트 가수",
            embedded_subtitles="[00:05.00] 자체 자막 테스트 가사입니다."
        )
        self.assertEqual(source, "YouTube Subtitles")
        self.assertTrue(is_synced)
        self.assertIn("자체 자막 테스트", lyrics)


if __name__ == '__main__':
    unittest.main()
