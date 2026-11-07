# -*- coding: utf-8 -*-
"""
Application Entry Point for ytmusic-dl.
Version: v1.3.6
"""
import sys
import os
import io
import traceback

# In Windows GUI / no-console mode, ensure robust stdout/stderr to prevent crashes
class _NullStream(io.StringIO):
    def write(self, text):
        return len(text)
    def flush(self):
        pass
    def isatty(self):
        return False
    @property
    def encoding(self):
        return 'utf-8'

if sys.stdout is None:
    sys.stdout = _NullStream()
else:
    try:
        if getattr(sys.stdout, 'encoding', None) != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = _NullStream()
else:
    try:
        if getattr(sys.stderr, 'encoding', None) != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


def _global_excepthook(exctype, value, tb):
    """예기치 않은 예외로 인한 무단 프로세스 종료(튕김)를 방지하고 crash.log에 기록합니다."""
    err_text = "".join(traceback.format_exception(exctype, value, tb))
    try:
        from core.cookie_util import get_app_root_dir
        log_path = os.path.join(get_app_root_dir(), "crash.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(err_text + "\n" + "=" * 60 + "\n")
    except Exception:
        pass


sys.excepthook = _global_excepthook

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ytmusic-dl")
    app.setApplicationVersion("1.3.6")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
