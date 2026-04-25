from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services import auth_service


ACCENT     = "#2B79FF"
BG_PAGE    = "#F0F2F5"
BG_CARD    = "#FFFFFF"
TEXT_MAIN  = "#111111"
TEXT_MUTED = "#888888"
BORDER     = "#E4EAFF"
DANGER     = "#E53935"


STYLESHEET = f"""
QWidget {{
    background: {BG_PAGE};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI';
}}
QFrame#loginCard {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 16px;
}}
QLabel {{
    background: transparent;
}}
QLineEdit {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    color: {TEXT_MAIN};
    min-width: 280px;
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QPushButton#submitBtn {{
    background: {ACCENT};
    border: none;
    border-radius: 8px;
    padding: 10px 0;
    font-size: 14px;
    font-weight: 600;
    color: #FFFFFF;
    min-width: 280px;
}}
QPushButton#submitBtn:hover {{
    background: #1A65E0;
}}
QPushButton#submitBtn:pressed {{
    background: #1255C0;
}}
"""


class LoginPage(QWidget):
    """Login / Registration page shown before the main app."""

    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self._on_login_success = on_login_success
        self._is_register = auth_service.is_first_launch()
        self.setStyleSheet(STYLESHEET)
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Center the card
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # App title
        app_title = QLabel("SCANOVA")
        app_title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        app_title.setStyleSheet(f"color: {TEXT_MAIN};")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_title)

        # Page subtitle
        subtitle_text = "Admin Registration" if self._is_register else "Login"
        subtitle = QLabel(subtitle_text)
        subtitle.setFont(QFont("Segoe UI", 14))
        subtitle.setStyleSheet(f"color: {TEXT_MUTED};")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # Username
        lbl_user = QLabel("Username")
        lbl_user.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(lbl_user)

        self._username_input = QLineEdit()
        self._username_input.setPlaceholderText("Enter username")
        layout.addWidget(self._username_input)

        # Password
        lbl_pass = QLabel("Password")
        lbl_pass.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(lbl_pass)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Enter password")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self._password_input)

        # Confirm password (register only)
        self._confirm_input = None
        if self._is_register:
            lbl_confirm = QLabel("Confirm Password")
            lbl_confirm.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            layout.addWidget(lbl_confirm)

            self._confirm_input = QLineEdit()
            self._confirm_input.setPlaceholderText("Repeat password")
            self._confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(self._confirm_input)

        layout.addSpacing(6)

        # Submit button
        btn_text = "Register" if self._is_register else "Login"
        btn = QPushButton(btn_text)
        btn.setObjectName("submitBtn")
        btn.clicked.connect(self._submit)
        # Allow Enter key to submit
        btn.setDefault(True)
        layout.addWidget(btn)

        # Status label (errors)
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {DANGER}; font-size: 12px;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        outer.addWidget(card)

    # ── Actions ───────────────────────────────────────────────────────

    def _submit(self):
        username = self._username_input.text().strip()
        password = self._password_input.text().strip()

        if self._is_register:
            confirm = self._confirm_input.text().strip()
            if password != confirm:
                self._status_label.setText("Passwords do not match.")
                return
            ok, msg = auth_service.register_admin(username, password)
            if ok:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", msg)
                self._on_login_success(username)
            else:
                self._status_label.setText(msg)
        else:
            ok, msg = auth_service.login(username, password)
            if ok:
                self._on_login_success(username)
            else:
                self._status_label.setText(msg)