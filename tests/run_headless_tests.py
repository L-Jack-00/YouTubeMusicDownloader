# -*- coding: utf-8 -*-
"""
Headless Test Suite Runner
Executes all unit tests in memory and outputs structured summary.
"""
import sys
import unittest
import os

# Set UTF-8 encoding for Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def run_all_tests():
    print("=" * 65)
    print(" [LJack Protocol] Headless Unit Test Suite Runner")
    print("=" * 65)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    from tests.test_lyrics import TestLyricsModule
    from tests.test_image_util import TestImageUtil
    from tests.test_tagger import TestTagger
    from tests.test_fsm_and_worker import TestStateAndDownloader

    suite.addTests(loader.loadTestsFromTestCase(TestLyricsModule))
    suite.addTests(loader.loadTestsFromTestCase(TestImageUtil))
    suite.addTests(loader.loadTestsFromTestCase(TestTagger))
    suite.addTests(loader.loadTestsFromTestCase(TestStateAndDownloader))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("-" * 65)
    if result.wasSuccessful():
        print(f"[PASS] All {result.testsRun} test cases passed successfully.")
        print("=" * 65)
        return 0
    else:
        print(f"[FAIL] Failures: {len(result.failures)}, Errors: {len(result.errors)}")
        print("=" * 65)
        return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
