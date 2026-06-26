#!/usr/bin/env python3
"""
NFC Attendance & Payroll Management System
Production-ready version
"""

import sys
import os
import json

from utils.storage import (
    BASE_DIR,
    EMPLOYEES_FILE,
    ATTENDANCE_FILE,
    ADVANCES_FILE,
    PRIMES_FILE,
    NOTES_FILE,
)

# ─────────────────────────────────────────────
# DATA FILES PATHS
# ─────────────────────────────────────────────


# ─────────────────────────────────────────────
# INIT FILES
# ─────────────────────────────────────────────
def _ensure_data_files():
    import pandas as pd

    # employees.json
    if not os.path.exists(EMPLOYEES_FILE):
        with open(EMPLOYEES_FILE, "w") as f:
            json.dump({}, f)

    # attendance.xlsx
    if not os.path.exists(ATTENDANCE_FILE):
        from models.attendance_record import AttendanceRecord
        df = pd.DataFrame(columns=AttendanceRecord.columns())
        df.to_excel(ATTENDANCE_FILE, index=False)

    # excel files
    excel_files = {
        ADVANCES_FILE: ["UID", "Employee Name", "Month", "Year", "Amount", "Note"],
        PRIMES_FILE:   ["UID", "Employee Name", "Month", "Year", "Amount", "Note"],
        NOTES_FILE:    ["UID", "Employee Name", "Date", "Note"],
    }

    for path, cols in excel_files.items():
        if not os.path.exists(path):
            pd.DataFrame(columns=cols).to_excel(path, index=False)


# ─────────────────────────────────────────────
# PYQT APP
# ─────────────────────────────────────────────
from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget

from utils.file_utils import setup_logging, ensure_directories
from ui.activation_page import ActivationPage
from ui.login_page import LoginPage
from ui.main_window import MainWindow
from translation_manager import TranslationManager
from services import license_service
from services.attendance_cleanup_service import cleanup_old_attendance_months


# ─────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────
class AppWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(TranslationManager.instance().t("app.title"))
        self.resize(1200, 750)
        self.setMinimumSize(1000, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_window = None
        self.login_page = None
        self.activation_page = None
        self._show_initial_page()

    def _show_initial_page(self):
        if not license_service.is_activated():
            self._show_activation()
        else:
            self._show_login()

    def _show_activation(self):
        self.main_window = self._clear_page(self.main_window)
        self.login_page = self._clear_page(self.login_page)

        if self.activation_page is None:
            self.activation_page = ActivationPage(self.stack, on_activate=self._show_login)
            self.stack.addWidget(self.activation_page)
        self.stack.setCurrentWidget(self.activation_page)

    def _show_login(self):
        self.activation_page = self._clear_page(self.activation_page)
        self.main_window = self._clear_page(self.main_window)

        if self.login_page is None:
            self.login_page = LoginPage(self.stack, on_login_success=self._on_login_success)
            self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.login_page)

    def _clear_page(self, page):
        if page is None:
            return None
        try:
            self.stack.removeWidget(page)
        except Exception:
            pass
        page.deleteLater()
        return None

    def _on_login_success(self, username: str):
        if self.main_window:
            self.stack.removeWidget(self.main_window)
            self.main_window = None

        self.main_window = MainWindow(
            self.stack,
            username,
            on_logout=self._on_logout
        )
        self.stack.addWidget(self.main_window)
        self.stack.setCurrentWidget(self.main_window)

    def _on_logout(self):
        if self.main_window:
            self.stack.removeWidget(self.main_window)
            self.main_window = None

        self._show_login()

    def closeEvent(self, event):
        if self.main_window:
            self.main_window.destroy()
        event.accept()


# ─────────────────────────────────────────────
# MAIN ENTRY
# ─────────────────────────────────────────────
def main():
    print("DATA DIR:", BASE_DIR)

    _ensure_data_files()
    ensure_directories()
    setup_logging()
    cleanup_old_attendance_months()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    translator = TranslationManager.instance()
    app.setLayoutDirection(translator.qt_layout_direction)
    translator.language_changed.connect(
        lambda lang: app.setLayoutDirection(translator.qt_layout_direction)
    )

    window = AppWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()