# -*- coding: utf-8 -*-
"""
Unit tests for Lyrics Language Detection & Romanization Rejection Engine.
"""
import unittest
from unittest.mock import patch

from core.lyrics_detector import (
    is_romanized_korean_lyrics,
    is_korean_track,
    has_hangul,
    count_hangul
)
from core.lyrics import (
    resolve_lyrics,
    parse_subtitles_to_lrc,
    extract_lyrics_from_description
)


class TestLyricsDetector(unittest.TestCase):

    def test_romanized_korean_lyrics_detection(self):
        # 1. 전형적인 로마자 발음 가사 (기각 대상)
        romanized_1 = (
            "[00:15.20] saranghaessjanha uri hamkke haessjanha\n"
            "[00:20.50] neoreul bogo sipeo michil geotman gata\n"
            "[00:25.10] geureohge uri dasi mannasseo"
        )
        self.assertTrue(is_romanized_korean_lyrics(romanized_1))

        # 2. 명시적 로마자 태그 포함 가사 (기각 대상)
        romanized_tag = (
            "[00:00.00] (Romanized Lyrics)\n"
            "[00:10.00] Baby I love you so much\n"
            "[00:15.00] You are my everything"
        )
        self.assertTrue(is_romanized_korean_lyrics(romanized_tag))

        # 3. K-POP 후렴구 로마자 전사 (기각 대상)
        romanized_kpop = (
            "[00:10.00] Stay in the middle like you a little\n"
            "[00:15.00] Malhaejwo say it ditto achimeun neomu meoreo\n"
            "[00:20.00] Huljjeok keobeorin nae mami geu gieogi neowa na"
        )
        self.assertTrue(is_romanized_korean_lyrics(romanized_kpop))

        # 4. 정식 한글 가사 (정상 허용)
        real_hangul = (
            "[00:15.20] 사랑했잖아 우리 함께 했잖아\n"
            "[00:20.50] 너를 보고 싶어 미칠 것만 같아\n"
            "[00:25.10] 그렇게 우리 다시 만났어"
        )
        self.assertFalse(is_romanized_korean_lyrics(real_hangul))

        # 5. 한영 혼용 K-POP 정식 가사 (한글 포함 - 정상 허용)
        mixed_kpop = (
            "[00:10.00] Yeah I'm the drama 사건은 다가와 ah oh ay\n"
            "[00:15.00] 거세게 커져가 내 안의 깨어난 emotion"
        )
        self.assertFalse(is_romanized_korean_lyrics(mixed_kpop))

        # 6. 정식 해외 팝송 (정상 허용 - 로마자 아님)
        english_pop = (
            "[00:10.00] I'm in love with the shape of you\n"
            "[00:15.00] We push and pull like a magnet do\n"
            "[00:20.00] Although my heart is falling too"
        )
        self.assertFalse(is_romanized_korean_lyrics(english_pop))

        # 7. 한국 가수의 100% 영어 노래 (BTS Dynamite - 정상 허용)
        bts_dynamite = (
            "[00:15.00] 'Cause I, I, I'm in the stars tonight\n"
            "[00:20.00] So watch me bring the fire and set the night alight\n"
            "[00:25.00] Shining through the city with a little funk and soul"
        )
        self.assertFalse(is_romanized_korean_lyrics(bts_dynamite))

    def test_is_korean_track_detection(self):
        # 한글 제목/가수
        self.assertTrue(is_korean_track(title="사랑했잖아", artist="린"))
        self.assertTrue(is_korean_track(title="좋은 날", artist="아이유"))
        self.assertTrue(is_korean_track(title="TOMBOY", artist="(여자)아이들"))

        # 영문 표기 K-POP 대표 아티스트
        self.assertTrue(is_korean_track(title="Supernova", artist="aespa"))
        self.assertTrue(is_korean_track(title="Hype Boy", artist="NewJeans"))
        self.assertTrue(is_korean_track(title="Dynamite", artist="BTS"))
        self.assertTrue(is_korean_track(title="Shut Down", artist="BLACKPINK"))
        self.assertTrue(is_korean_track(title="I AM", artist="IVE"))

        # 설명란/자막에 한글 포함된 경우
        self.assertTrue(is_korean_track(
            title="Song",
            artist="Unknown",
            description="작사: 김이나, 작곡: 이민수. 이 음원은 공식 배포 음원입니다."
        ))

        # 순수 해외 팝송
        self.assertFalse(is_korean_track(title="Cruel Summer", artist="Taylor Swift"))
        self.assertFalse(is_korean_track(title="Shape of You", artist="Ed Sheeran"))
        self.assertFalse(is_korean_track(title="Bohemian Rhapsody", artist="Queen"))

    def test_has_hangul_and_count(self):
        self.assertTrue(has_hangul("Hello 안녕하세요"))
        self.assertFalse(has_hangul("Hello World 123!"))
        self.assertEqual(count_hangul("안녕 세상아"), 5)
        self.assertEqual(count_hangul("Hello"), 0)

    @patch('core.lyrics.fetch_alsong_lyrics')
    @patch('core.lyrics.fetch_lrclib_lyrics')
    def test_korean_track_rejects_romanized_and_uses_hangul_alsong(self, mock_lrclib, mock_alsong):
        # 알송에서 정식 한글 싱크 가사 반환 시 1순위로 채택
        mock_alsong.return_value = ("[00:10.00] 사랑해 영원히", True)
        mock_lrclib.return_value = ("[00:10.00] saranghae yeongwonhi", True)

        text, is_synced, source = resolve_lyrics(title="사랑해", artist="가수")
        self.assertEqual(source, "AlSong (Synced)")
        self.assertEqual(text, "[00:10.00] 사랑해 영원히")
        self.assertTrue(is_synced)

    @patch('core.lyrics.fetch_alsong_lyrics')
    @patch('core.lyrics.fetch_lrclib_lyrics')
    def test_korean_track_rejects_romanized_lrclib_falls_to_subtitles(self, mock_lrclib, mock_alsong):
        # 알송 없음, LRCLIB는 로마자 가사 반환 -> 로마자 기각하고 유튜브 한글 자막 채택
        mock_alsong.return_value = None
        mock_lrclib.return_value = ("[00:15.00] saranghaessjanha uri hamkke haessjanha", True)

        subtitles = "WEBVTT\n\n00:00:15.000 --> 00:00:20.000\n사랑했잖아 우리 함께 했잖아\n"
        text, is_synced, source = resolve_lyrics(
            title="사랑했잖아",
            artist="린",
            embedded_subtitles=subtitles
        )
        self.assertEqual(source, "YouTube Subtitles (Synced)")
        self.assertIn("사랑했잖아", text)
        self.assertTrue(is_synced)

    @patch('core.lyrics.fetch_alsong_lyrics')
    @patch('core.lyrics.fetch_lrclib_lyrics')
    def test_foreign_pop_prefers_lrclib_original_sync(self, mock_lrclib, mock_alsong):
        # 해외 팝송의 경우 LRCLIB 원문 영어 싱크 가사를 알송보다 우선 채택
        mock_lrclib.return_value = ("[00:15.00] I'm in love with the shape of you", True)
        mock_alsong.return_value = ("[00:15.00] 아임 인 러브 위드 더 셰이프 오브 유", True)

        text, is_synced, source = resolve_lyrics(title="Shape of You", artist="Ed Sheeran")
        self.assertEqual(source, "LRCLIB (Synced)")
        self.assertIn("shape of you", text.lower())
        self.assertTrue(is_synced)


if __name__ == '__main__':
    unittest.main()
