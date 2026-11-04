# -*- coding: utf-8 -*-
"""
yt-dlp version check and update utility.
"""
import os
import sys
import json
import urllib.request
import zipfile
from typing import Tuple


def get_current_ytdlp_version() -> str:
    """현재 설치된 yt-dlp 버전 반환"""
    try:
        import yt_dlp.version
        return yt_dlp.version.__version__
    except Exception:
        try:
            import yt_dlp
            return getattr(yt_dlp, "__version__", "알 수 없음")
        except Exception:
            return "알 수 없음"


def update_ytdlp() -> Tuple[bool, str]:
    """
    PyPI 공식 API를 통해 yt-dlp를 최신 버전으로 업데이트합니다.
    (포터블 바이너리 복제 실행 버그 방지 및 독립 환경 무설치 패치)
    """
    try:
        cur_ver = get_current_ytdlp_version()

        # 1. PyPI 최신 버전 확인
        req = urllib.request.Request(
            "https://pypi.org/pypi/yt-dlp/json",
            headers={"User-Agent": "ytmusic-dl"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest_ver = data.get("info", {}).get("version", "")
        if not latest_ver:
            return False, "최신 버전 정보를 가져오지 못했습니다."

        if cur_ver != "알 수 없음" and cur_ver >= latest_ver:
            return True, f"이미 최신 버전의 yt-dlp 엔진(v{cur_ver})을 사용 중입니다."

        # 2. 순수 파이썬 wheel URL 탐색
        wheel_url = None
        for item in data.get("urls", []):
            fn = item.get("filename", "")
            if fn.endswith("-py3-none-any.whl") or fn.endswith(".whl"):
                wheel_url = item.get("url")
                break

        if not wheel_url:
            return False, f"최신 버전(v{latest_ver})의 다운로드 패키지를 찾지 못했습니다."

        # 3. 대상 패키지 디렉터리 결정
        app_dir = (
            os.path.dirname(os.path.abspath(sys.executable))
            if getattr(sys, "frozen", False)
            else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        target_internal = (
            os.path.join(app_dir, "_internal")
            if os.path.isdir(os.path.join(app_dir, "_internal"))
            else app_dir
        )

        temp_whl = os.path.join(target_internal, "_yt_dlp_update.whl")
        urllib.request.urlretrieve(wheel_url, temp_whl)

        # 4. wheel 압축 해제
        with zipfile.ZipFile(temp_whl, "r") as zf:
            for member in zf.namelist():
                if member.startswith("yt_dlp/"):
                    zf.extract(member, target_internal)

        try:
            os.remove(temp_whl)
        except Exception:
            pass

        return (
            True,
            f"yt-dlp 엔진이 최신 버전(v{latest_ver})으로 성공적으로 업데이트되었습니다!\n\n프로그램을 재시작하시면 최신 엔진이 적용됩니다.",
        )

    except Exception as e:
        return False, f"엔진 업데이트 중 오류가 발생했습니다:\n{str(e)}"
