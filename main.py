#!/usr/bin/env python3
"""
NFC Attendance & Payroll Management System
Production-ready version
"""

import sys
import os
import json

# ─────────────────────────────────────────────
# APP DATA (IMPORTANT FOR EXE / MULTI PC)
# ─────────────────────────────────────────────
APP_NAME = "SCANOVA"

DATA_DIR = os.path.join(os.getenv("APPDATA"), APP_NAME)
os.makedirs(DATA_DIR, exist_ok=True)


# ─────────────────────────────────────────────
# DATA FILES PATHS
# ─────────────────────────────────────────────
EMPLOYEES_FILE = os.path.join(DATA_DIR, "employees.json")
ATTENDANCE_FILE = os.path.join(DATA_DIR, "attendance.xlsx")
ADVANCES_FILE = os.path.join(DATA_DIR, "advances.xlsx")
PRIMES_FILE = os.path.join(DATA_DIR, "primes.xlsx")
NOTES_FILE = os.path.join(DATA_DIR, "notes.xlsx")


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
from ui.login_page import LoginPage
from ui.main_window import MainWindow


# ─────────────────────────────────────────────
# MAIN WINDOW
# ─────────────────────────────────────────────
class AppWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SCANOVA")
        self.resize(1200, 750)
        self.setMinimumSize(1000, 600)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.main_window = None
        self._show_login()

    def _show_login(self):
        login = LoginPage(self.stack, on_login_success=self._on_login_success)
        self.stack.addWidget(login)
        self.stack.setCurrentWidget(login)

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
    print("DATA DIR:", DATA_DIR)

    _ensure_data_files()
    ensure_directories()
    setup_logging()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = AppWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()