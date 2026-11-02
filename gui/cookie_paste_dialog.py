# -*- coding: utf-8 -*-
"""
Dialog for manually pasting browser cookie headers (F12) without extensions.
Supports raw cookies, cURL, DevTools Request Headers blocks, Netscape cookies.txt, and JSON arrays.
"""
import os
import re
import json
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox, QFrame
)


def parse_raw_cookie_to_netscape(raw_cookie_text: str) -> tuple[str, int]:
    """
    브라우저 F12 네트워크 탭에서 복사한 'Cookie: ...' 또는 순수 쿠키 문자열,
    cURL 명령어, 요청 헤더 블록, Netscape cookies.txt, JSON 등을
    yt-dlp가 인식할 수 있는 표준 Netscape cookies.txt 형식으로 변환합니다.
    """
    text = (raw_cookie_text or "").strip()
    if not text:
        return "", 0

    curr_time = int(time.time()) + 31536000  # 1년 유효기간 부여

    # 1. Format: 이미 Netscape cookies.txt 형식인 경우
    if "# Netscape" in text or "\tTRUE\t" in text or "\tFALSE\t" in text:
        valid_lines = [
            "# Netscape HTTP Cookie File\n",
            "# Converted from Netscape cookies.txt\n\n"
        ]
        count = 0
        for line in text.splitlines():
            line_s = line.strip()
            if not line_s or line_s.startswith("#"):
                continue
            parts = line_s.split("\t")
            if len(parts) >= 7:
                domain, flag, path, secure, expiry, name, value = parts[:7]
                domain = domain.strip()
                flag = flag.strip()
                path = path.strip()
                secure = secure.strip()
                expiry = expiry.strip()
                name = name.strip().replace("\t", "").replace("\r", "").replace("\n", "")
                value = value.strip().replace("\t", "").replace("\r", "").replace("\n", "")
                if name:
                    valid_lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")
                    count += 1
        if count > 0:
            return "".join(valid_lines), count

    # 2. Format: JSON 쿠키 배열 형식 (Cookie-Editor, EditThisCookie 등)
    if text.startswith("[") and text.endswith("]"):
        try:
            items = json.loads(text)
            if isinstance(items, list):
                cookie_dict = {}
                for item in items:
                    if isinstance(item, dict) and "name" in item and "value" in item:
                        c_name = str(item["name"]).strip().replace("\t", "").replace("\r", "").replace("\n", "")
                        c_val = str(item["value"]).strip().replace("\t", "").replace("\r", "").replace("\n", "")
                        if c_name:
                            cookie_dict[c_name] = c_val
                if cookie_dict:
                    lines = [
                        "# Netscape HTTP Cookie File\n",
                        "# Converted from JSON cookies\n\n"
                    ]
                    for name, val in cookie_dict.items():
                        lines.append(f".youtube.com\tTRUE\t/\tTRUE\t{curr_time}\t{name}\t{val}\n")
                        lines.append(f".google.com\tTRUE\t/\tTRUE\t{curr_time}\t{name}\t{val}\n")
                    return "".join(lines), len(cookie_dict)
        except Exception:
            pass

    # 3. cURL 명령어, 요청 헤더 블록, 또는 일반 텍스트에서 Cookie 헤더 추출
    cookie_str = ""

    # 3-1. cURL 명령어 패턴 (-H 'cookie: ...' or -H "cookie: ...")
    curl_match = re.search(r'-[Hh]\s+[\'"]cookie:\s*([^\'"]+)[\'"]', text, re.IGNORECASE)
    if curl_match:
        cookie_str = curl_match.group(1).strip()
    else:
        # 3-2. 멀티라인 요청 헤더 블록 (Chrome F12 개발자 도구 복사본)
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            line_clean = line.strip()
            if line_clean.lower().startswith("cookie:") or line_clean.lower().startswith(":cookie:"):
                extracted = line_clean.split(":", 1)[1].strip()
                if extracted:
                    cookie_str = extracted
                    break
                else:
                    # Cookie: 키 다음 줄에 값이 있는 경우
                    subsequent = []
                    for next_line in lines[idx + 1:]:
                        nl_s = next_line.strip()
                        if not nl_s:
                            continue
                        if (re.match(r'^[a-zA-Z0-9_\-]+:', nl_s) or nl_s.startswith(":")) and "=" not in nl_s.split(":", 1)[0]:
                            break
                        subsequent.append(nl_s)
                    if subsequent:
                        cookie_str = " ".join(subsequent)
                        break

    if not cookie_str:
        cookie_str = text

    # 양쪽 따옴표 제거
    if (cookie_str.startswith('"') and cookie_str.endswith('"')) or (cookie_str.startswith("'") and cookie_str.endswith("'")):
        cookie_str = cookie_str[1:-1].strip()

    # 4. 세미콜론 및 개행으로 키=값 분리
    cookie_dict = {}
    tokens = re.split(r'[;\r\n]+', cookie_str)
    for token in tokens:
        token = token.strip()
        if not token or "=" not in token:
            continue
        name, val = token.split("=", 1)
        name = name.strip()
        val = val.strip()

        # 접두어 'cookie:' 또는 ':cookie:' 가 이름에 포함된 경우 제거
        if name.lower().startswith("cookie:"):
            name = name[7:].strip()
        elif name.lower().startswith(":cookie:"):
            name = name[8:].strip()
        name = name.lstrip(":")

        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1].strip()

        # 줄바꿈 및 탭 문자 제거 (Netscape 포맷 파손 방지)
        name = name.replace("\t", "").replace("\r", "").replace("\n", "").strip()
        val = val.replace("\t", " ").replace("\r", "").replace("\n", "").strip()

        # 유효한 쿠키 이름 토큰 검증
        if re.match(r'^[a-zA-Z0-9_\-\.\~\%\$\!]+$', name) and not name.lower().startswith("http"):
            cookie_dict[name] = val

    if not cookie_dict:
        return "", 0

    lines = [
        "# Netscape HTTP Cookie File\n",
        "# Converted from browser request header\n\n"
    ]
    for name, val in cookie_dict.items():
        lines.append(f".youtube.com\tTRUE\t/\tTRUE\t{curr_time}\t{name}\t{val}\n")
        lines.append(f".google.com\tTRUE\t/\tTRUE\t{curr_time}\t{name}\t{val}\n")

    return "".join(lines), len(cookie_dict)


class CookiePasteDialog(QDialog):
    """
    플러그인 없이 F12 네트워크 헤더에서 복사한 쿠키를 붙여넣는 대화상자
    """

    def __init__(self, parent=None, save_dir: str = ""):
        super().__init__(parent)
        from core.cookie_util import get_app_root_dir
        self.save_dir = save_dir or get_app_root_dir()
        self.cookie_file_path = os.path.join(self.save_dir, "session_cookies.txt")

        self.setWindowTitle("쿠키 텍스트 직접 입력 (플러그인 불필요)")
        self.resize(680, 520)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
                color: #111111;
                font-family: "Pretendard", "Segoe UI", "Malgun Gothic", sans-serif;
            }
            QLabel {
                color: #111111;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        # 상단 타이틀 및 가이드 링크 버튼
        top_bar = QHBoxLayout()
        title_label = QLabel("<b>📋 브라우저 쿠키 직접 붙여넣기</b>")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #111111;")
        top_bar.addWidget(title_label)
        top_bar.addStretch()

        self.btn_open_guide = QPushButton("📖 쿠키 복사 가이드 보기")
        self.btn_open_guide.setStyleSheet("""
            QPushButton {
                background-color: #F0F4F8;
                color: #1E3A8A;
                font-size: 12px;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
                border: 1px solid #D0DCE5;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
            }
        """)
        self.btn_open_guide.clicked.connect(self._handle_show_guide)
        top_bar.addWidget(self.btn_open_guide)
        layout.addLayout(top_bar)

        # 요약 안내 배너
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #F8F9FA;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(8, 6, 8, 6)
        info_layout.setSpacing(4)

        guide_label = QLabel(
            "<b>💡 쿠키 복사 방법 (F12 개발자 도구):</b><br>"
            "1. 브라우저에서 <b>music.youtube.com</b> 로그인 후 <b>[F12]</b>(개발자 도구) → <b>[네트워크 (Network)]</b> 탭으로 이동합니다.<br>"
            "2. <b>[Disable cache]</b> 체크 후 새로고침(F5)하거나 <b>[Fetch/XHR]</b> 필터를 클릭합니다.<br>"
            "3. 목록의 요청을 클릭하고 오른쪽 <b>[Request Headers]</b>의 <b>Cookie:</b> 값(또는 요청 전체)을 복사하여 아래에 붙여넣으세요."
        )
        guide_label.setStyleSheet("color: #333333; font-size: 12px; line-height: 1.5;")
        guide_label.setWordWrap(True)
        info_layout.addWidget(guide_label)
        layout.addWidget(info_frame)

        # 쿠키 붙여넣기 텍스트 박스
        self.edit_cookie = QTextEdit()
        self.edit_cookie.setPlaceholderText(
            "여기에 복사한 쿠키 값(SID=...; HSID=... 또는 cURL 명령어, cookies.txt 내용)을 붙여넣으세요."
        )
        self.edit_cookie.setStyleSheet("""
            QTextEdit {
                background-color: #FAFAFA;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
                color: #111111;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 10px;
            }
            QTextEdit:focus {
                border: 1px solid #E62117;
                background-color: #FFFFFF;
            }
        """)
        layout.addWidget(self.edit_cookie, 1)

        # 하단 액션 버튼
        btn_box = QHBoxLayout()
        self.btn_apply = QPushButton("쿠키 적용 및 저장")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #E62117;
                color: #FFFFFF;
                font-weight: bold;
                padding: 9px 24px;
                border-radius: 6px;
                border: none;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #FF334B; }
        """)
        self.btn_apply.clicked.connect(self._handle_apply)

        self.btn_cancel = QPushButton("취소")
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #EAEAEA;
                color: #222222;
                padding: 9px 18px;
                border-radius: 6px;
                border: 1px solid #CCCCCC;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #DADADA; }
        """)
        self.btn_cancel.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(self.btn_apply)
        btn_box.addWidget(self.btn_cancel)
        layout.addLayout(btn_box)

    def _handle_show_guide(self):
        try:
            from gui.cookie_guide_dialog import CookieGuideDialog
            guide_dlg = CookieGuideDialog(self)
            guide_dlg.exec()
        except Exception as e:
            QMessageBox.warning(self, "안내", f"가이드 창을 여는 중 문제가 발생했습니다: {str(e)}")

    def _handle_apply(self):
        text = self.edit_cookie.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "입력 확인", "쿠키 텍스트를 입력해 주세요.")
            return

        netscape_content, cookie_count = parse_raw_cookie_to_netscape(text)
        if cookie_count == 0:
            QMessageBox.warning(
                self,
                "쿠키 확인",
                "유효한 쿠키 정보를 찾지 못했습니다.\n\n"
                "개발자 도구(F12)의 Cookie 헤더 값, cURL 명령문, 또는 cookies.txt 텍스트를 입력해 주세요."
            )
            return

        try:
            with open(self.cookie_file_path, "w", encoding="utf-8") as f:
                f.write(netscape_content)

            QMessageBox.information(
                self,
                "적용 완료",
                f"총 {cookie_count}개의 쿠키 키-값이 성공적으로 등록되었습니다!\n"
                f"이제 프리미엄 256kbps 최고 음질로 다운로드가 가능합니다."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"쿠키 저장 중 오류가 발생했습니다: {str(e)}")
