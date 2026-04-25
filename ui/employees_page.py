from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

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
    padding: 6px 10px;
    font-size: 13px;
    color: {TEXT_MAIN};
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}

/* ── Form card ── */
QFrame#formCard {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
}}

/* ── Buttons ── */
QPushButton {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 13px;
    font-weight: 600;
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

/* ── Table ── */
QTableWidget {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
    gridline-color: {BORDER};
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 8px 12px;
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
    padding: 8px 12px;
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

        # Title
        title = QLabel("Employee Management")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

        # Body: table (left) + form (right)
        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

        # ── Table ────────────────────────────────
        cols = ("UID", "Full Name", "Hourly Rate", "Expected Start")
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.itemSelectionChanged.connect(self._on_select)
        body.addWidget(self._table, stretch=3)

        # ── Form card ────────────────────────────
        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        form_card.setFixedWidth(260)

        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(16, 16, 16, 16)
        form_layout.setSpacing(8)

        form_title = QLabel("Employee Details")
        form_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        form_title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        form_layout.addWidget(form_title)

        fields = [
            ("UID (NFC Card)",         "uid"),
            ("Full Name",              "name"),
            ("Hourly Rate (DH)",        "rate"),
            ("Expected Start (HH:MM)", "start"),
        ]
        self._inputs: dict[str, QLineEdit] = {}
        for label_text, key in fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
            form_layout.addWidget(lbl)

            inp = QLineEdit()
            form_layout.addWidget(inp)
            self._inputs[key] = inp

        form_layout.addSpacing(8)

        # Buttons
        btn_add = QPushButton("Add Employee")
        btn_add.setObjectName("addBtn")
        btn_add.clicked.connect(self._add)
        form_layout.addWidget(btn_add)

        btn_update = QPushButton("Update")
        btn_update.clicked.connect(self._update)
        form_layout.addWidget(btn_update)

        btn_delete = QPushButton("Delete")
        btn_delete.setObjectName("deleteBtn")
        btn_delete.clicked.connect(self._delete)
        form_layout.addWidget(btn_delete)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._clear_form)
        form_layout.addWidget(btn_clear)

        form_layout.addStretch()
        body.addWidget(form_card, stretch=0)

    # ── Actions ───────────────────────────────────────────────────────

    def refresh(self):
        self._table.setRowCount(0)
        for emp in employee_service.get_all_employees():
            r = self._table.rowCount()
            self._table.insertRow(r)
            for c, val in enumerate([emp.uid, emp.full_name, emp.hourly_rate, emp.expected_start_time]):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(r, c, item)

    def _on_select(self):
        rows = self._table.selectedItems()
        if not rows:
            return
        row = self._table.currentRow()
        keys = ["uid", "name", "rate", "start"]
        for col, key in enumerate(keys):
            item = self._table.item(row, col)
            self._inputs[key].setText(item.text() if item else "")

    def _get_form_employee(self) -> Employee | None:
        uid   = self._inputs["uid"].text().strip()
        name  = self._inputs["name"].text().strip()
        rate_str = self._inputs["rate"].text().strip()
        start = self._inputs["start"].text().strip()

        if not all([uid, name, rate_str, start]):
            QMessageBox.warning(self, "Validation", "All fields are required.")
            return None
        try:
            rate = float(rate_str)
        except ValueError:
            QMessageBox.warning(self, "Validation", "Hourly rate must be a number.")
            return None
        return Employee(uid=uid, full_name=name, hourly_rate=rate, expected_start_time=start)

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
            QMessageBox.warning(self, "Validation", "Select an employee first.")
            return
        confirm = QMessageBox.question(
            self, "Confirm",
            f"Delete employee with UID '{uid}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
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