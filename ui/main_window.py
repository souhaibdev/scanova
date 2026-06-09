import logging
import os
import platform
import subprocess

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel,
    QPushButton, QComboBox, QFrame, QStackedWidget, QDialog,
    QLineEdit, QMessageBox, QSizePolicy
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

from services import auth_service
from translation_manager import TranslationManager
from services.attendance_service import process_scan
from services.nfc_reader import NFCReader
from ui.dashboard_page import DashboardPage
from ui.attendance_page import AttendancePage
from ui.employees_page import EmployeesPage
from ui.notes_page import NotesPage
from ui.monthly_report_page import MonthlyReportPage
from ui.employee_report_page import EmployeeReportPage
from ui.primes_page import PrimesPage     
from ui.manual_attendance_page import ManualAttendancePage                   # ← زيد

logger = logging.getLogger(__name__)


# ── Colors ────────────────────────────────────────────────────────────────────
ACCENT      = "#2B79FF"
BG_PAGE     = "#F0F2F5"
BG_CARD     = "#FFFFFF"
BG_SIDEBAR  = "#1E1E2E"
BG_HEADER   = "#2D2D4E"
BG_STATUS   = "#1A1A2E"
TEXT_MAIN   = "#111111"
TEXT_LIGHT  = "#E0E0E0"
TEXT_MUTED  = "#A0A0C0"
TEXT_ACCENT = "#7C83FF"
FG_SUCCESS  = "#4ADE80"
FG_WARNING  = "#FACC15"
FG_DANGER   = "#F87171"
BORDER      = "#E4EAFF"


STYLESHEET = f"""
QWidget {{ font-family: 'Segoe UI'; }}

QFrame#header {{ background: {BG_HEADER}; }}
QLabel#appTitle {{
    color: white; font-size: 16px; font-weight: 600; background: transparent;
}}
QLabel#adminLabel {{
    color: {TEXT_MUTED}; font-size: 11px; background: transparent;
}}
QPushButton#headerBtn {{
    background: transparent;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 6px;
    color: {TEXT_LIGHT};
    padding: 5px 12px;
    font-size: 12px;
}}
QPushButton#headerBtn:hover {{ background: rgba(255,255,255,0.1); }}

QFrame#sidebar {{ background: {BG_SIDEBAR}; min-width: 200px; max-width: 200px; }}
QPushButton#navBtn {{
    background: transparent; border: none;
    color: {TEXT_MUTED};
    padding: 12px 20px; font-size: 13px;
}}
QPushButton#navBtn:hover {{
    background: rgba(255,255,255,0.07); color: {TEXT_LIGHT};
}}
QPushButton#navBtnActive {{
    background: {ACCENT}; border: none; color: white;
    padding: 12px 20px;
    font-size: 13px; font-weight: 600;
}}

QFrame#content {{ background: {BG_PAGE}; }}

QFrame#statusBar {{ background: {BG_STATUS}; }}
QLabel#statusLabel  {{ color: {TEXT_MUTED};   font-size: 11px; background: transparent; }}
QLabel#statusGreen  {{ color: {FG_SUCCESS};   font-size: 11px; font-weight: 600; background: transparent; }}
QLabel#statusYellow {{ color: {FG_WARNING};   font-size: 11px; background: transparent; }}
QLabel#statusRed    {{ color: {FG_DANGER};    font-size: 11px; background: transparent; }}
"""


# ── NFC Signal Bridge ─────────────────────────────────────────────────────────
# Runs process_scan in the NFC thread, then emits a signal to the main thread.
# This is the ONLY safe way to update Qt UI from a background thread.

class NFCBridge(QObject):
    scan_done = pyqtSignal(dict)

    def on_scan(self, uid: str):
        result = process_scan(uid)
        self.scan_done.emit(result)   # crosses the thread boundary safely


# ── Change Password Dialog ─────────────────────────────────────────────────────

class ChangePasswordDialog(QDialog):
    def __init__(self, username: str, parent=None):
        super().__init__(parent)
        self._username = username
        self._translator = TranslationManager.instance()
        self.setWindowTitle(self._translator.t("menu.change_password"))
        self.setFixedSize(340, 220)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        for label_key, attr in [("change_password.old_password", "_old_input"), ("change_password.new_password", "_new_input")]:
            lbl = QLabel(self._translator.t(label_key))
            self._translator.bind_text(lbl, label_key)
            lbl.setStyleSheet("color: #555; font-size: 12px;")
            layout.addWidget(lbl)
            inp = QLineEdit()
            inp.setEchoMode(QLineEdit.EchoMode.Password)
            inp.setStyleSheet("border: 1.5px solid #E4EAFF; border-radius: 7px; padding: 6px 10px; font-size: 13px;")
            layout.addWidget(inp)
            setattr(self, attr, inp)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet(f"color: {FG_DANGER}; font-size: 12px;")
        layout.addWidget(self._status_lbl)

        btn = QPushButton(self._translator.t("menu.change_password"))
        self._translator.bind_text(btn, "menu.change_password")
        btn.setStyleSheet(f"background: {ACCENT}; color: white; border: none; border-radius: 7px; padding: 8px; font-weight: 600;")
        btn.clicked.connect(self._submit)
        layout.addWidget(btn)

    def _submit(self):
        ok, msg = auth_service.change_password(self._username, self._old_input.text(), self._new_input.text())
        if ok:
            QMessageBox.information(self, self._translator.t("common.success"), msg)
            self.accept()
        else:
            self._status_lbl.setText(msg)


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QWidget):
    """Main application shell: header, sidebar, content area, status bar."""

    _NAV_PAGES = [
        ("Dashboard", "nav.dashboard"),
        ("Attendance", "nav.attendance"),
        ("Manual Entry", "nav.manual_entry"),
        ("Employees", "nav.employees"),
        ("Monthly Report", "nav.monthly_report"),
        ("Advances", "nav.advances"),
        ("Employee Reports", "nav.employee_reports"),
        ("Primes", "nav.primes"),
    ]

    def __init__(self, parent, username: str, on_logout=None):
        super().__init__(parent)
        self._username = username
        self._on_logout = on_logout
        self._current_page_name: str = ""
        self._pages: dict[str, QWidget] = {}
        self._nav_buttons: dict[str, QPushButton] = {}
        self._translator = TranslationManager.instance()
        self._last_scan_result: dict | None = None

        self._translator.language_changed.connect(self.apply_language_change)

        self.setStyleSheet(STYLESHEET)
        self._build_shell()
        self._init_nfc_reader()
        self._translate_dynamic_texts()
        self._apply_language_direction(self._translator.current_language)
        self._show_page("Dashboard")
        self._start_status_timer()

    # ── Shell Layout ──────────────────────────────────────────────────

    def _build_shell(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(56)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)

        title_layout = QHBoxLayout()
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        logo = QLabel()
        image_path = os.path.join(os.path.dirname(__file__), "scanova-removebg-preview.png")
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            logger.warning("Unable to load logo image from %s", image_path)

        app_title = QLabel("SCANOVA")
        app_title.setObjectName("appTitle")
        app_title.setContentsMargins(0, 0, 0, 0)

        title_layout.addWidget(logo)

        self._app_title = QLabel(self._translator.t("app.title"))
        self._app_title.setObjectName("appTitle")
        self._translator.bind_text(self._app_title, "app.title")
        self._app_title.setContentsMargins(0, 0, 0, 0)
        title_layout.addWidget(self._app_title)

        title_widget = QWidget()
        title_widget.setLayout(title_layout)

        h_layout.addWidget(title_widget)
        h_layout.addStretch()

        self._lang_combo = QComboBox()
        self._lang_combo.setFixedWidth(140)
        self._translator.bind_combo_items(self._lang_combo, [
            ("lang.en", "en"),
            ("lang.ar", "ar"),
        ])
        self._lang_combo.currentIndexChanged.connect(self._change_language)
        h_layout.addWidget(self._lang_combo)

        self._admin_lbl = QLabel("")
        self._admin_lbl.setObjectName("adminLabel")
        h_layout.addWidget(self._admin_lbl)

        self._change_password_btn = QPushButton()
        self._change_password_btn.setObjectName("headerBtn")
        self._translator.bind_text(self._change_password_btn, "menu.change_password")
        self._change_password_btn.clicked.connect(self._change_password)
        h_layout.addWidget(self._change_password_btn)

        self._logout_btn = QPushButton()
        self._logout_btn.setObjectName("headerBtn")
        self._translator.bind_text(self._logout_btn, "menu.logout")
        self._logout_btn.clicked.connect(self._logout)
        h_layout.addWidget(self._logout_btn)

        root.addWidget(header)

        # Middle
        self._middle_layout = QHBoxLayout()
        self._middle_layout.setDirection(QBoxLayout.Direction.LeftToRight)
        self._middle_layout.setContentsMargins(0, 0, 0, 0)
        self._middle_layout.setSpacing(0)

        self._sidebar = QFrame()
        self._sidebar.setObjectName("sidebar")
        self._sidebar_layout = QVBoxLayout(self._sidebar)
        self._sidebar_layout.setContentsMargins(0, 16, 0, 0)
        self._sidebar_layout.setSpacing(2)
        self._rebuild_sidebar()
        self._middle_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._stack.setObjectName("content")
        self._middle_layout.addWidget(self._stack, stretch=1)
        root.addLayout(self._middle_layout, stretch=1)

        # Status bar
        status_bar = QFrame()
        status_bar.setObjectName("statusBar")
        status_bar.setFixedHeight(32)
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(12, 0, 12, 0)
        sb_layout.setSpacing(24)

        self._nfc_status_lbl  = self._status_label("status.nfc_waiting")
        self._scan_status_lbl = self._status_label("status.scan_issue")
        self._last_uid_lbl    = self._status_label("status.last_uid", bind=False, uid="—")
        self._last_name_lbl   = self._status_label("status.employee_none")
        self._last_action_lbl = self._status_label("")

        for lbl in (self._nfc_status_lbl, self._scan_status_lbl,
                    self._last_uid_lbl, self._last_name_lbl, self._last_action_lbl):
            sb_layout.addWidget(lbl)

        sb_layout.addStretch()
        root.addWidget(status_bar)

    def _status_label(self, key: str, bind: bool = True, **kwargs) -> QLabel:
        lbl = QLabel(self._translator.t(key, **kwargs) if key else "")
        lbl.setObjectName("statusLabel")
        if key and bind and not kwargs:
            self._translator.bind_text(lbl, key)
        return lbl

    def _translate_dynamic_texts(self):
        self.setWindowTitle(self._translator.t("app.title"))
        self._admin_lbl.setText(self._translator.t("app.admin_label", username=self._username))
        self._lang_combo.setCurrentIndex(self._lang_combo.findData(self._translator.current_language))
        self._render_scan_status(self._last_scan_result)

    def _arrange_sidebar(self):
        self._middle_layout.removeWidget(self._sidebar)
        self._middle_layout.removeWidget(self._stack)

        is_rtl = self._translator.current_language == "ar"
        
        # ← بدل direction الـ layout
        if is_rtl:
            self._middle_layout.insertWidget(0, self._stack, stretch=1)
            self._middle_layout.insertWidget(1, self._sidebar)
        else:
            self._middle_layout.insertWidget(0, self._sidebar)
            self._middle_layout.insertWidget(1, self._stack, stretch=1)

    # ← بدل alignment ديال الـ sidebar buttons
        for btn in self._nav_buttons.values():
            if is_rtl:
                btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
                btn.setStyleSheet(btn.styleSheet().replace("text-align: left", "text-align: right"))
            else:
                btn.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
                btn.setStyleSheet(btn.styleSheet().replace("text-align: right", "text-align: left"))

    def _rebuild_sidebar(self):
        if hasattr(self, "_sidebar_layout"):
            while self._sidebar_layout.count():
                item = self._sidebar_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
        self._nav_buttons.clear()

        for name, key in self._NAV_PAGES:
            btn = QPushButton()
            self._translator.bind_text(btn, key)
            btn.setObjectName("navBtn")
            btn.clicked.connect(lambda checked, n=name: self._show_page(n))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self._sidebar_layout.addWidget(btn)
            self._nav_buttons[name] = btn

        self._sidebar_layout.addStretch()
        self._sidebar.update()

    def _apply_language_direction(self, language: str):
        direction = self._translator.qt_layout_direction
        self.setLayoutDirection(direction)
        self._sidebar.setLayoutDirection(direction)
        self._stack.setLayoutDirection(direction)
        self._arrange_sidebar()
        self._translate_dynamic_texts()

    def _render_scan_status(self, result: dict | None):
        if result is None:
            self._last_uid_lbl.setText(self._translator.t("status.last_uid", uid="—"))
            self._last_name_lbl.setText(self._translator.t("status.employee_none"))
            self._last_action_lbl.setText("")
            return

        self._last_uid_lbl.setText(self._translator.t("status.last_uid", uid=result.get("uid", "")))
        if result.get("success"):
            self._scan_status_lbl.setText(self._translator.t("status.scan_success"))
            self._scan_status_lbl.setObjectName("statusGreen")
            self._last_name_lbl.setText(self._translator.t("status.employee", employee=result.get("employee", "")))
            action = result.get("action", "")
            if action == "entry":
                late_tag = " [LATE]" if result.get("late") else ""
                self._last_action_lbl.setText(self._translator.t(
                    "status.action.entry",
                    time=result.get("time", ""),
                    late_tag=late_tag,
                ))
            elif action == "exit":
                self._last_action_lbl.setText(self._translator.t(
                    "status.action.exit",
                    time=result.get("time", ""),
                    worked_hours=result.get("worked_hours", ""),
                    salary=result.get("salary", 0.0),
                ))
            self._last_action_lbl.setObjectName("statusGreen")
        else:
            self._scan_status_lbl.setText(self._translator.t("status.scan_issue"))
            self._scan_status_lbl.setObjectName("statusYellow")
            self._last_name_lbl.setText(self._translator.t("status.employee_none"))
            self._last_action_lbl.setText(result.get("message", ""))
            self._last_action_lbl.setObjectName("statusRed")

    def _change_language(self, index: int):
        language = self._lang_combo.itemData(index)
        if language:
            self._translator.set_language(language)

    def apply_language_change(self, language: str):
        self._rebuild_sidebar()
        self._translator.translate_all()
        self._apply_language_direction(language)
        self._refresh_all_pages()

    def _init_nfc_reader(self):
        # Bridge lives in main thread — signal is thread-safe
        self._nfc_bridge = NFCBridge()
        self._nfc_bridge.scan_done.connect(self._update_after_scan)
        self._nfc_reader = NFCReader(on_scan_callback=self._nfc_bridge.on_scan)
        self._nfc_reader.start()

    def _update_after_scan(self, result: dict):
        self._last_scan_result = result
        self._render_scan_status(result)
        action = result.get("action", "")

        if not result.get("success") and action == "unknown":
            # If user is on the Employees page, populate the UID input
            # so they can register the card without an interrupting popup.
            if self._current_page_name == "Employees" and "Employees" in self._pages:
                try:
                    page = self._pages["Employees"]
                    if hasattr(page, "_inputs") and "uid" in page._inputs:
                        page._inputs["uid"].setText(result.get("uid", ""))
                        page._inputs["uid"].setFocus()
                except Exception:
                    QMessageBox.warning(
                        self,
                        self._translator.t("common.error"),
                        result.get("message", ""),
                    )
            else:
                QMessageBox.warning(
                    self,
                    self._translator.t("common.error"),
                    result.get("message", ""),
                )

        for lbl in (self._scan_status_lbl, self._last_action_lbl):
            lbl.setStyle(lbl.style())

        # File I/O already done in NFC thread before signal was emitted
        QTimer.singleShot(50, self._refresh_all_pages)

    def _play_sound(self):
        try:
            if platform.system() == "Darwin":
                subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif platform.system() == "Linux":
                subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass

    # ── Status Timer ──────────────────────────────────────────────────

    def _start_status_timer(self):
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_nfc_status)
        self._status_timer.start(5000)
        self._update_nfc_status()

    def _update_nfc_status(self):
        if self._nfc_reader.is_connected_hint():
            self._nfc_status_lbl.setText(self._translator.t("status.nfc_connected"))
            self._nfc_status_lbl.setObjectName("statusGreen")
        else:
            self._nfc_status_lbl.setText(self._translator.t("status.nfc_waiting"))
            self._nfc_status_lbl.setObjectName("statusLabel")
        self._nfc_status_lbl.setStyle(self._nfc_status_lbl.style())

    # ── Navigation ────────────────────────────────────────────────────

    def _show_page(self, name: str):
        # Update sidebar highlight
        for btn_name, btn in self._nav_buttons.items():
            btn.setObjectName("navBtnActive" if btn_name == name else "navBtn")
            btn.setStyle(btn.style())

        # Create page if not yet cached
        if name not in self._pages:
            page_cls = {
                "Dashboard":        DashboardPage,
                "Attendance":       AttendancePage,
                "Manual Entry":     ManualAttendancePage,
                "Employees":        EmployeesPage,
                "Advances":         NotesPage,
                "Notes":            NotesPage,
                "Monthly Report":   MonthlyReportPage,
                "Employee Reports": EmployeeReportPage,
                "Primes":           PrimesPage,
            }[name]
            page = page_cls(self._stack)
            self._stack.addWidget(page)
            self._pages[name] = page

        # ✅ Always refresh when switching — fixes stale data after scan
        page = self._pages[name]
        if hasattr(page, "refresh"):
            page.refresh()

        self._stack.setCurrentWidget(page)
        self._current_page_name = name

    def _refresh_all_pages(self):
        """
        Called after every NFC scan.
        Refreshes ALL cached pages + forces Qt to repaint immediately,
        even if the page is hidden inside the QStackedWidget.
        """
        from PyQt6.QtWidgets import QApplication
        for page_name, page in self._pages.items():
            if hasattr(page, "refresh"):
                logger.debug("Post-scan refresh: %s", page_name)
                page.refresh()
                page.update()
                page.repaint()
        # Force Qt to flush all pending paint events right now
        QApplication.processEvents()

    # ── Auth Actions ──────────────────────────────────────────────────

    def _change_password(self):
        dlg = ChangePasswordDialog(self._username, self)
        dlg.exec()

    def _logout(self):
        reply = QMessageBox.question(
            self,
            self._translator.t("common.confirm"),
            self._translator.t("logout.confirm"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.destroy()
        if self._on_logout:
            self._on_logout()

    def destroy(self):
        if hasattr(self, "_nfc_reader"):
            self._nfc_reader.stop()
        if hasattr(self, "_status_timer"):
            self._status_timer.stop()
        super().destroy()