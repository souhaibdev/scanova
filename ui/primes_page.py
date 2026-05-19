"""
ui/primes_page.py
──────────────────
Primes page — same layout as Advances page.
Prime ADDS to the monthly net salary.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox,
    QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

from services.primes_service import get_all_primes, add_prime, delete_prime
from services import employee_service

# ── Palette ───────────────────────────────────────────────────────────────────
ACCENT     = "#2B79FF"
BG_PAGE    = "#F0F2F5"
BG_CARD    = "#FFFFFF"
TEXT_MAIN  = "#111111"
TEXT_MUTED = "#888888"
BORDER     = "#E4EAFF"
DANGER     = "#E53935"

STYLESHEET = f"""
QWidget {{ background: {BG_PAGE}; color: {TEXT_MAIN}; font-family: 'Segoe UI'; }}
QLineEdit {{
    background: {BG_CARD}; border: 1.5px solid {BORDER};
    border-radius: 8px; padding: 6px 10px; font-size: 13px; color: {TEXT_MAIN};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QFrame#card {{ background: {BG_CARD}; border: 1.5px solid {BORDER}; border-radius: 12px; }}
QTableWidget {{
    background: {BG_CARD}; border: 1.5px solid {BORDER}; border-radius: 12px;
    gridline-color: {BORDER}; font-size: 13px;
}}
QTableWidget::item {{ padding: 8px 12px; }}
QTableWidget::item:selected {{ background: #EBF2FF; color: {TEXT_MAIN}; }}
QHeaderView::section {{
    background: #F5F8FF; color: {TEXT_MUTED}; font-size: 11px; font-weight: 600;
    padding: 7px 10px; border: none; border-bottom: 1px solid {BORDER};
}}
QPushButton {{
    background: {BG_CARD}; border: 1.5px solid {BORDER}; border-radius: 8px;
    padding: 7px 16px; font-size: 13px; font-weight: 600; color: {TEXT_MAIN};
}}
QPushButton:hover {{ background: #EBF2FF; border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton#saveBtn {{ background: {ACCENT}; border-color: {ACCENT}; color: white; }}
QPushButton#saveBtn:hover {{ background: #1A65E0; }}
QPushButton#delBtn {{ background: #FFF0F0; border-color: #FFCDD2; color: {DANGER}; }}
QPushButton#delBtn:hover {{ background: #FFCDD2; }}
QScrollBar:vertical {{ width: 6px; background: transparent; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 3px; }}
"""


class PrimesPage(QWidget):
    """Primes page — adds to monthly net salary."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLESHEET)
        self._selected_uid: str = ""
        self._selected_name: str = ""
        self._selected_history_index: int = -1
        self._all_employees: list[tuple[str, str]] = []
        self._build_ui()
        self.refresh()

    # ── Build ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Title + badge
        title_row = QHBoxLayout()
        title = QLabel("Primes")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        title_row.addWidget(title)

        badge = QLabel("+  Adds to Net Salary")
        badge.setStyleSheet(
            f"background: #EBF2FF; color: {ACCENT}; font-size: 11px; font-weight: 600;"
            f"border-radius: 10px; padding: 3px 10px;"
        )
        title_row.addWidget(badge)
        title_row.addStretch()
        root.addLayout(title_row)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

        # ── LEFT: Employee selector ───────────────────────────────────
        left = QFrame()
        left.setObjectName("card")
        left.setFixedWidth(240)
        ll = QVBoxLayout(left)
        ll.setContentsMargins(12, 12, 12, 12)
        ll.setSpacing(8)

        lbl = QLabel("Select Employee")
        lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        ll.addWidget(lbl)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(" Search name or UID...")
        self._search_input.textChanged.connect(self._filter_employees)
        ll.addWidget(self._search_input)

        self._emp_table = QTableWidget(0, 1)
        self._emp_table.horizontalHeader().setVisible(False)
        self._emp_table.verticalHeader().setVisible(False)
        self._emp_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._emp_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._emp_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._emp_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._emp_table.setShowGrid(False)
        self._emp_table.itemSelectionChanged.connect(self._on_employee_select)
        ll.addWidget(self._emp_table, stretch=1)
        body.addWidget(left)

        # ── RIGHT ─────────────────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(10)

        self._selected_lbl = QLabel("← Select an employee")
        self._selected_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._selected_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        right.addWidget(self._selected_lbl)

        # Form card
        form_card = QFrame()
        form_card.setObjectName("card")
        fl = QHBoxLayout(form_card)
        fl.setContentsMargins(16, 14, 16, 14)
        fl.setSpacing(12)

        fl.addWidget(self._muted("Amount (DH):"))
        self._amount_input = QLineEdit()
        self._amount_input.setPlaceholderText("ex: 500")
        self._amount_input.setFixedWidth(110)
        fl.addWidget(self._amount_input)

        fl.addWidget(self._muted("Note:"))
        self._note_input = QLineEdit()
        self._note_input.setPlaceholderText("Prime de rendement...")
        fl.addWidget(self._note_input, stretch=1)

        self._save_btn = QPushButton("Save Prime")
        self._save_btn.setObjectName("saveBtn")
        self._save_btn.clicked.connect(self._save_prime)
        fl.addWidget(self._save_btn)

        self._del_btn = QPushButton("Delete")
        self._del_btn.setObjectName("delBtn")
        self._del_btn.clicked.connect(self._delete_prime)
        self._del_btn.setVisible(False)
        fl.addWidget(self._del_btn)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._clear_form)
        fl.addWidget(btn_clear)

        right.addWidget(form_card)

        hist_lbl = QLabel("Prime History")
        hist_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hist_lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        right.addWidget(hist_lbl)

        cols = ["UID", "Employee Name", "Amount (DH)", "Date", "Note", "Month", "Year"]
        self._hist_table = QTableWidget(0, len(cols))
        self._hist_table.setHorizontalHeaderLabels(cols)
        self._hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._hist_table.verticalHeader().setVisible(False)
        self._hist_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._hist_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._hist_table.itemSelectionChanged.connect(self._on_history_select)
        right.addWidget(self._hist_table, stretch=1)

        body.addLayout(right, stretch=1)

    def _muted(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        return lbl

    # ── Refresh ───────────────────────────────────────────────────────

    def refresh(self):
        self._all_employees = [
            (emp.uid, emp.full_name)
            for emp in employee_service.get_all_employees()
        ]
        self._filter_employees(self._search_input.text())
        self._load_history(uid_filter=self._selected_uid)

    def _filter_employees(self, query: str):
        q = query.strip().lower()
        filtered = [
            (uid, name) for uid, name in self._all_employees
            if q in name.lower() or q in uid.lower()
        ] if q else self._all_employees

        self._emp_table.setRowCount(0)

        # "All Employees" option
        all_item = QTableWidgetItem("All Employees")
        all_item.setData(Qt.ItemDataRole.UserRole, "*all*")
        all_item.setForeground(QColor(ACCENT))
        self._emp_table.insertRow(0)
        self._emp_table.setItem(0, 0, all_item)

        for uid, name in filtered:
            r = self._emp_table.rowCount()
            self._emp_table.insertRow(r)
            item = QTableWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, uid)
            item.setToolTip(f"UID: {uid}")
            self._emp_table.setItem(r, 0, item)

    def _load_history(self, uid_filter: str = ""):
        self._hist_table.setRowCount(0)
        if not uid_filter:
            return

        df = get_all_primes()
        if df.empty:
            return

        if uid_filter != "*all*":
            df = df[df["UID"].astype(str) == uid_filter]

        src_cols = ["UID", "Employee Name", "Amount", "Date", "Note", "Month", "Year"]

        for idx, row in df.iterrows():
            r = self._hist_table.rowCount()
            self._hist_table.insertRow(r)
            for c, col in enumerate(src_cols):
                val  = str(row.get(col, ""))
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, idx)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == "Amount":
                    item.setForeground(QColor(ACCENT))
                    item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
                self._hist_table.setItem(r, c, item)

        self._hist_table.viewport().update()

    # ── Employee selection ─────────────────────────────────────────────

    def _on_employee_select(self):
        items = self._emp_table.selectedItems()
        if not items:
            return
        item = self._emp_table.item(self._emp_table.currentRow(), 0)
        if not item:
            return
        self._selected_uid  = item.data(Qt.ItemDataRole.UserRole)
        self._selected_name = item.text()

        if self._selected_uid == "*all*":
            self._selected_lbl.setText("All Employees")
        else:
            self._selected_lbl.setText(f"{self._selected_name}")
        self._selected_lbl.setStyleSheet(
            f"color: {ACCENT}; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self._load_history(uid_filter=self._selected_uid)
        self._clear_form()

    # ── History selection ──────────────────────────────────────────────

    def _on_history_select(self):
        if not self._hist_table.selectedItems():
            self._del_btn.setVisible(False)
            return
        row = self._hist_table.currentRow()

        uid_item    = self._hist_table.item(row, 0)
        name_item   = self._hist_table.item(row, 1)
        amount_item = self._hist_table.item(row, 2)
        note_item   = self._hist_table.item(row, 4)

        self._selected_history_index = uid_item.data(Qt.ItemDataRole.UserRole) if uid_item else -1
        self._amount_input.setText(amount_item.text() if amount_item else "")
        self._note_input.setText(note_item.text() if note_item else "")

        uid  = uid_item.text()  if uid_item  else ""
        name = name_item.text() if name_item else ""
        if uid and uid != self._selected_uid:
            self._selected_uid  = uid
            self._selected_name = name
            self._selected_lbl.setText(f"{name}")
            self._selected_lbl.setStyleSheet(
                f"color: {ACCENT}; font-size: 14px; font-weight: 700; background: transparent;"
            )

        self._del_btn.setVisible(True)

    # ── Actions ───────────────────────────────────────────────────────

    def _save_prime(self):
        if not self._selected_uid or self._selected_uid == "*all*":
            QMessageBox.warning(self, "Validation", "Please select a specific employee.")
            return
        amount_str = self._amount_input.text().strip()
        note       = self._note_input.text().strip()
        if not amount_str:
            QMessageBox.warning(self, "Validation", "Please enter an amount.")
            return
        try:
            amount = float(amount_str)
        except ValueError:
            QMessageBox.warning(self, "Validation", "Amount must be a number.")
            return

        ok, msg = add_prime(self._selected_uid, self._selected_name, amount, note)
        if ok:
            QMessageBox.information(self, "Success", msg)
            self._clear_form()
            self._load_history(uid_filter=self._selected_uid)
        else:
            QMessageBox.warning(self, "Error", msg)

    def _delete_prime(self):
        if self._selected_history_index < 0:
            return
        reply = QMessageBox.question(
            self, "Confirm", "Delete this prime record?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok, msg = delete_prime(self._selected_history_index)
        if ok:
            self._clear_form()
            self._load_history(uid_filter=self._selected_uid)
        else:
            QMessageBox.warning(self, "Error", msg)

    def _clear_form(self):
        self._amount_input.clear()
        self._note_input.clear()
        self._selected_history_index = -1
        self._del_btn.setVisible(False)
        self._hist_table.clearSelection()