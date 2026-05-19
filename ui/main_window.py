import logging
import os
import platform
import subprocess

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QDialog,
    QLineEdit, QMessageBox, QSizePolicy
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

from services import auth_service
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
    color: {TEXT_MUTED}; text-align: left;
    padding: 12px 20px; font-size: 13px;
}}
QPushButton#navBtn:hover {{
    background: rgba(255,255,255,0.07); color: {TEXT_LIGHT};
}}
QPushButton#navBtnActive {{
    background: {ACCENT}; border: none; color: white;
    text-align: left; padding: 12px 20px;
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
        self.setWindowTitle("Change Password")
        self.setFixedSize(340, 220)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        for label_text, attr in [("Old Password", "_old_input"), ("New Password", "_new_input")]:
            lbl = QLabel(label_text)
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

        btn = QPushButton("Change Password")
        btn.setStyleSheet(f"background: {ACCENT}; color: white; border: none; border-radius: 7px; padding: 8px; font-weight: 600;")
        btn.clicked.connect(self._submit)
        layout.addWidget(btn)

    def _submit(self):
        ok, msg = auth_service.change_password(self._username, self._old_input.text(), self._new_input.text())
        if ok:
            QMessageBox.information(self, "Success", msg)
            self.accept()
        else:
            self._status_lbl.setText(msg)


# ── Main Window ───────────────────────────────────────────────────────────────

class MainWindow(QWidget):
    """Main application shell: header, sidebar, content area, status bar."""

    _NAV_PAGES = ("Dashboard", "Attendance", "Manual Entry", "Employees", "Monthly Report", "Advances", "Employee Reports", "Primes")

    def __init__(self, parent, username: str, on_logout=None):
        super().__init__(parent)
        self._username = username
        self._on_logout = on_logout
        self._current_page_name: str = ""
        self._pages: dict[str, QWidget] = {}
        self._nav_buttons: dict[str, QPushButton] = {}

        self.setStyleSheet(STYLESHEET)
        self._build_shell()
        self._init_nfc_reader()
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
        title_layout.addWidget(app_title)
        title_widget = QWidget()
        title_widget.setLayout(title_layout)

        h_layout.addWidget(title_widget)
        h_layout.addStretch()

        admin_lbl = QLabel(f"Admin: {self._username}")
        admin_lbl.setObjectName("adminLabel")
        h_layout.addWidget(admin_lbl)

        for text, slot in [("Change Password", self._change_password), ("Logout", self._logout)]:
            btn = QPushButton(text)
            btn.setObjectName("headerBtn")
            btn.clicked.connect(slot)
            h_layout.addWidget(btn)

        root.addWidget(header)

        # Middle
        middle = QHBoxLayout()
        middle.setContentsMargins(0, 0, 0, 0)
        middle.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(0, 16, 0, 0)
        s_layout.setSpacing(2)

        for name in self._NAV_PAGES:
            btn = QPushButton(f"  {name}")
            btn.setObjectName("navBtn")
            btn.clicked.connect(lambda checked, n=name: self._show_page(n))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            s_layout.addWidget(btn)
            self._nav_buttons[name] = btn

        s_layout.addStretch()
        middle.addWidget(sidebar)

        self._stack = QStackedWidget()
        self._stack.setObjectName("content")
        middle.addWidget(self._stack, stretch=1)
        root.addLayout(middle, stretch=1)

        # Status bar
        status_bar = QFrame()
        status_bar.setObjectName("statusBar")
        status_bar.setFixedHeight(32)
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(12, 0, 12, 0)
        sb_layout.setSpacing(24)

        self._nfc_status_lbl  = self._status_label("Waiting for NFC Reader...")
        self._scan_status_lbl = self._status_label("Scan Status: Idle")
        self._last_uid_lbl    = self._status_label("Last UID: —")
        self._last_name_lbl   = self._status_label("Employee: —")
        self._last_action_lbl = self._status_label("")

        for lbl in (self._nfc_status_lbl, self._scan_status_lbl,
                    self._last_uid_lbl, self._last_name_lbl, self._last_action_lbl):
            sb_layout.addWidget(lbl)

        sb_layout.addStretch()
        root.addWidget(status_bar)

    def _status_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("statusLabel")
        return lbl

    # ── NFC ───────────────────────────────────────────────────────────

    def _init_nfc_reader(self):
        # Bridge lives in main thread — signal is thread-safe
        self._nfc_bridge = NFCBridge()
        self._nfc_bridge.scan_done.connect(self._update_after_scan)
        self._nfc_reader = NFCReader(on_scan_callback=self._nfc_bridge.on_scan)
        self._nfc_reader.start()

    def _update_after_scan(self, result: dict):
        uid      = result.get("uid", "")
        employee = result.get("employee", "Unknown")
        action   = result.get("action", "")

        self._last_uid_lbl.setText(f"Last UID: {uid}")

        if result["success"]:
            self._scan_status_lbl.setText("Scan Status: ✅ Success")
            self._scan_status_lbl.setObjectName("statusGreen")
            self._last_name_lbl.setText(f"Employee: {employee}")
            if action == "entry":
                late_tag = " [LATE]" if result.get("late") else ""
                self._last_action_lbl.setText(f"ENTRY at {result['time']}{late_tag}")
            elif action == "exit":
                self._last_action_lbl.setText(
                    f"EXIT at {result['time']} | {result['worked_hours']}h | ${result['salary']:.2f}"
                )
            self._last_action_lbl.setObjectName("statusGreen")
            self._play_sound()
        else:
            self._scan_status_lbl.setText("Scan Status: ⚠ Issue")
            self._scan_status_lbl.setObjectName("statusYellow")
            self._last_name_lbl.setText("Employee: —")
            self._last_action_lbl.setText(result.get("message", ""))
            self._last_action_lbl.setObjectName("statusRed")
            if action == "unknown":
                # If user is on the Employees page, populate the UID input
                # so they can register the card without an interrupting popup.
                if self._current_page_name == "Employees" and "Employees" in self._pages:
                    try:
                        page = self._pages["Employees"]
                        if hasattr(page, "_inputs") and "uid" in page._inputs:
                            page._inputs["uid"].setText(uid)
                            page._inputs["uid"].setFocus()
                    except Exception:
                        QMessageBox.warning(self, "Unknown Card", result["message"])
                else:
                    QMessageBox.warning(self, "Unknown Card", result["message"])

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
            self._nfc_status_lbl.setText("NFC Reader Connected ✅")
            self._nfc_status_lbl.setObjectName("statusGreen")
        else:
            self._nfc_status_lbl.setText("Waiting for NFC Reader...")
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
            self, "Logout", "Are you sure you want to logout?",
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