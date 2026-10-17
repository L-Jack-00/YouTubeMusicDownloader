# -*- coding: utf-8 -*-
"""
Application Entry Point for YouTube Music Downloader.
Version: v1.0.0
"""
import sys
import os

# In Windows GUI / no-console mode, sys.stdout and sys.stderr can be None.
class _NullStream:
    def write(self, text):
        pass
    def flush(self):
        pass
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

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("YouTube Music 고음질 다운로더")
    app.setApplicationVersion("1.0.0")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
