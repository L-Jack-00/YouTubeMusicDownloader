# -*- coding: utf-8 -*-
import io
import unittest
import http.cookiejar
from gui.cookie_paste_dialog import parse_raw_cookie_to_netscape


class TestCookieParser(unittest.TestCase):
    def test_standard_cookie_string(self):
        raw = "SID=abc123; HSID=def456; SAPISID=xyz789; __Secure-3PSID=sec123"
        out, count = parse_raw_cookie_to_netscape(raw)
        self.assertEqual(count, 4)
        self.assertIn(".youtube.com\tTRUE\t/\tTRUE", out)
        self.assertIn("SID\tabc123", out)

    def test_cookie_prefix(self):
        raw = "Cookie: SID=abc123; HSID=def456"
        out, count = parse_raw_cookie_to_netscape(raw)
        self.assertEqual(count, 2)
        self.assertIn("SID\tabc123", out)

    def test_curl_command(self):
        raw = "curl 'https://music.youtube.com' -H 'cookie: SID=abc123; HSID=def456' --compressed"
        out, count = parse_raw_cookie_to_netscape(raw)
        self.assertEqual(count, 2)
        self.assertIn("SID\tabc123", out)

    def test_multiline_devtools_headers(self):
        raw = ":authority: music.youtube.com\naccept: */*\ncookie: SID=abc123; HSID=def456\nuser-agent: Mozilla/5.0"
        out, count = parse_raw_cookie_to_netscape(raw)
        self.assertEqual(count, 2)
        self.assertIn("SID\tabc123", out)

    def test_multiline_cookie_separated_by_newlines(self):
        raw = "SID=abc123\nHSID=def456\nSAPISID=xyz789"
        out, count = parse_raw_cookie_to_netscape(raw)
        self.assertEqual(count, 3)

    def test_netscape_format(self):
        raw = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t1893456000\tSID\tabc123\n.google.com\tTRUE\t/\tTRUE\t1893456000\tHSID\tdef456"
        out, count = parse_raw_cookie_to_netscape(raw)
        self.assertEqual(count, 2)
        self.assertIn("SID\tabc123", out)

    def test_json_array_format(self):
        raw = '[{"name": "SID", "value": "abc123"}, {"name": "HSID", "value": "def456"}]'
        out, count = parse_raw_cookie_to_netscape(raw)
        self.assertEqual(count, 2)
        self.assertIn("SID\tabc123", out)

    def test_mozilla_cookie_jar_compatibility(self):
        raw = "SID=abc123; HSID=def456; SAPISID=xyz789"
        out, count = parse_raw_cookie_to_netscape(raw)
        jar = http.cookiejar.MozillaCookieJar()
        jar._really_load(io.StringIO(out), "test.txt", ignore_discard=True, ignore_expires=True)
        # 3 cookies * 2 domains (.youtube.com & .google.com) = 6 cookies loaded
        self.assertEqual(len(list(jar)), 6)

    def test_empty_or_invalid_input(self):
        out, count = parse_raw_cookie_to_netscape("")
        self.assertEqual(count, 0)
        self.assertEqual(out, "")

        out, count = parse_raw_cookie_to_netscape("this is some random text without any equals signs")
        self.assertEqual(count, 0)
