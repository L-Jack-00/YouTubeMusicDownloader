# -*- coding: utf-8 -*-
"""
FFmpeg binary resolver utility.
"""
import os
import sys
import shutil
from typing import Optional


def find_ffmpeg_binary() -> Optional[str]:
    """
    FFmpeg 바이너리 경로를 탐색하여 반환합니다.
    우선순위:
    1. 애플리케이션 실행 디렉터리 내 ffmpeg.exe (번들/포터블 환경)
    2. imageio-ffmpeg 내장 바이너리
    3. 시스템 PATH 환경 변수
    """
    # 1. 실행 위치 기준 확인
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_candidates = [
        os.path.join(base_dir, "ffmpeg.exe"),
        os.path.join(base_dir, "bin", "ffmpeg.exe"),
        os.path.join(base_dir, "_internal", "ffmpeg.exe"),
        os.path.join(os.path.dirname(sys.executable), "ffmpeg.exe"),
        os.path.join(os.path.dirname(sys.executable), "_internal", "ffmpeg.exe"),
        os.path.join(os.path.dirname(sys.executable), "bin", "ffmpeg.exe"),
    ]
    for candidate in local_candidates:
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)

    # 2. imageio-ffmpeg 패키지 확인
    try:
        import imageio_ffmpeg
        exe_path = imageio_ffmpeg.get_ffmpeg_exe()
        if exe_path and os.path.isfile(exe_path):
            return os.path.abspath(exe_path)
    except Exception:
        pass

    # 3. 시스템 PATH 확인
    sys_path = shutil.which("ffmpeg")
    if sys_path and os.path.isfile(sys_path):
        return os.path.abspath(sys_path)

    return None
