from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import re

from models.employee import Employee
from services import employee_service


ACCENT     = "#2B79FF"
BG_CARD    = "#FFFFFF"
BG_PAGE    = "#F0F2F5"
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
QLineEdit {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 0px 12px;
    font-size: 13px;
    color: {TEXT_MAIN};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QFrame#formCard {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
}}
QPushButton {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 0px 12px;
    font-size: 13px;
    font-weight: 600;
    height: 38px;
    color: {TEXT_MAIN};
}}
QPushButton:hover {{
    background: #EBF2FF;
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton#addBtn {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: #FFFFFF;
}}
QPushButton#addBtn:hover {{
    background: #1A65E0;
}}
QPushButton#deleteBtn {{
    background: #FFF0F0;
    border-color: #FFCDD2;
    color: {DANGER};
}}
QPushButton#deleteBtn:hover {{
    background: #FFCDD2;
}}
QTableWidget {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
    gridline-color: {BORDER};
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 10px 12px;
}}
QTableWidget::item:selected {{
    background: #EBF2FF;
    color: {TEXT_MAIN};
}}
QHeaderView::section {{
    background: #F5F8FF;
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 600;
    padding: 10px 12px;
    border: none;
    border-bottom: 1px solid {BORDER};
    text-transform: uppercase;
    letter-spacing: 0.4px;
}}
QScrollBar:vertical {{
    width: 6px;
    background: transparent;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
}}
"""

COLS      = ("UID", "CIN", "Full Name", "Hourly Rate (DH)", "Expected Start")
FIELD_MAP = ["uid", "cin", "name", "rate", "start"]


class EmployeesPage(QWidget):
    """CRUD interface for employee management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self.refresh()

    # ── Build ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel("Employee Management")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

        # Table
        self._table = QTableWidget(0, len(COLS))
        self._table.setHorizontalHeaderLabels(COLS)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.itemSelectionChanged.connect(self._on_select)
        body.addWidget(self._table, stretch=3)

        # Form card
        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        form_card.setFixedWidth(290)

        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(18, 18, 18, 18)
        fl.setSpacing(4)

        form_title = QLabel("Employee Details")
        form_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        form_title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        fl.addWidget(form_title)

        fl.addSpacing(8)

        fields = [
            ("UID (NFC Card)",         "uid"),
            ("CIN",                    "cin"),
            ("Full Name",              "name"),
            ("Hourly Rate (DH)",       "rate"),
            ("Expected Start (HH:MM)", "start"),
        ]
        self._inputs: dict[str, QLineEdit] = {}
        for label_text, key in fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
            fl.addWidget(lbl)
            inp = QLineEdit()
            inp.setFixedHeight(38)
            fl.addWidget(inp)
            fl.addSpacing(6)
            self._inputs[key] = inp

        fl.addSpacing(10)

        btn_add = QPushButton("Add Employee")
        btn_add.setFixedHeight(38)
        btn_add.setObjectName("addBtn")
        btn_add.clicked.connect(self._add)
        fl.addWidget(btn_add)

        btn_update = QPushButton("Update")
        btn_update.setFixedHeight(38)
        btn_update.clicked.connect(self._update)
        fl.addWidget(btn_update)

        btn_delete = QPushButton("Delete")
        btn_delete.setFixedHeight(38)
        btn_delete.setObjectName("deleteBtn")
        btn_delete.clicked.connect(self._delete)
        fl.addWidget(btn_delete)

        btn_clear = QPushButton("Clear")
        btn_clear.setFixedHeight(38)
        btn_clear.clicked.connect(self._clear_form)
        fl.addWidget(btn_clear)

        fl.addStretch()
        body.addWidget(form_card, stretch=0)

    # ── Table ─────────────────────────────────────────────────────────

    def refresh(self):
        self._table.setRowCount(0)
        for emp in employee_service.get_all_employees():
            r = self._table.rowCount()
            self._table.insertRow(r)
            for c, val in enumerate([
                emp.uid,
                emp.cin,
                emp.full_name,
                f"{emp.hourly_rate:.2f}",
                emp.expected_start_time,
            ]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(r, c, item)

    def _on_select(self):
        if not self._table.selectedItems():
            return
        row = self._table.currentRow()
        for col, key in enumerate(FIELD_MAP):
            item = self._table.item(row, col)
            self._inputs[key].setText(item.text() if item else "")

    # ── Validation ────────────────────────────────────────────────────

    def _get_form_employee(self) -> Employee | None:
        uid      = self._inputs["uid"].text().strip()
        cin      = self._inputs["cin"].text().strip()
        name     = self._inputs["name"].text().strip()
        rate_str = self._inputs["rate"].text().strip()
        start    = self._inputs["start"].text().strip()

        if not all([uid, cin, name, rate_str, start]):
            QMessageBox.warning(self, "Validation", "All fields are required.")
            return None

        if not cin.isalnum() or not (6 <= len(cin) <= 8):
            QMessageBox.warning(self, "Validation", "CIN must be 6 to 8 alphanumeric characters.")
            return None

        try:
            rate = float(rate_str.replace(",", "."))
            if rate <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Validation", "Hourly Rate must be a positive number.")
            return None

        if not re.fullmatch(r"\d{2}:\d{2}", start):
            QMessageBox.warning(self, "Validation", "Expected Start must follow this format: 08:00")
            return None

        return Employee(
            uid=uid,
            cin=cin.upper(),
            full_name=name,
            hourly_rate=rate,
            expected_start_time=start,
        )

    # ── CRUD ──────────────────────────────────────────────────────────

    def _add(self):
        emp = self._get_form_employee()
        if emp is None:
            return
        ok, msg = employee_service.add_employee(emp)
        if ok:
            self.refresh()
            self._clear_form()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.warning(self, "Error", msg)

    def _update(self):
        emp = self._get_form_employee()
        if emp is None:
            return
        ok, msg = employee_service.update_employee(emp)
        if ok:
            self.refresh()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.warning(self, "Error", msg)

    def _delete(self):
        uid = self._inputs["uid"].text().strip()
        if not uid:
            QMessageBox.warning(self, "Validation", "Please select an employee first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm",
            f"Delete employee with UID '{uid}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        ok, msg = employee_service.delete_employee(uid)
        if ok:
            self.refresh()
            self._clear_form()
            QMessageBox.information(self, "Deleted", msg)
        else:
            QMessageBox.warning(self, "Error", msg)

    def _clear_form(self):
        for inp in self._inputs.values():
            inp.clear()