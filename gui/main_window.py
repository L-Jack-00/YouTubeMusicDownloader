# -*- coding: utf-8 -*-
"""
Main Application Window for YouTube Music Downloader.
"""
import os
import sys
import subprocess
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QProgressBar, QPlainTextEdit, QFileDialog, QMessageBox,
    QGroupBox, QApplication
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices

from core.types import DownloadOptions
from core.updater import get_current_ytdlp_version, update_ytdlp
from gui.styles import DARK_THEME_QSS
from gui.worker import DownloadWorker


class MainWindow(QMainWindow):
    """
    유튜브 뮤직 음원 다운로더 메인 윈도우
    """

    def __init__(self):
        super().__init__()
        self.worker: Optional[DownloadWorker] = None
        self.default_download_dir = os.path.join(os.path.expanduser("~"), "Music", "YouTubeMusic")
        os.makedirs(self.default_download_dir, exist_ok=True)

        self._init_ui()
        self._apply_styles()

    def _init_ui(self):
        self.setWindowTitle("YouTube Music 고음질 다운로더")
        self.setMinimumSize(820, 680)
        self.resize(860, 720)

        central_widget = QWidget(self)
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # 1. 상단 헤더
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_label = QLabel("YouTube Music 고음질 다운로더")
        title_label.setObjectName("titleLabel")
        subtitle_label = QLabel("단일 곡 및 재생목록 · 앨범아트 1:1 맞춤 · 알송 및 LRCLIB 가사 자동 삽입")
        subtitle_label.setObjectName("statusLabel")
        title_box.addWidget(title_label)
        title_box.addWidget(subtitle_label)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_update = QPushButton("다운로드 엔진 업데이트")
        current_ver = get_current_ytdlp_version()
        self.btn_update.setToolTip(f"현재 엔진 버전: {current_ver}\n유튜브 변경에 대응하여 최신 버전으로 갱신합니다.")
        self.btn_update.clicked.connect(self._handle_update_engine)
        header_layout.addWidget(self.btn_update)

        main_layout.addLayout(header_layout)

        # 2. 링크 입력 카드
        url_group = QGroupBox("음원 또는 재생목록 링크")
        url_layout = QHBoxLayout(url_group)
        self.edit_url = QLineEdit()
        self.edit_url.setPlaceholderText("유튜브 또는 유튜브 뮤직 링크를 입력하세요 (예: https://music.youtube.com/watch?v=...)")
        self.edit_url.setFixedHeight(36)
        self.btn_paste = QPushButton("붙여넣기")
        self.btn_paste.setFixedHeight(36)
        self.btn_paste.clicked.connect(self._handle_paste_url)
        url_layout.addWidget(self.edit_url, 1)
        url_layout.addWidget(self.btn_paste)
        main_layout.addWidget(url_group)

        # 3. 설정 카드 (저장 경로, 포맷, 쿠키)
        settings_group = QGroupBox("저장 및 음질 설정")
        settings_layout = QGridLayout(settings_group)
        settings_layout.setHorizontalSpacing(10)
        settings_layout.setVerticalSpacing(8)

        # 저장 폴더
        settings_layout.addWidget(QLabel("저장 폴더:"), 0, 0)
        self.edit_folder = QLineEdit(self.default_download_dir)
        self.edit_folder.setFixedHeight(34)
        self.btn_browse = QPushButton("폴더 선택")
        self.btn_browse.setFixedHeight(34)
        self.btn_browse.clicked.connect(self._handle_browse_folder)
        self.btn_open_folder = QPushButton("폴더 열기")
        self.btn_open_folder.setFixedHeight(34)
        self.btn_open_folder.clicked.connect(self._handle_open_folder)

        folder_box = QHBoxLayout()
        folder_box.setSpacing(6)
        folder_box.addWidget(self.edit_folder, 1)
        folder_box.addWidget(self.btn_browse)
        folder_box.addWidget(self.btn_open_folder)
        settings_layout.addLayout(folder_box, 0, 1)

        # 파일 이름 형식 (기본값: 아티스트 - 곡명)
        settings_layout.addWidget(QLabel("파일 이름:"), 1, 0)
        self.combo_naming = QComboBox()
        self.combo_naming.setFixedHeight(34)
        self.combo_naming.addItem("아티스트 - 곡명 (기본값)", "artist_title")
        self.combo_naming.addItem("곡명 - 아티스트", "title_artist")
        self.combo_naming.addItem("곡명 단독", "title_only")
        self.combo_naming.addItem("순번. 아티스트 - 곡명 (01. 아티스트 - 곡명)", "num_artist_title")
        self.combo_naming.addItem("순번. 곡명 (01. 곡명)", "num_title")
        settings_layout.addWidget(self.combo_naming, 1, 1)

        # 음원 포맷
        settings_layout.addWidget(QLabel("음원 포맷:"), 2, 0)
        self.combo_format = QComboBox()
        self.combo_format.setFixedHeight(34)
        self.combo_format.addItem("무손실 M4A (AAC 원본 다이렉트 복사, 최고 음질/초고속)", "m4a")
        self.combo_format.addItem("고음질 MP3 (320kbps 변환, 높은 호환성)", "mp3")
        settings_layout.addWidget(self.combo_format, 2, 1)

        # 쿠키 연동 (프리미엄 256k 지원)
        settings_layout.addWidget(QLabel("쿠키 연동:"), 3, 0)
        cookie_box = QHBoxLayout()
        cookie_box.setSpacing(6)
        self.combo_cookie = QComboBox()
        self.combo_cookie.setFixedHeight(34)
        self.combo_cookie.addItem("로그인 없음 (기본 128~160kbps)", "none")
        self.combo_cookie.addItem("Chrome 브라우저 로그인 연동 (구버전/외부)", "chrome")
        self.combo_cookie.addItem("Edge 브라우저 로그인 연동 (구버전/외부)", "edge")
        self.combo_cookie.addItem("Firefox 브라우저 로그인 연동 (프리미엄 256kbps)", "firefox")
        self.combo_cookie.addItem("cookies.txt 파일 직접 선택", "file")

        self.btn_paste_cookie = QPushButton("📋 쿠키 직접 붙여넣기 (F12)")
        self.btn_paste_cookie.setFixedHeight(34)
        self.btn_paste_cookie.setToolTip("확장 프로그램 없이, 브라우저 F12에서 복사한 쿠키를 붙여넣어 즉시 적용합니다.")
        self.btn_paste_cookie.clicked.connect(self._handle_open_cookie_paste_dialog)

        self.btn_cookie_guide = QPushButton("❓ 쿠키 추출 가이드")
        self.btn_cookie_guide.setFixedHeight(34)
        self.btn_cookie_guide.setToolTip("확장 프로그램 없이, 브라우저 F12를 통해 10초 만에 쿠키를 추출하는 가이드를 엽니다.")
        self.btn_cookie_guide.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        self.btn_cookie_guide.clicked.connect(self._handle_open_cookie_guide)

        self.edit_cookie_file = QLineEdit()
        self.edit_cookie_file.setFixedHeight(34)
        self.edit_cookie_file.setPlaceholderText("cookies.txt 파일 경로")
        self.edit_cookie_file.setVisible(False)
        self.btn_browse_cookie = QPushButton("파일 찾기")
        self.btn_browse_cookie.setFixedHeight(34)
        self.btn_browse_cookie.setVisible(False)
        self.btn_browse_cookie.clicked.connect(self._handle_browse_cookie_file)

        cookie_box.addWidget(self.combo_cookie, 1)
        cookie_box.addWidget(self.btn_paste_cookie)
        cookie_box.addWidget(self.btn_cookie_guide)
        cookie_box.addWidget(self.edit_cookie_file, 1)
        cookie_box.addWidget(self.btn_browse_cookie)
        settings_layout.addLayout(cookie_box, 3, 1)

        # 기존 자동 저장된 쿠키가 있는지 확인
        from core.cookie_util import get_app_root_dir
        session_cookie_file = os.path.join(get_app_root_dir(), "session_cookies.txt")
        if os.path.isfile(session_cookie_file):
            self.combo_cookie.insertItem(1, "✓ 자동 추출된 로그인 쿠키 사용 (프리미엄 256k)", "session")
            self.combo_cookie.setCurrentIndex(1)

        main_layout.addWidget(settings_group)

        # 4. 부가 옵션 카드 (가사 및 앨범아트)
        option_group = QGroupBox("메타데이터 및 가사 옵션")
        option_layout = QHBoxLayout(option_group)
        self.chk_lyrics = QCheckBox("음원 태그 및 가사(알송/LRCLIB) 자동 삽입")
        self.chk_lyrics.setChecked(True)
        self.chk_lrc_file = QCheckBox("싱크 가사(.lrc) 별도 파일 함께 저장")
        self.chk_lrc_file.setChecked(False)
        self.chk_square_cover = QCheckBox("앨범 커버 1:1 정방형 자동 맞춤")
        self.chk_square_cover.setChecked(True)

        option_layout.addWidget(self.chk_lyrics)
        option_layout.addWidget(self.chk_lrc_file)
        option_layout.addWidget(self.chk_square_cover)
        main_layout.addWidget(option_group)

        # 5. 진행 상태 및 액션 버튼
        action_layout = QHBoxLayout()
        self.btn_start = QPushButton("다운로드 시작")
        self.btn_start.setObjectName("primaryButton")
        self.btn_start.clicked.connect(self._handle_start_download)

        self.btn_cancel = QPushButton("작업 취소")
        self.btn_cancel.setObjectName("cancelButton")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self._handle_cancel_download)

        action_layout.addWidget(self.btn_start, 2)
        action_layout.addWidget(self.btn_cancel, 1)
        main_layout.addLayout(action_layout)

        # 프로그레스바 및 상태 라벨
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        status_box = QHBoxLayout()
        self.label_status = QLabel("준비 완료 - 다운로드할 링크를 입력해 주세요.")
        self.label_status.setObjectName("statusLabel")
        self.btn_clear_log = QPushButton("로그 지우기")
        self.btn_clear_log.clicked.connect(self._handle_clear_log)
        status_box.addWidget(self.label_status, 1)
        status_box.addWidget(self.btn_clear_log)
        main_layout.addLayout(status_box)

        # 6. 실시간 작업 로그 창
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        main_layout.addWidget(self.log_view, 1)

        # 모든 위젯 생성 완료 후 시그널 연결
        self.combo_cookie.currentIndexChanged.connect(self._handle_cookie_mode_changed)

    def _apply_styles(self):
        self.setStyleSheet(DARK_THEME_QSS)

    def _handle_paste_url(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self.edit_url.setText(text)

    def _handle_browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "저장 폴더 선택", self.edit_folder.text())
        if folder:
            self.edit_folder.setText(os.path.normpath(folder))

    def _handle_open_folder(self):
        folder = self.edit_folder.text().strip()
        if os.path.isdir(folder):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
        else:
            QMessageBox.information(self, "안내", "지정된 저장 폴더가 아직 존재하지 않습니다.")

    def _handle_cookie_mode_changed(self, index: int):
        if not hasattr(self, 'edit_cookie_file') or not hasattr(self, 'label_status'):
            return
        data = self.combo_cookie.currentData()
        is_file = (data == "file")
        self.edit_cookie_file.setVisible(is_file)
        self.btn_browse_cookie.setVisible(is_file)
        if data in ("chrome", "edge"):
            self.label_status.setText("💡 최신 크롬/엣지는 윈도우 보안 암호화로 인해 'cookies.txt 파일 직접 선택' 방식을 권장합니다.")
        elif data == "session":
            self.label_status.setText("준비 완료 - 프로그램 내장 로그인으로 자동 추출된 쿠키(프리미엄 256k)를 사용합니다.")
        elif data == "none":
            self.label_status.setText("준비 완료 - 로그인 없이 기본 128~160kbps 음질로 저장됩니다.")
        elif data == "file":
            self.label_status.setText("준비 완료 - 브라우저 확장으로 추출한 cookies.txt 파일을 선택해 주세요.")

    def _handle_open_cookie_paste_dialog(self):
        try:
            from gui.cookie_paste_dialog import CookiePasteDialog
            dialog = CookiePasteDialog(self)
            if dialog.exec():
                has_session = False
                for i in range(self.combo_cookie.count()):
                    if self.combo_cookie.itemData(i) == "session":
                        has_session = True
                        self.combo_cookie.setCurrentIndex(i)
                        break
                if not has_session:
                    self.combo_cookie.insertItem(1, "✓ 자동 추출된 로그인 쿠키 사용 (프리미엄 256k)", "session")
                    self.combo_cookie.setCurrentIndex(1)
                self.label_status.setText("✓ 쿠키가 성공적으로 등록되었습니다! (프리미엄 256kbps 적용)")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"대화상자 실행 중 오류: {str(e)}")

    def _handle_open_cookie_guide(self):
        try:
            from gui.cookie_guide_dialog import CookieGuideDialog
            dialog = CookieGuideDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"쿠키 가이드 창을 여는 중 문제가 발생했습니다: {str(e)}")

    def _handle_browse_cookie_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "쿠키 파일 선택", "", "쿠키 텍스트 파일 (*.txt);;모든 파일 (*.*)"
        )
        if file_path:
            self.edit_cookie_file.setText(os.path.normpath(file_path))

    def _handle_update_engine(self):
        self.label_status.setText("다운로드 엔진 최신 버전 확인 중...")
        self.btn_update.setEnabled(False)
        QApplication.processEvents()

        success, msg = update_ytdlp()
        self.btn_update.setEnabled(True)
        if success:
            QMessageBox.information(self, "업데이트 완료", msg)
            current_ver = get_current_ytdlp_version()
            self.btn_update.setToolTip(f"현재 엔진 버전: {current_ver}")
            self.label_status.setText(f"엔진 최신 상태 (버전: {current_ver})")
        else:
            QMessageBox.warning(self, "업데이트 안내", msg)
            self.label_status.setText("엔진 업데이트 확인 완료")

    def _handle_clear_log(self):
        self.log_view.clear()

    def _handle_start_download(self):
        url = self.edit_url.text().strip()
        if not url:
            QMessageBox.warning(self, "입력 확인", "다운로드할 유튜브 또는 유튜브 뮤직 링크를 입력해 주세요.")
            return

        out_dir = self.edit_folder.text().strip()
        if not out_dir:
            out_dir = self.default_download_dir
            self.edit_folder.setText(out_dir)

        # 옵션 객체 생성
        format_val = self.combo_format.currentData()
        cookie_choice = self.combo_cookie.currentData()

        cookie_mode = "none"
        browser_name = "chrome"
        cookie_file = None

        if cookie_choice == "session":
            from core.cookie_util import get_app_root_dir
            session_file = os.path.join(get_app_root_dir(), "session_cookies.txt")
            if os.path.isfile(session_file):
                cookie_mode = "file"
                cookie_file = session_file
            else:
                QMessageBox.warning(
                    self,
                    "쿠키 파일 확인",
                    "저장된 내장 로그인 쿠키를 찾을 수 없습니다. 상단의 [📋 쿠키 직접 붙여넣기 (F12)] 버튼을 눌러 먼저 쿠키를 등록해 주세요."
                )
                return
        elif cookie_choice in ("chrome", "edge", "firefox"):
            cookie_mode = "browser"
            browser_name = cookie_choice
            from core.cookie_util import is_browser_cookie_locked
            is_locked, _ = is_browser_cookie_locked(browser_name)
            if is_locked:
                b_name_upper = browser_name.upper()
                reply = QMessageBox.question(
                    self,
                    "브라우저 쿠키 파일 잠김 안내",
                    f"선택하신 브라우저({b_name_upper})가 현재 실행 중(또는 백그라운드 상주)이어서 쿠키 파일이 잠겨 있습니다.\n"
                    f"({b_name_upper}는 Chromium 엔진 기반으로, 실행 중일 때 외부 프로그램의 쿠키 접근이 제한됩니다)\n\n"
                    f"쿠키 없이(기본 128~160kbps 음질로) 다운로드를 계속 진행하시겠습니까?\n\n"
                    f"• [Yes / 예]: 쿠키 없이 즉시 다운로드 진행\n"
                    f"• [No / 아니오]: 취소 ({b_name_upper} 완전 종료 후 다시 시도하거나 cookies.txt 사용)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    cookie_mode = "none"
                else:
                    return
        elif cookie_choice == "file":
            cookie_mode = "file"
            cookie_file = self.edit_cookie_file.text().strip()
            if not cookie_file or not os.path.isfile(cookie_file):
                QMessageBox.warning(self, "파일 확인", "유효한 cookies.txt 파일 경로를 선택해 주세요.")
                return

        options = DownloadOptions(
            output_dir=out_dir,
            audio_format=format_val,
            naming_format=self.combo_naming.currentData(),
            embed_lyrics=self.chk_lyrics.isChecked(),
            save_lrc_file=self.chk_lrc_file.isChecked(),
            crop_square_cover=self.chk_square_cover.isChecked(),
            cookie_mode=cookie_mode,
            browser_name=browser_name,
            cookie_file_path=cookie_file
        )

        # UI 잠금 및 상태 전환
        self._set_ui_busy(True)
        self.progress_bar.setValue(0)
        self.label_status.setText("작업을 준비하는 중입니다...")

        # 워커 시작
        self.worker = DownloadWorker(url=url, options=options)
        self.worker.progress_changed.connect(self._on_worker_progress)
        self.worker.log_emitted.connect(self._on_worker_log)
        self.worker.batch_finished.connect(self._on_worker_finished)
        self.worker.work_cancelled.connect(self._on_worker_cancelled)
        self.worker.error_occurred.connect(self._on_worker_error)
        self.worker.start()

    def _handle_cancel_download(self):
        if self.worker and self.worker.isRunning():
            self.label_status.setText("작업 중지를 요청했습니다...")
            self.btn_cancel.setEnabled(False)
            self.worker.stop()

    def _set_ui_busy(self, is_busy: bool):
        self.btn_start.setEnabled(not is_busy)
        self.btn_cancel.setEnabled(is_busy)
        self.edit_url.setEnabled(not is_busy)
        self.btn_paste.setEnabled(not is_busy)
        self.combo_naming.setEnabled(not is_busy)
        self.combo_format.setEnabled(not is_busy)
        self.combo_cookie.setEnabled(not is_busy)
        self.btn_browse.setEnabled(not is_busy)

    def _on_worker_progress(self, state_text: str, percentage: float, message: str):
        self.progress_bar.setValue(int(percentage))
        self.label_status.setText(f"[{state_text}] {message}")

    def _on_worker_log(self, log_text: str):
        self.log_view.appendPlainText(log_text)

    def _on_worker_finished(self, succeeded: int, total: int):
        self._set_ui_busy(False)
        self.progress_bar.setValue(100)
        self.label_status.setText(f"다운로드 완료 ({succeeded}/{total}곡 저장됨)")
        QMessageBox.information(
            self,
            "다운로드 완료",
            f"선택하신 음원 저장이 완료되었습니다.\n성공: {succeeded}곡 / 전체: {total}곡\n저장 위치: {self.edit_folder.text()}"
        )

    def _on_worker_cancelled(self):
        self._set_ui_busy(False)
        self.label_status.setText("작업이 취소되었습니다.")
        QMessageBox.information(self, "작업 취소", "사용자에 의해 작업이 안전하게 중단되었습니다.")

    def _on_worker_error(self, err_msg: str):
        self._set_ui_busy(False)
        self.label_status.setText("오류 발생으로 작업이 중단되었습니다.")
        QMessageBox.critical(self, "다운로드 오류", err_msg)
