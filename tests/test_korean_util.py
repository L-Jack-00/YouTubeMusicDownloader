# -*- coding: utf-8 -*-
import unittest
from core.korean_util import (
    prefer_korean_artist,
    prefer_korean_title,
    refine_korean_metadata,
    has_hangul
)


class TestKoreanUtil(unittest.TestCase):
    def test_has_hangul(self):
        self.assertTrue(has_hangul("에픽하이"))
        self.assertTrue(has_hangul("Epik High (에픽하이)"))
        self.assertFalse(has_hangul("Epik High"))
        self.assertFalse(has_hangul("12345!@#$"))

    def test_prefer_korean_artist_mapped(self):
        self.assertEqual(prefer_korean_artist("Dynamicduo"), "다이나믹 듀오")
        self.assertEqual(prefer_korean_artist("dynamic duo"), "다이나믹 듀오")
        self.assertEqual(prefer_korean_artist("Drunken Tiger"), "드렁큰 타이거")
        self.assertEqual(prefer_korean_artist("Epik High"), "에픽하이")
        self.assertEqual(prefer_korean_artist("Leessang"), "리쌍")
        self.assertEqual(prefer_korean_artist("Baechigi"), "배치기")
        self.assertEqual(prefer_korean_artist("Supreme Team"), "슈프림팀")

    def test_prefer_korean_artist_bilingual(self):
        self.assertEqual(prefer_korean_artist("드렁큰 타이거 (Drunken Tiger)"), "드렁큰 타이거")
        self.assertEqual(prefer_korean_artist("넬 (Nell)"), "넬")
        self.assertEqual(prefer_korean_artist("리쌍 (LeeSsang)"), "리쌍")
        self.assertEqual(prefer_korean_artist("배치기 (Baechigi)"), "배치기")
        self.assertEqual(prefer_korean_artist("에픽하이 Epik High"), "에픽하이")

    def test_prefer_korean_artist_multi(self):
        self.assertEqual(prefer_korean_artist("Dynamicduo, DJ Premier"), "다이나믹 듀오, DJ Premier")
        self.assertEqual(prefer_korean_artist("리쌍 LeeSsang, 정인 Jung In"), "리쌍, 정인")
        self.assertEqual(prefer_korean_artist("Supreme Team, Young Jun"), "슈프림팀, 영준")

    def test_prefer_korean_title_patterns(self):
        self.assertEqual(prefer_korean_title("Then Then Then (그땐 그땐 그땐)"), "그땐 그땐 그땐")
        self.assertEqual(prefer_korean_title("소년이여 (A Boy)"), "소년이여")
        self.assertEqual(prefer_korean_title("땡땡땡 Dang Dang Dang"), "땡땡땡")
        self.assertEqual(prefer_korean_title("난 널 원해"), "난 널 원해")
        self.assertEqual(prefer_korean_title("Good Life"), "Good Life")
        self.assertEqual(prefer_korean_title("Supermagic"), "Supermagic")

    def test_refine_korean_metadata(self):
        # 1. raw_title에 한글 가수가 있고 yt-dlp artist는 영문인 경우
        a1, t1 = refine_korean_metadata("다이나믹 듀오 - Go Back", "Dynamicduo", "Go Back")
        self.assertEqual(a1, "다이나믹 듀오")
        self.assertEqual(t1, "Go Back")

        # 2. raw_title에 영문/한글 복합 가수와 부제가 있는 경우
        a2, t2 = refine_korean_metadata(
            "에픽하이 (EPIK HIGH) - Love Love Love",
            "Epik High",
            "Love Love Love"
        )
        self.assertEqual(a2, "에픽하이")
        self.assertEqual(t2, "Love Love Love")

        # 3. 영문 (한글) 곡명 정제
        a3, t3 = refine_korean_metadata(
            "Supreme Team, Young Jun - Then Then Then (그땐 그땐 그땐)",
            "Supreme Team",
            "Then Then Then (그땐 그땐 그땐)"
        )
        self.assertEqual(a3, "슈프림팀, 영준")
        self.assertEqual(t3, "그땐 그땐 그땐")
