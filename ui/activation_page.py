import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services import license_service
from translation_manager import TranslationManager

ACCENT = "#2B79FF"
BG_PAGE = "#F0F2F5"
BG_CARD = "#FFFFFF"
TEXT_MAIN = "#111111"
TEXT_MUTED = "#888888"
BORDER = "#E4EAFF"
DANGER = "#E53935"

STYLESHEET = f"""
QWidget {{
    background: {BG_PAGE};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI';
}}
QFrame#activationCard {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 18px;
}}
QLabel {{
    background: transparent;
}}
QLineEdit {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 14px;
    color: {TEXT_MAIN};
    min-width: 300px;
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QPushButton#activateBtn {{
    background: {ACCENT};
    border: none;
    border-radius: 8px;
    padding: 10px 0;
    font-size: 14px;
    font-weight: 600;
    color: #FFFFFF;
    min-width: 300px;
}}
QPushButton#activateBtn:hover {{
    background: #1A65E0;
}}
QPushButton#activateBtn:pressed {{
    background: #1255C0;
}}
QPushButton#toggleBtn {{
    background: transparent;
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    color: {ACCENT};
    padding: 6px 10px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton#toggleBtn:hover {{
    background: #F5F8FF;
}}
"""


class ActivationPage(QWidget):
    def __init__(self, parent, on_activate):
        super().__init__(parent)
        self._on_activate = on_activate
        self._translator = TranslationManager.instance()
        self._status_key = None
        self._translator.language_changed.connect(self._apply_language)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self._apply_language()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("activationCard")
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 45))
        card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        logo_label = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "scanova-removebg-preview.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(88, 88, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("SCANOVA")
            logo_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        logo_label.setStyleSheet("border-radius: 10px;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        self._app_name_label = QLabel(self._translator.t("app.title"))
        self._app_name_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._app_name_label.setStyleSheet(f"color: {TEXT_MAIN};")
        self._app_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._app_name_label)

        self._title_label = QLabel()
        self._title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title_label)

        self._description_label = QLabel()
        self._description_label.setWordWrap(True)
        self._description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._description_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        layout.addWidget(self._description_label)
        layout.addSpacing(8)

        self._code_label = QLabel()
        self._code_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self._code_label)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._code_input = QLineEdit()
        self._code_input.setPlaceholderText("")
        self._code_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_row.addWidget(self._code_input, 1)

        self._toggle_visibility_btn = QPushButton()
        self._toggle_visibility_btn.setObjectName("toggleBtn")
        self._toggle_visibility_btn.setFixedWidth(72)
        self._toggle_visibility_btn.clicked.connect(self._toggle_visibility)
        input_row.addWidget(self._toggle_visibility_btn)

        layout.addLayout(input_row)

        self._activate_btn = QPushButton()
        self._activate_btn.setObjectName("activateBtn")
        self._activate_btn.clicked.connect(self._submit)
        self._activate_btn.setDefault(True)
        layout.addWidget(self._activate_btn)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {DANGER}; font-size: 12px;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        outer.addWidget(card)

    def _apply_language(self):
        self.setLayoutDirection(self._translator.qt_layout_direction)
        self._app_name_label.setText(self._translator.t("app.title"))
        self._title_label.setText(self._translator.t("activation.title"))
        self._description_label.setText(self._translator.t("activation.description"))
        self._code_label.setText(self._translator.t("activation.code_label"))
        self._code_input.setPlaceholderText(self._translator.t("activation.code_placeholder"))
        self._refresh_visibility_toggle()
        self._activate_btn.setText(self._translator.t("activation.activate"))
        if self._status_key:
            self._status_label.setText(self._translator.t(self._status_key))
        else:
            self._status_label.setText("")

    def _refresh_visibility_toggle(self):
        if self._code_input.echoMode() == QLineEdit.EchoMode.Password:
            self._toggle_visibility_btn.setText(self._translator.t("activation.show"))
        else:
            self._toggle_visibility_btn.setText(self._translator.t("activation.hide"))

    def _toggle_visibility(self):
        if self._code_input.echoMode() == QLineEdit.EchoMode.Password:
            self._code_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self._code_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._refresh_visibility_toggle()

    def _set_status(self, key: str | None):
        self._status_key = key
        if key is None:
            self._status_label.setText("")
            return
        self._status_label.setText(self._translator.t(key))

    def _submit(self):
        code = self._code_input.text().strip()
        ok, _ = license_service.activate(code)
        if ok:
            self._on_activate()
        else:
            self._set_status("activation.invalid")
