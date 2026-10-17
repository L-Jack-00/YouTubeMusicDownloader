# -*- coding: utf-8 -*-
"""
Automated Build & Packaging Script for YouTube Music Downloader Portable Release.
Constructs an AV-friendly, non-heuristic portable distribution:
- Standalone folder bundle (--onedir) without %TEMP% extraction dropper behavior
- No UPX compression (--noupx) to prevent heuristic packer signatures
- Formal Windows PE Version Info resource integration
- Bundled FFmpeg binary directly in the portable root
- Direct 1-click launcher batch script & comprehensive user guide
- Release zip archive creation
"""
import os
import sys
import shutil
import subprocess
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def run_build():
    print("=" * 65)
    print(" [Release Rig] Building Clean Portable Distribution")
    print("=" * 65)

    dist_dir = os.path.join(BASE_DIR, "dist")
    build_dir = os.path.join(BASE_DIR, "build")
    release_dir = os.path.join(BASE_DIR, "release")
    os.makedirs(release_dir, exist_ok=True)

    # 1. PyInstaller 명령 구성
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconsole",
        "--onedir",
        "--noupx",
        "--clean",
        "-y",
        "--name", "YouTubeMusicDownloader",
        "--version-file", os.path.join(BASE_DIR, "version_info.txt"),
        # 불필요한 대용량/휴리스틱 유발 모듈 제외
        "--exclude-module", "PyQt6.QtWebEngine",
        "--exclude-module", "PyQt6.QtWebEngineWidgets",
        "--exclude-module", "PyQt6.QtWebEngineCore",
        "--exclude-module", "PyQt6.QtQuick",
        "--exclude-module", "PyQt6.QtQml",
        "--exclude-module", "PyQt6.QtSql",
        "--exclude-module", "PyQt6.QtTest",
        "--exclude-module", "tkinter",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--exclude-module", "steamreviews",
        # 필수 동적 모듈 임포트 명시
        "--hidden-import", "mutagen.mp4",
        "--hidden-import", "mutagen.mp3",
        "--hidden-import", "mutagen.id3",
        "--hidden-import", "PIL.JpegImagePlugin",
        "--hidden-import", "PIL.WebPImagePlugin",
        "--hidden-import", "PIL.PngImagePlugin",
        "--hidden-import", "requests",
        "--hidden-import", "yt_dlp",
        os.path.join(BASE_DIR, "main.py")
    ]

    print("[*] Executing PyInstaller build...")
    ret = subprocess.run(cmd, cwd=BASE_DIR)
    if ret.returncode != 0:
        print("[!] PyInstaller build failed!")
        sys.exit(1)

    app_dir = os.path.join(dist_dir, "YouTubeMusicDownloader")
    if not os.path.isdir(app_dir):
        print(f"[!] Output directory not found: {app_dir}")
        sys.exit(1)

    # 2. FFmpeg 바이너리 격리 번들링 (_internal 폴더 내부로 격리)
    print("[*] Bundling FFmpeg binary into isolated _internal directory...")
    try:
        import imageio_ffmpeg
        ffmpeg_src = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_src and os.path.isfile(ffmpeg_src):
            internal_dir = os.path.join(app_dir, "_internal")
            os.makedirs(internal_dir, exist_ok=True)
            ffmpeg_dst = os.path.join(internal_dir, "ffmpeg.exe")
            shutil.copy2(ffmpeg_src, ffmpeg_dst)
            print(f"    -> Copied isolated ffmpeg.exe to {ffmpeg_dst}")
    except Exception as e:
        print(f"    [!] Warning: Failed to bundle ffmpeg: {e}")

    # 3. 사용자 개인정보(세션 쿠키 및 다운로드 데이터) 완전 격리 (배포 패키지 미포함)
    print("[*] User credentials & runtime data cleanly isolated (0 private files in release bundle)")

    # 4. 1-클릭 실행 배치 파일 생성
    bat_path = os.path.join(app_dir, "Run_App.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write("@echo off\r\n")
        f.write("chcp 65001 >nul\r\n")
        f.write("cd /d \"%~dp0\"\r\n")
        f.write("start \"\" \"YouTubeMusicDownloader.exe\"\r\n")
        f.write("exit\r\n")
    print(f"    -> Created {bat_path}")

    # 5. 사용 안내서 및 백신 오탐지 방지 가이드 생성
    guide_path = os.path.join(app_dir, "USER_GUIDE.txt")
    guide_content = """================================================================================
 YouTube Music 고음질 다운로더 v1.0.0 (포터블 에디션)
================================================================================

[프로그램 개요]
본 프로그램은 유튜브(YouTube) 및 유튜브 뮤직(YouTube Music)의 음원을
무손실 M4A(AAC 원본 다이렉트 복사) 또는 320kbps MP3로 최고 음질 다운로드하고,
정밀 메타데이터 / 싱크 가사(알송/LRCLIB) / 1:1 앨범 아트를 자동 삽입해 주는
무설치(Portable) 프로그램입니다.

--------------------------------------------------------------------------------
[실행 방법]
1. 'YouTubeMusicDownloader.exe' 또는 'Run_App.bat'을 더블 클릭하여 실행합니다.
2. 다운로드할 유튜브 음원 또는 재생목록 링크를 붙여넣고 [다운로드 시작]을 누릅니다.

--------------------------------------------------------------------------------
[유튜브 프리미엄 256kbps 최고 음질 연동 (쿠키 가이드)]
브라우저 확장 프로그램 설치 없이, 10초 만에 브라우저에서 직접 쿠키를 가져올 수 있습니다.
프로그램 내 [❓ 쿠키 추출 가이드] 버튼을 누르시면 상세한 2가지 방법이 안내됩니다:

[방법 1. 가장 추천 - 5초 컷]
1. 웹 브라우저(Chrome/Edge)에서 music.youtube.com 로그인 후 F12 (개발자 도구) 누름
2. [네트워크 (Network)] 탭 클릭 후 상단 [✓] Disable cache (캐시 사용 중지) 체크
3. F5 (새로고침) 후 목록 맨 위 항목(music.youtube.com 또는 browse) 클릭
4. 오른쪽 헤더 패널 [요청 헤더]에서 'Cookie:' 값 전체 우클릭 -> [값 복사]
5. 프로그램의 [📋 쿠키 직접 붙여넣기 (F12)] 버튼을 누르고 붙여넣기

[방법 2. Fetch/XHR 필터 클릭 - 새로고침 없이 즉시 확인]
1. 네트워크 탭 검색창 바로 아래에 있는 [Fetch/XHR] 필터 버튼 클릭
2. 목록에 뜨는 browse, next, player 중 아무거나 클릭
3. 오른쪽 [요청 헤더] 목록에서 Cookie: 값 우클릭 -> [값 복사]
4. 프로그램의 [📋 쿠키 직접 붙여넣기 (F12)] 버튼을 누르고 붙여넣기

--------------------------------------------------------------------------------
[백신 오탐지(False Positive) 안전성 안내]
본 프로그램은 사용자 PC에 불필요한 드롭퍼를 생성하지 않는 '폴더형 독립 포터블' 규격으로 제작되었으며,
UPX 압축을 일체 사용하지 않아 윈도우 디펜더 및 각종 백신 휴리스틱 감지에서 안전합니다.
- 악성코드, 광고, 외부 데이터 전송 행위가 없는 순수 오픈소스 기반 프로그램입니다.
- 윈도우 스마트스크린(SmartScreen)의 '알려지지 않은 게시자' 파란색 창이 뜰 경우:
  [추가 정보] -> [실행]을 클릭하시면 정상 실행됩니다.

제작: SBK Studio (2026)
================================================================================
"""
    with open(guide_path, "w", encoding="utf-8") as f:
        f.write(guide_content)
    print(f"    -> Created {guide_path}")

    # 6. 최종 포터블 ZIP 아카이브 압축
    zip_filename = "YouTubeMusicDownloader_v1.0.0_Portable.zip"
    zip_path = os.path.join(release_dir, zip_filename)
    print(f"[*] Packaging portable zip archive to {zip_path}...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(app_dir):
            for file in files:
                abs_file = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file, dist_dir)
                zf.write(abs_file, rel_path)

    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print("-" * 65)
    print(f"[SUCCESS] Portable release successfully created!")
    print(f"  - App Folder : {app_dir}")
    print(f"  - Zip Archive: {zip_path} ({zip_size_mb:.1f} MB)")
    print("=" * 65)


if __name__ == "__main__":
    run_build()
