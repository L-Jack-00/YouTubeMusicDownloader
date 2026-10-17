# -*- coding: utf-8 -*-
"""
yt-dlp version check and update utility.
"""
import sys
import subprocess
from typing import Tuple
import yt_dlp


def get_current_ytdlp_version() -> str:
    """현재 설치된 yt-dlp 버전 반환"""
    return getattr(yt_dlp, "__version__", "알 수 없음")


def update_ytdlp() -> Tuple[bool, str]:
    """
    yt-dlp를 최신 버전으로 업데이트합니다.
    """
    try:
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
            check=False
        )
        if proc.returncode == 0:
            return True, "yt-dlp가 성공적으로 최신 버전으로 업데이트되었습니다."
        else:
            return False, f"업데이트 실패: {proc.stderr.strip()}"
    except Exception as e:
        return False, f"업데이트 실행 중 오류: {str(e)}"
