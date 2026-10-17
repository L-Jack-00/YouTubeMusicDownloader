# -*- coding: utf-8 -*-
"""
Modern Dark Theme QSS Stylesheet and Theme Definitions.
"""

DARK_THEME_QSS = """
/* Global Window & Typography */
QMainWindow, QWidget#centralWidget {
    background-color: #121212;
    color: #FFFFFF;
    font-family: "Pretendard", "Segoe UI", "Malgun Gothic", sans-serif;
    font-size: 13px;
}

/* Group Boxes / Cards */
QGroupBox {
    background-color: #1E1E1E;
    border: 1px solid #2C2C2C;
    border-radius: 8px;
    margin-top: 14px;
    padding: 14px;
    font-weight: bold;
    color: #EEEEEE;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #1E1E1E;
    color: #FF4444;
}

/* Labels */
QLabel {
    color: #DDDDDD;
}

QLabel#titleLabel {
    font-size: 18px;
    font-weight: bold;
    color: #FFFFFF;
}

QLabel#statusLabel {
    font-size: 12px;
    color: #AAAAAA;
}

/* Line Edit / Input Boxes */
QLineEdit {
    background-color: #282828;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    padding: 5px 10px;
    color: #FFFFFF;
    selection-background-color: #FF0033;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #FF0033;
    background-color: #303030;
}

/* Push Buttons */
QPushButton {
    background-color: #2E2E2E;
    border: 1px solid #3E3E3E;
    border-radius: 6px;
    padding: 6px 14px;
    color: #FFFFFF;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3A3A3A;
    border: 1px solid #555555;
}

QPushButton:pressed {
    background-color: #242424;
}

QPushButton:disabled {
    background-color: #1C1C1C;
    color: #666666;
    border: 1px solid #262626;
}

/* Primary Action Button (YouTube Red) */
QPushButton#primaryButton {
    background-color: #E62117;
    border: none;
    color: #FFFFFF;
    font-weight: bold;
    font-size: 14px;
    padding: 11px 24px;
    border-radius: 6px;
}

QPushButton#primaryButton:hover {
    background-color: #FF334B;
}

QPushButton#primaryButton:pressed {
    background-color: #CC181E;
}

QPushButton#primaryButton:disabled {
    background-color: #4A2222;
    color: #888888;
}

/* Secondary Cancel Button */
QPushButton#cancelButton {
    background-color: #333333;
    border: 1px solid #444444;
    color: #FF7777;
    padding: 11px 20px;
}

QPushButton#cancelButton:hover {
    background-color: #442222;
    border-color: #FF5555;
}

/* Combo Box */
QComboBox {
    background-color: #282828;
    border: 1px solid #3A3A3A;
    border-radius: 6px;
    padding: 5px 10px;
    color: #FFFFFF;
    font-size: 13px;
}

QComboBox:hover {
    border: 1px solid #555555;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #242424;
    border: 1px solid #3C3C3C;
    selection-background-color: #E62117;
    selection-color: #FFFFFF;
    color: #EEEEEE;
    padding: 6px;
}

QComboBox QAbstractItemView::item {
    min-height: 28px;
    padding: 4px 8px;
}

/* Check Box & Radio Button */
QCheckBox, QRadioButton {
    color: #CCCCCC;
    spacing: 8px;
}

QCheckBox:hover, QRadioButton:hover {
    color: #FFFFFF;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
    background-color: #282828;
    border: 1px solid #444444;
    border-radius: 3px;
}

QRadioButton::indicator {
    border-radius: 8px;
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked {
    background-color: #E62117;
    border: 1px solid #FF334B;
}

/* Progress Bar */
QProgressBar {
    background-color: #222222;
    border: 1px solid #333333;
    border-radius: 6px;
    text-align: center;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: bold;
    height: 20px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #E62117, stop:1 #FF4E50);
    border-radius: 5px;
}

/* Text Edit / Log Area */
QTextEdit, QPlainTextEdit {
    background-color: #181818;
    border: 1px solid #2B2B2B;
    border-radius: 6px;
    padding: 8px;
    color: #B0B0B0;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 12px;
}

/* Scroll Bar */
QScrollBar:vertical {
    background: #181818;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #383838;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #505050;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Dialogs & Message Box Popups (High Contrast Black Font) */
QDialog, QMessageBox {
    background-color: #FFFFFF;
    color: #111111;
}

QDialog QLabel, QMessageBox QLabel {
    color: #111111;
    font-size: 13px;
}

QMessageBox QLabel#qt_msgbox_label,
QMessageBox QLabel#qt_msgbox_informativelabel {
    color: #111111;
    font-size: 13px;
}

QDialog QPushButton, QMessageBox QPushButton {
    background-color: #ECECEC;
    border: 1px solid #CCCCCC;
    border-radius: 5px;
    padding: 6px 16px;
    color: #111111;
    font-weight: 500;
    min-width: 70px;
}

QDialog QPushButton:hover, QMessageBox QPushButton:hover {
    background-color: #DDDDDD;
    border-color: #AAAAAA;
}

QDialog QPushButton:pressed, QMessageBox QPushButton:pressed {
    background-color: #CECECE;
}

QDialog QTextEdit, QDialog QPlainTextEdit, QDialog QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 6px;
    color: #111111;
}
"""
