from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import re

from models.employee import Employee
from services import employee_service
from translation_manager import TranslationManager


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
    padding: 8px 14px;
    font-size: 13px;
    color: {TEXT_MAIN};
    selection-background-color: {ACCENT};
}}
QLineEdit:focus {{
    border: 2px solid {ACCENT};
    background: #F8FBFF;
}}
QLineEdit:disabled {{
    background: #F5F5F5;
    color: #BBBBBB;
    border-color: #E0E0E0;
}}
QLineEdit:hover:!focus {{
    border-color: #B0C4FF;
}}

QCheckBox {{
    font-size: 13px;
    color: {TEXT_MAIN};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1.5px solid {BORDER};
    border-radius: 4px;
    background: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
    image: url(none);
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}

QFrame#formCard {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 16px;
}}

QPushButton {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 0px 16px;
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
QPushButton:pressed {{
    background: #D6E8FF;
}}
QPushButton#addBtn {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: #FFFFFF;
    border-radius: 8px;
}}
QPushButton#addBtn:hover {{
    background: #1A65E0;
    border-color: #1A65E0;
}}
QPushButton#addBtn:pressed {{
    background: #1255C0;
}}
QPushButton#deleteBtn {{
    background: #FFF5F5;
    border-color: #FFCDD2;
    color: {DANGER};
}}
QPushButton#deleteBtn:hover {{
    background: #FFCDD2;
    border-color: {DANGER};
}}
QPushButton#deleteBtn:pressed {{
    background: #FFB3B3;
}}

QTableWidget {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
    gridline-color: {BORDER};
    font-size: 13px;
    outline: none;
}}
QTableWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid {BORDER};
}}
QTableWidget::item:selected {{
    background: #EBF2FF;
    color: {TEXT_MAIN};
}}
QTableWidget::item:hover {{
    background: #F5F9FF;
}}
QHeaderView::section {{
    background: #F5F8FF;
    color: {TEXT_MUTED};
    font-size: 11px;
    font-weight: 700;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid {BORDER};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:first {{
    border-top-left-radius: 10px;
}}
QHeaderView::section:last {{
    border-top-right-radius: 10px;
}}

QScrollBar:vertical {{
    width: 6px;
    background: transparent;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    height: 6px;
    background: transparent;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {ACCENT};
}}
"""

COLS      = ("UID", "CIN", "Full Name", "Hourly Rate (DH)", "Expected Start")
FIELD_MAP = ["uid", "cin", "name", "rate", "start"]


class EmployeesPage(QWidget):
    """CRUD interface for employee management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._translator = TranslationManager.instance()
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self.refresh()

    # ── Build ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel(self._translator.t("employee.title"))
        self._translator.bind_text(title, "employee.title")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

        # Table
        self._table = QTableWidget(0, len(COLS))
        self._translator.bind_table_headers(self._table, [
            "employee.table.uid",
            "employee.table.cin",
            "employee.table.full_name",
            "employee.table.hourly_rate",
            "employee.table.expected_start",
        ])
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

        form_title = QLabel(self._translator.t("employee.form.title"))
        self._translator.bind_text(form_title, "employee.form.title")
        form_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        form_title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        fl.addWidget(form_title)

        fl.addSpacing(8)

        fields = [
            ("employee.field.uid",         "uid"),
            ("employee.field.cin",         "cin"),
            ("employee.field.full_name",   "name"),
            ("employee.field.hourly_rate", "rate"),
            ("employee.field.expected_start", "start"),
        ]
        self._inputs: dict[str, QLineEdit] = {}
        for label_text, key in fields:
            lbl = QLabel(self._translator.t(label_text))
            self._translator.bind_text(lbl, label_text)
            lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
            fl.addWidget(lbl)
            inp = QLineEdit()
            inp.setFixedHeight(38)
            fl.addWidget(inp)
            fl.addSpacing(6)
            self._inputs[key] = inp

        self._cnss_checkbox = QCheckBox(self._translator.t("employee.checkbox.cnss"))
        self._translator.bind_text(self._cnss_checkbox, "employee.checkbox.cnss")
        self._cnss_checkbox.toggled.connect(self._set_cnss_enabled)
        fl.addWidget(self._cnss_checkbox)

        self._cnss_input = QLineEdit()
        self._cnss_input.setFixedHeight(38)
        self._cnss_input.setEnabled(False)
        self._translator.bind_placeholder(self._cnss_input, "employee.field.cnss")
        fl.addWidget(self._cnss_input)
        fl.addSpacing(6)

        self._amo_checkbox = QCheckBox(self._translator.t("employee.checkbox.amo"))
        self._translator.bind_text(self._amo_checkbox, "employee.checkbox.amo")
        self._amo_checkbox.toggled.connect(self._set_amo_enabled)
        fl.addWidget(self._amo_checkbox)

        self._amo_input = QLineEdit()
        self._amo_input.setFixedHeight(38)
        self._amo_input.setEnabled(False)
        self._translator.bind_placeholder(self._amo_input, "employee.field.amo")
        fl.addWidget(self._amo_input)
        fl.addSpacing(6)

        fl.addSpacing(10)

        btn_add = QPushButton(self._translator.t("employee.button.add"))
        self._translator.bind_text(btn_add, "employee.button.add")
        btn_add.setFixedHeight(38)
        btn_add.setObjectName("addBtn")
        btn_add.clicked.connect(self._add)
        fl.addWidget(btn_add)

        btn_update = QPushButton(self._translator.t("employee.button.update"))
        self._translator.bind_text(btn_update, "employee.button.update")
        btn_update.setFixedHeight(38)
        btn_update.clicked.connect(self._update)
        fl.addWidget(btn_update)

        btn_delete = QPushButton(self._translator.t("employee.button.delete"))
        self._translator.bind_text(btn_delete, "employee.button.delete")
        btn_delete.setFixedHeight(38)
        btn_delete.setObjectName("deleteBtn")
        btn_delete.clicked.connect(self._delete)
        fl.addWidget(btn_delete)

        btn_clear = QPushButton(self._translator.t("employee.button.clear"))
        self._translator.bind_text(btn_clear, "employee.button.clear")
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
        uid_item = self._table.item(row, 0)
        uid = uid_item.text() if uid_item else ""
        emp = employee_service.get_employee_by_uid(uid)
        if emp:
            self._inputs["uid"].setText(emp.uid)
            self._inputs["cin"].setText(emp.cin)
            self._inputs["name"].setText(emp.full_name)
            self._inputs["rate"].setText(f"{emp.hourly_rate:.2f}")
            self._inputs["start"].setText(emp.expected_start_time)

            self._cnss_checkbox.setChecked(emp.cnss_enabled)
            self._cnss_input.setText(f"{emp.cnss_value*100:.2f}" if emp.cnss_enabled and emp.cnss_value is not None else "")
            self._cnss_input.setEnabled(emp.cnss_enabled)

            self._amo_checkbox.setChecked(emp.amo_enabled)
            self._amo_input.setText(f"{emp.amo_value*100:.2f}" if emp.amo_enabled and emp.amo_value is not None else "")
            self._amo_input.setEnabled(emp.amo_enabled)
        else:
            for col, key in enumerate(FIELD_MAP):
                item = self._table.item(row, col)
                self._inputs[key].setText(item.text() if item else "")
            self._cnss_checkbox.setChecked(False)
            self._cnss_input.clear()
            self._cnss_input.setEnabled(False)
            self._amo_checkbox.setChecked(False)
            self._amo_input.clear()
            self._amo_input.setEnabled(False)

    # ── Validation ────────────────────────────────────────────────────

    def _get_form_employee(self) -> Employee | None:
        uid      = self._inputs["uid"].text().strip()
        cin      = self._inputs["cin"].text().strip()
        name     = self._inputs["name"].text().strip()
        rate_str = self._inputs["rate"].text().strip()
        start    = self._inputs["start"].text().strip()

        if not all([uid, cin, name, rate_str, start]):
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("employee.validation.all_required"),
            )
            return None

        if not cin.isalnum() or not (6 <= len(cin) <= 8):
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("employee.validation.cin_invalid"),
            )
            return None

        try:
            rate = float(rate_str.replace(",", "."))
            if rate <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("employee.validation.rate_invalid"),
            )
            return None

        if not re.fullmatch(r"\d{2}:\d{2}", start):
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("employee.validation.start_invalid"),
            )
            return None

        cnss_enabled = self._cnss_checkbox.isChecked()
        cnss_value = None
        if cnss_enabled:
            cnss_text = self._cnss_input.text().strip()
            if not cnss_text:
                QMessageBox.warning(
                    self,
                    self._translator.t("common.validation"),
                    self._translator.t("employee.validation.cnss_required"),
                )
                return None
            try:
                cnss_value = float(cnss_text.replace(",", ".")) / 100
            except ValueError:
                QMessageBox.warning(
                    self,
                    self._translator.t("common.validation"),
                    self._translator.t("employee.validation.cnss_invalid"),
                )
                return None

        amo_enabled = self._amo_checkbox.isChecked()
        amo_value = None
        if amo_enabled:
            amo_text = self._amo_input.text().strip()
            if not amo_text:
                QMessageBox.warning(
                    self,
                    self._translator.t("common.validation"),
                    self._translator.t("employee.validation.amo_required"),
                )
                return None
            try:
                amo_value = float(amo_text.replace(",", ".")) / 100
            except ValueError:
                QMessageBox.warning(
                    self,
                    self._translator.t("common.validation"),
                    self._translator.t("employee.validation.amo_invalid"),
                )
                return None

        return Employee(
            uid=uid,
            cin=cin.upper(),
            full_name=name,
            hourly_rate=rate,
            expected_start_time=start,
            cnss_enabled=cnss_enabled,
            cnss_value=cnss_value,
            amo_enabled=amo_enabled,
            amo_value=amo_value,
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
            QMessageBox.information(self, self._translator.t("common.success"), msg)
        else:
            QMessageBox.warning(self, self._translator.t("common.error"), msg)

    def _update(self):
        emp = self._get_form_employee()
        if emp is None:
            return
        ok, msg = employee_service.update_employee(emp)
        if ok:
            self.refresh()
            QMessageBox.information(self, self._translator.t("common.success"), msg)
        else:
            QMessageBox.warning(self, self._translator.t("common.error"), msg)

    def _set_cnss_enabled(self, enabled: bool):
        self._cnss_input.setEnabled(enabled)
        if not enabled:
            self._cnss_input.clear()

    def _set_amo_enabled(self, enabled: bool):
        self._amo_input.setEnabled(enabled)
        if not enabled:
            self._amo_input.clear()

    def _delete(self):
        uid = self._inputs["uid"].text().strip()
        if not uid:
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("employee.validation.all_required"),
            )
            return
        confirm = QMessageBox.question(
            self,
            self._translator.t("common.confirm"),
            self._translator.t("employee.confirm.delete_employee", uid=uid),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        ok, msg = employee_service.delete_employee(uid)
        if ok:
            self.refresh()
            self._clear_form()
            QMessageBox.information(self, self._translator.t("common.success"), msg)
        else:
            QMessageBox.warning(self, self._translator.t("common.error"), msg)

    def _clear_form(self):
        for inp in self._inputs.values():
            inp.clear()
        self._cnss_checkbox.setChecked(False)
        self._cnss_input.clear()
        self._cnss_input.setEnabled(False)
        self._amo_checkbox.setChecked(False)
        self._amo_input.clear()
        self._amo_input.setEnabled(False)
