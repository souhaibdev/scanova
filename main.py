#!/usr/bin/env python3
"""
NFC Attendance & Payroll Management System
==========================================
Production-ready desktop application for NFC-based employee
attendance tracking with real-time HID keyboard reader integration.

Run:
    python main.py
"""

import sys
import os

from PyQt6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt6.QtCore import Qt

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.file_utils import setup_logging, ensure_directories
from ui.login_page import LoginPage
from ui.main_window import MainWindow


class AppWindow(QMainWindow):
    """Top-level window — switches between LoginPage and MainWindow."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SCANOVA")
        self.resize(1200, 750)
        self.setMinimumSize(1000, 600)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._main_window: MainWindow | None = None
        self._show_login()

    # ── Navigation ────────────────────────────────────────────────────

    def _show_login(self):
        login = LoginPage(self._stack, on_login_success=self._on_login_success)
        self._stack.addWidget(login)
        self._stack.setCurrentWidget(login)

    def _on_login_success(self, username: str):
        # Clean up old main window if exists (re-login case)
        if self._main_window is not None:
            self._main_window.destroy()
            self._stack.removeWidget(self._main_window)
            self._main_window = None

        self._main_window = MainWindow(self._stack, username, on_logout=self._on_logout)
        self._stack.addWidget(self._main_window)
        self._stack.setCurrentWidget(self._main_window)

    def _on_logout(self):
        # Clean up main window and switch back to login
        if self._main_window is not None:
            self._stack.removeWidget(self._main_window)
            self._main_window = None
        self._show_login()

    # ── Cleanup ───────────────────────────────────────────────────────

    def closeEvent(self, event):
        if self._main_window is not None:
            self._main_window.destroy()
        event.accept()


def main():
    # Bootstrap
    ensure_directories()
    setup_logging()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # consistent look across platforms

    window = AppWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()