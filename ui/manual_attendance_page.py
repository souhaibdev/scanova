"""
ui/manual_attendance_page.py
─────────────────────────────
Manual attendance entry — styled to match monthly_report_page.py

FIX (see _save method below):
- The Exit Time (and Entry Time) QLineEdit widgets use
  setInputMask("00:00"). When the field is left untouched, Qt's
  input-mask machinery does NOT return an empty string from .text() —
  it returns the mask's blank placeholder characters plus the literal
  separator, e.g. "  :  ". After .strip(), that collapses to just ":",
  which is a non-empty, truthy string.
  This made the code think the user had entered something in Exit
  Time, so it ran the "^\\d{2}:\\d{2}$" regex check on ":", which of
  course failed, and popped the "Exit Time must be HH:MM" warning even
  when the user never touched the exit field and only wanted to submit
  an entry-only record.
  Fix: after stripping, treat any value with no actual digits as
  genuinely empty before running the format checks.
"""

from __future__ import annotations

import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QMessageBox, QSizePolicy, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

from services.manual_attendance_service import add_manual_record, get_missing_employees
from translation_manager import TranslationManager

ACCENT     = "#2B79FF"
BG_PAGE    = "#F0F2F5"
BG_CARD    = "#FFFFFF"
TEXT_MAIN  = "#111111"
TEXT_MUTED = "#888888"
BORDER     = "#E4EAFF"
AMBER      = "#D97A00"
RED        = "#E53935"

STYLESHEET = f"""
QWidget {{
    background: {BG_PAGE};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI';
}}
QLineEdit, QDateEdit {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 13px;
    color: {TEXT_MAIN};
    min-height: 23px;
}}
QLineEdit:focus, QDateEdit:focus {{
    border-color: {ACCENT};
}}
QDateEdit::drop-down {{
    border: none;
    padding-right: 8px;
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
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 600;
    color: {TEXT_MAIN};
    min-height: 23px;
}}
QPushButton:hover {{
    background: #EBF2FF;
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton#saveBtn {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: #FFFFFF;
}}
QPushButton#saveBtn:hover {{
    background: #1A65E0;
}}
QPushButton#clearBtn {{
    background: transparent;
    border: 1.5px solid {BORDER};
    color: {TEXT_MUTED};
}}
QPushButton#clearBtn:hover {{
    background: #F7F9FF;
}}
QTableWidget {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
    gridline-color: {BORDER};
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 7px 10px;
    border-bottom: 1px solid {BORDER};
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
    padding: 8px 10px;
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

COLS = ("UID", "CIN", "Employee Name", "Entry Time", "Status")


class ManualAttendancePage(QWidget):
    """Manual attendance entry for employees who forgot to scan."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._translator = TranslationManager.instance()
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self.refresh()

    # ── Build ──────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel(self._translator.t("manual.title"))
        self._translator.bind_text(title, "manual.title")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

        subtitle = QLabel(self._translator.t("manual.subtitle"))
        self._translator.bind_text(subtitle, "manual.subtitle")
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        root.addWidget(subtitle)

        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

        # ── Table ──────────────────────────────────────────────────────
        self._table = QTableWidget(0, len(COLS))
        self._translator.bind_table_headers(self._table, [
            "employee.table.uid",
            "employee.table.cin",
            "employee.table.full_name",
            "manual.field.entry_time",
            "manual.field.status",
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.itemSelectionChanged.connect(self._on_table_selection_changed)
        body.addWidget(self._table, stretch=3)

        # ── Form Card ──────────────────────────────────────────────────
        form_card = QFrame()
        form_card.setObjectName("formCard")
        form_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        form_card.setFixedWidth(300)

        fl = QVBoxLayout(form_card)
        fl.setContentsMargins(18, 18, 18, 18)
        fl.setSpacing(10)

        form_title = QLabel(self._translator.t("manual.form.title"))
        self._translator.bind_text(form_title, "manual.form.title")
        form_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        form_title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        fl.addWidget(form_title)
        fl.addSpacing(10)

        def add_field(label_key, widget):
            fl.addWidget(self._muted_label(label_key))
            fl.addWidget(widget)
            fl.addSpacing(10)

        self._inp_uid = QLineEdit()
        self._inp_uid.setFixedHeight(38)
        self._translator.bind_placeholder(self._inp_uid, "manual.placeholder.uid")
        add_field("manual.field.uid", self._inp_uid)

        self._inp_name = QLineEdit()
        self._inp_name.setFixedHeight(38)
        self._inp_name.setReadOnly(True)
        self._inp_name.setStyleSheet(f"background: #F5F8FF; color: {TEXT_MUTED};")
        add_field("employee.field.full_name", self._inp_name)

        self._inp_cin = QLineEdit()
        self._inp_cin.setFixedHeight(38)
        self._inp_cin.setReadOnly(True)
        self._inp_cin.setStyleSheet(f"background: #F5F8FF; color: {TEXT_MUTED};")
        add_field("employee.field.cin", self._inp_cin)

        self._inp_date = QDateEdit()
        self._inp_date.setFixedHeight(38)
        self._inp_date.setCalendarPopup(True)
        self._inp_date.setDate(QDate.currentDate())
        self._inp_date.setDisplayFormat("yyyy-MM-dd")
        add_field("manual.field.date", self._inp_date)

        self._inp_entry = QLineEdit()
        self._inp_entry.setFixedHeight(38)
        self._inp_entry.setInputMask("00:00")
        self._translator.bind_placeholder(self._inp_entry, "manual.placeholder.entry")
        add_field("manual.field.entry_time", self._inp_entry)

        self._inp_exit = QLineEdit()
        self._inp_exit.setFixedHeight(38)
        self._inp_exit.setInputMask("00:00")
        self._translator.bind_placeholder(self._inp_exit, "manual.placeholder.exit")
        self._translator.bind_tooltip(self._inp_exit, "manual.tooltip.exit_optional")
        add_field("manual.field.exit_time", self._inp_exit)

        fl.addSpacing(4)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_clear = QPushButton(self._translator.t("manual.button.clear"))
        self._translator.bind_text(btn_clear, "manual.button.clear")
        btn_clear.setObjectName("clearBtn")
        btn_clear.setFixedHeight(38)
        btn_clear.clicked.connect(self._clear_form)
        btn_row.addWidget(btn_clear)

        btn_save = QPushButton(self._translator.t("manual.button.save"))
        self._translator.bind_text(btn_save, "manual.button.save")
        btn_save.setObjectName("saveBtn")
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        fl.addLayout(btn_row)
        fl.addStretch()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setWidget(form_card)
        scroll_area.setFixedWidth(300)
        body.addWidget(scroll_area, stretch=0)

    def _muted_label(self, text_key: str) -> QLabel:
        lbl = QLabel(self._translator.t(text_key))
        self._translator.bind_text(lbl, text_key)
        lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;"
        )
        return lbl

    # ── Data ───────────────────────────────────────────────────────────

    def refresh(self):
        self._populate(get_missing_employees())

    def _populate(self, df):
        self._table.setRowCount(0)
        for _, row in df.iterrows():
            r = self._table.rowCount()
            self._table.insertRow(r)
            for c, col in enumerate(COLS):
                val  = str(row.get(col, ""))
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == "Status":
                    if val == "Missing Exit":
                        item.setForeground(Qt.GlobalColor.darkYellow)
                    elif val == "No Record":
                        item.setForeground(Qt.GlobalColor.red)
                self._table.setItem(r, c, item)

    # ── Selection ──────────────────────────────────────────────────────

    def _on_table_selection_changed(self):
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            self._inp_name.clear()
            self._inp_cin.clear()
            return

        row         = selected_rows[0].row()
        uid_item    = self._table.item(row, 0)
        cin_item    = self._table.item(row, 1)
        name_item   = self._table.item(row, 2)
        entry_item  = self._table.item(row, 3)
        status_item = self._table.item(row, 4)

        self._inp_uid.setText(uid_item.text()   if uid_item   else "")
        self._inp_cin.setText(cin_item.text()   if cin_item   else "")
        self._inp_name.setText(name_item.text() if name_item  else "")
        self._inp_date.setDate(QDate.currentDate())

        status = status_item.text() if status_item else ""

        if status == "Missing Exit":
            entry_val = entry_item.text() if entry_item else ""
            self._inp_entry.setText(entry_val)
            self._inp_entry.setReadOnly(True)
            self._inp_entry.setStyleSheet(f"background: #F5F8FF; color: {TEXT_MUTED};")
            self._inp_exit.clear()
            self._inp_exit.setFocus()
        else:
            self._inp_entry.clear()
            self._inp_entry.setReadOnly(False)
            self._inp_entry.setEnabled(True)
            self._inp_entry.setStyleSheet("")
            self._inp_exit.clear()
            self._inp_exit.setEnabled(True)

    # ── Actions ────────────────────────────────────────────────────────

    def _save(self):
        uid        = self._inp_uid.text().strip()
        date_str   = self._inp_date.date().toString("yyyy-MM-dd")
        entry_time = self._inp_entry.text().strip()
        exit_time  = self._inp_exit.text().strip()

        # QLineEdit with setInputMask("00:00") never returns a truly empty
        # string when the field is untouched — it returns the mask's blank
        # placeholders plus the literal ":" separator (e.g. "  :  "), which
        # after strip() collapses to just ":". That is a non-empty, truthy
        # string, so it was being treated as "the user typed something" and
        # failing the HH:MM format check below even when nothing was
        # actually entered. Treat any value with no digits as empty.
        if not re.search(r"\d", entry_time):
            entry_time = ""
        if not re.search(r"\d", exit_time):
            exit_time = ""

        if not uid:
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("manual.validation.uid_required"),
            )
            return
        if not entry_time:
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("manual.validation.entry_required"),
            )
            return

        time_re = re.compile(r"^\d{2}:\d{2}$")
        if not time_re.match(entry_time):
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("manual.validation.entry_format"),
            )
            return
        if exit_time and not time_re.match(exit_time):
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("manual.validation.exit_format"),
            )
            return

        ok, msg = add_manual_record(uid, date_str, entry_time, exit_time)
        if ok:
            self.refresh()
            self._clear_form()
            QMessageBox.information(self, self._translator.t("common.success"), msg)
        else:
            QMessageBox.warning(self, self._translator.t("common.error"), msg)

    def _clear_form(self):
        self._inp_uid.clear()
        self._inp_name.clear()
        self._inp_cin.clear()
        self._inp_entry.clear()
        self._inp_entry.setReadOnly(False)
        self._inp_entry.setStyleSheet("")
        self._inp_exit.clear()
        self._inp_date.setDate(QDate.currentDate())