# -*- coding: utf-8 -*-
"""
Dialog for manually pasting browser cookie headers (F12) without extensions.
"""
import os
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
)


def parse_raw_cookie_to_netscape(raw_cookie_text: str) -> str:
    """
    브라우저 F12 네트워크 탭에서 복사한 'Cookie: ...' 또는 순수 쿠키 문자열을
    yt-dlp가 인식할 수 있는 Netscape cookies.txt 형식으로 변환합니다.
    """
    clean_text = raw_cookie_text.strip()
    if clean_text.lower().startswith("cookie:"):
        clean_text = clean_text[7:].strip()

    lines = [
        "# Netscape HTTP Cookie File\n",
        "# Converted from browser request header\n\n"
    ]
    curr_time = int(time.time()) + 31536000  # 1년 유효기간 부여

    pairs = clean_text.split(";")
    count = 0
    for item in pairs:
        if "=" in item:
            name, val = item.strip().split("=", 1)
            name = name.strip()
            val = val.strip()
            if name:
                count += 1
                lines.append(f".youtube.com\tTRUE\t/\tTRUE\t{curr_time}\t{name}\t{val}\n")
                lines.append(f".google.com\tTRUE\t/\tTRUE\t{curr_time}\t{name}\t{val}\n")

    return "".join(lines), count


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
        self.resize(650, 480)
        self._init_ui()

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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 사용 가이드 안내
        guide_label = QLabel(
            "<b>💡 확장 프로그램 없이 10초 만에 쿠키 복사하는 방법:</b><br>"
            "1. 평소 쓰시는 브라우저(Edge, Chrome 등)에서 <b>music.youtube.com</b>을 엽니다.<br>"
            "2. 키보드 <b>[F12]</b>(개발자 도구)를 누른 후 <b>[네트워크 (Network)]</b> 탭을 클릭합니다.<br>"
            "3. 페이지를 새로고침(F5)하고 맨 위 목록 중 하나를 클릭합니다.<br>"
            "4. 오른쪽 <b>[요청 헤더 (Request Headers)]</b>의 <b>Cookie:</b> 값 전체를 우클릭하여 복사합니다.<br>"
            "5. 아래 입력창에 붙여넣고 [쿠키 적용]을 누르면 끝납니다."
        )
        guide_label.setStyleSheet("color: #222222; font-size: 12px; line-height: 1.5;")
        layout.addWidget(guide_label)

        # 쿠키 붙여넣기 텍스트 박스
        self.edit_cookie = QTextEdit()
        self.edit_cookie.setPlaceholderText(
            "여기에 복사한 쿠키 값을 붙여넣으세요 (예: SID=...; HSID=...; SAPISID=...)"
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
        self.btn_apply = QPushButton("쿠키 적용 및 영구 저장")
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background-color: #E62117;
                color: #FFFFFF;
                font-weight: bold;
                padding: 9px 22px;
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

    def _handle_apply(self):
        text = self.edit_cookie.toPlainText().strip()
        if not text or "=" not in text:
            QMessageBox.warning(self, "입력 확인", "올바른 쿠키 문자열을 입력해 주세요.")
            return

        netscape_content, cookie_count = parse_raw_cookie_to_netscape(text)
        if cookie_count == 0:
            QMessageBox.warning(self, "파싱 오류", "쿠키 키-값을 찾을 수 없습니다.")
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
