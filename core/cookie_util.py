# -*- coding: utf-8 -*-
"""
Browser cookie lock detection and text sanitization utility.
"""
import os
import re
from typing import Tuple, Optional


def strip_ansi_codes(text: str) -> str:
    """터미널 ANSI 이스케이프 코드 제거"""
    if not text:
        return ""
    ansi_regex = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    return ansi_regex.sub('', text)


def get_app_root_dir() -> str:
    """애플리케이션 루트 디렉터리 경로 반환 (개발 환경 및 PyInstaller 포터블 환경 지원)"""
    import sys
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_browser_cookie_path(browser_name: str) -> Optional[str]:
    """브라우저별 쿠키 파일 경로 반환 (Windows 환경)"""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if not local_app_data:
        return None

    b_lower = browser_name.lower()
    if b_lower == "edge":
        return os.path.join(local_app_data, "Microsoft", "Edge", "User Data", "Default", "Network", "Cookies")
    elif b_lower == "chrome":
        return os.path.join(local_app_data, "Google", "Chrome", "User Data", "Default", "Network", "Cookies")
    elif b_lower == "brave":
        return os.path.join(local_app_data, "BraveSoftware", "Brave-Browser", "User Data", "Default", "Network", "Cookies")
    elif b_lower == "whale":
        return os.path.join(local_app_data, "Naver", "Naver Whale", "User Data", "Default", "Network", "Cookies")

    return None


def is_browser_cookie_locked(browser_name: str) -> Tuple[bool, Optional[str]]:
    """
    브라우저의 쿠키 데이터베이스가 실행 중인 프로세스에 의해 잠겨 있는지 확인합니다.
    반환값: (잠김 여부, 쿠키 파일 경로)
    """
    cookie_path = get_browser_cookie_path(browser_name)
    if not cookie_path or not os.path.exists(cookie_path):
        return False, cookie_path

    try:
        # 단독 읽기 시도
        with open(cookie_path, "rb") as f:
            f.read(1)
        return False, cookie_path
    except (PermissionError, OSError):
        # 다른 프로세스(브라우저)에서 배타적 잠금 상태
        return True, cookie_path
