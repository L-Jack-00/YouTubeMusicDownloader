# -*- coding: utf-8 -*-
"""
Intuitive step-by-step Cookie Extraction Guide Dialog.
Incorporates Method 1 (Disable Cache + F5) and Method 2 (Fetch/XHR filter).
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices


class CookieGuideDialog(QDialog):
    """
    브라우저 개발자 도구(F12)를 통해 확장 프로그램 없이
    10초 만에 쿠키를 안전하게 복사하는 가이드 대화상자
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("유튜브 뮤직 쿠키 추출 가이드 (플러그인 불필요)")
        self.resize(720, 640)
        self.setMinimumSize(640, 520)
        self._init_ui()

    def _init_ui(self):
        # 팝업 창 전체 기본 폰트 색상을 선명한 고대비 검정색(#111111)으로 지정
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
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. 상단 헤더
        header_box = QVBoxLayout()
        title = QLabel("💡 10초 만에 브라우저에서 쿠키 가져오기")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #E62117;")
        header_box.addWidget(title)

        subtitle = QLabel(
            "별도의 확장 프로그램 설치 없이, 평소 쓰시는 웹 브라우저(Chrome, Edge 등)의 개발자 도구(F12)에서 "
            "쿠키를 바로 복사할 수 있는 2가지 방법입니다."
        )
        subtitle.setStyleSheet("font-size: 13px; color: #444444; margin-top: 4px; line-height: 1.4;")
        subtitle.setWordWrap(True)
        header_box.addWidget(subtitle)
        layout.addLayout(header_box)

        # 구분선
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("color: #E0E0E0;")
        layout.addWidget(sep)

        # 2. 스크롤 가능한 본문 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background-color: #FAFAFA; border-radius: 8px;")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        # [공통 준비 단계]
        prep_frame = QFrame()
        prep_frame.setStyleSheet("""
            QFrame {
                background-color: #F0F4F8;
                border: 1px solid #D0DCE5;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        prep_layout = QVBoxLayout(prep_frame)
        prep_title = QLabel("📌 [사전 준비] 개발자 도구 열기")
        prep_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E3A8A;")
        prep_desc = QLabel(
            "1. 브라우저에서 <b>music.youtube.com</b>에 접속 후 로그인합니다.<br>"
            "2. 키보드 <b>[F12]</b> 키를 누른 뒤, 상단 탭에서 <b>[네트워크 (Network)]</b>를 클릭합니다."
        )
        prep_desc.setStyleSheet("font-size: 12px; color: #222222; line-height: 1.4;")
        prep_desc.setWordWrap(True)
        prep_layout.addWidget(prep_title)
        prep_layout.addWidget(prep_desc)
        content_layout.addWidget(prep_frame)

        # [방법 1 카드] - 가장 추천: Disable cache + F5
        card1 = QFrame()
        card1.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 2px solid #E62117;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        c1_layout = QVBoxLayout(card1)
        c1_title_box = QHBoxLayout()

        badge1 = QLabel("방법 1")
        badge1.setStyleSheet("""
            background-color: #E62117;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 4px;
        """)
        c1_title = QLabel("<b>[가장 추천] Disable cache 체크 후 새로고침 (5초 컷)</b>")
        c1_title.setStyleSheet("font-size: 14px; color: #111111;")
        c1_title_box.addWidget(badge1)
        c1_title_box.addWidget(c1_title)
        c1_title_box.addStretch()
        c1_layout.addLayout(c1_title_box)

        c1_desc = QLabel(
            "① 네트워크(Network) 탭 상단 메뉴에 있는 <b>[✓] Disable cache</b> (한국어: <b>[✓] 캐시 사용 중지</b>)에 체크합니다.<br>"
            "② 키보드 <b>[F5] (새로고침)</b>를 누릅니다.<br>"
            "③ 목록 맨 위의 요청(<b>music.youtube.com</b> 또는 <b>browse</b>)을 다시 클릭합니다.<br>"
            "④ 오른쪽에 열린 패널에서 아래로 스크롤하시면 <b>경고문 없이</b> <code>Cookie: SID=...; HSID=...</code> 전체 헤더가 깨끗하게 나타납니다!<br>"
            "⑤ <b>Cookie:</b> 값 전체를 우클릭 → <b>[값 복사 (Copy value)]</b>를 선택합니다."
        )
        c1_desc.setStyleSheet("font-size: 12px; color: #222222; line-height: 1.5; margin-top: 6px;")
        c1_desc.setWordWrap(True)
        c1_layout.addWidget(c1_desc)
        content_layout.addWidget(card1)

        # [방법 2 카드] - Fetch/XHR 필터 클릭
        card2 = QFrame()
        card2.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        c2_layout = QVBoxLayout(card2)
        c2_title_box = QHBoxLayout()

        badge2 = QLabel("방법 2")
        badge2.setStyleSheet("""
            background-color: #4B5563;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 4px;
        """)
        c2_title = QLabel("<b>Fetch/XHR 요청 클릭하기 (새로고침 없이 바로 확인)</b>")
        c2_title.setStyleSheet("font-size: 14px; color: #111111;")
        c2_title_box.addWidget(badge2)
        c2_title_box.addWidget(c2_title)
        c2_title_box.addStretch()
        c2_layout.addLayout(c2_title_box)

        c2_desc = QLabel(
            "① 네트워크 탭 검색창 바로 아래에 있는 필터 버튼 중 <b>[Fetch/XHR]</b>을 누릅니다.<br>"
            "② 목록에 뜨는 <b>browse</b>, <b>next</b>, <b>player</b> 중 아무거나 하나를 클릭합니다. (API 통신이라 캐시가 적용되지 않습니다)<br>"
            "③ 오른쪽의 <b>[요청 헤더 (Request Headers)]</b> 목록에서 <b>Cookie:</b>를 찾아 우클릭 후 <b>[값 복사 (Copy value)]</b>를 선택합니다."
        )
        c2_desc.setStyleSheet("font-size: 12px; color: #222222; line-height: 1.5; margin-top: 6px;")
        c2_desc.setWordWrap(True)
        c2_layout.addWidget(c2_desc)
        content_layout.addWidget(card2)

        # [완료 안내 박스]
        finish_frame = QFrame()
        finish_frame.setStyleSheet("""
            QFrame {
                background-color: #EFFDF5;
                border: 1px solid #A7F3D0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        finish_layout = QVBoxLayout(finish_frame)
        finish_lbl = QLabel(
            "✅ <b>복사 완료 후 적용하기:</b><br>"
            "복사하신 후에는 프로그램의 <b>[📋 쿠키 직접 붙여넣기 (F12)]</b> 버튼을 누르고 붙여넣어 주시면 "
            "즉시 프리미엄 256kbps 무손실 추출이 적용됩니다!"
        )
        finish_lbl.setStyleSheet("font-size: 12px; color: #065F46; line-height: 1.4;")
        finish_lbl.setWordWrap(True)
        finish_layout.addWidget(finish_lbl)
        content_layout.addWidget(finish_frame)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area, 1)

        # 3. 하단 액션 버튼 바
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        self.btn_open_browser = QPushButton("🌐 YouTube Music 웹 열기")
        self.btn_open_browser.setStyleSheet("""
            QPushButton {
                background-color: #F0F0F0;
                color: #111111;
                border: 1px solid #D0D0D0;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E4E4E4;
            }
        """)
        self.btn_open_browser.clicked.connect(self._handle_open_browser)

        self.btn_open_paste = QPushButton("📋 쿠키 직접 붙여넣기 창 열기")
        self.btn_open_paste.setStyleSheet("""
            QPushButton {
                background-color: #E62117;
                color: #FFFFFF;
                border: none;
                padding: 8px 18px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF334B;
            }
        """)
        self.btn_open_paste.clicked.connect(self._handle_open_paste)

        self.btn_close = QPushButton("닫기")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: #E8E8E8;
                color: #333333;
                border: 1px solid #D0D0D0;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #D8D8D8;
            }
        """)
        self.btn_close.clicked.connect(self.accept)

        btn_box.addWidget(self.btn_open_browser)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_open_paste)
        btn_box.addWidget(self.btn_close)

        layout.addLayout(btn_box)

    def _handle_open_browser(self):
        QDesktopServices.openUrl(QUrl("https://music.youtube.com"))

    def _handle_open_paste(self):
        self.accept()
        parent = self.parent()
        if parent and hasattr(parent, "_handle_open_cookie_paste_dialog"):
            parent._handle_open_cookie_paste_dialog()
