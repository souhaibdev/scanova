from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QMessageBox, QSizePolicy, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont

import logging
import pandas as pd

from services.attendance_service import get_attendance_df
from models.attendance_record import AttendanceRecord

logger = logging.getLogger(__name__)


ACCENT    = "#2B79FF"
BG_CARD   = "#FFFFFF"
BG_PAGE   = "#F0F2F5"
TEXT_MAIN = "#111111"
TEXT_MUTED= "#888888"
BORDER    = "#E4EAFF"


STYLESHEET = f"""
QWidget {{
    background: {BG_PAGE};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI';
}}

/* ── Inputs ── */
QLineEdit, QComboBox, QDateEdit {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 13px;
    color: {TEXT_MAIN};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QDateEdit::drop-down {{
    border: none;
    padding-right: 8px;
}}
QDateEdit::down-arrow {{
    image: none;
    width: 12px;
    height: 12px;
}}

/* ── Calendar Popup ── */
QCalendarWidget {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 10px;
    font-size: 13px;
}}
QCalendarWidget QToolButton {{
    background: {BG_CARD};
    color: {TEXT_MAIN};
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 4px 8px;
}}
QCalendarWidget QToolButton:hover {{
    background: #EBF2FF;
    color: {ACCENT};
}}
QCalendarWidget QAbstractItemView {{
    background: {BG_CARD};
    selection-background-color: {ACCENT};
    selection-color: white;
    border-radius: 6px;
}}
QCalendarWidget QAbstractItemView:enabled {{
    color: {TEXT_MAIN};
}}
QCalendarWidget QAbstractItemView:disabled {{
    color: {TEXT_MUTED};
}}

/* ── Buttons ── */
QPushButton {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 600;
    color: {TEXT_MAIN};
}}
QPushButton:hover {{
    background: #EBF2FF;
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton#exportBtn {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: #FFFFFF;
}}
QPushButton#exportBtn:hover {{
    background: #1A65E0;
    border-color: #1A65E0;
    color: #FFFFFF;
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


class AttendancePage(QWidget):
    """Attendance records view with filters and Excel export."""

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
        title = QLabel("Attendance Records")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

        # ── Filters row ──
        filt_row = QHBoxLayout()
        filt_row.setSpacing(10)

        # Date — QDateEdit مع calendrier popup
        filt_row.addWidget(self._muted_label("Date:"))
        self._date_input = QDateEdit()
        self._date_input.setCalendarPopup(True)          # كيفتح calendrier بالكليك
        self._date_input.setDate(QDate.currentDate())    # default = اليوم
        self._date_input.setDisplayFormat("yyyy-MM-dd")  # نفس format YYYY-MM-DD
        self._date_input.setFixedWidth(140)
        self._date_input.setSpecialValueText(" ")         # يسمح بـ "بلا فلتر"
        self._date_input.setMinimumDate(QDate(2000, 1, 1))
        filt_row.addWidget(self._date_input)

        # Employee
        filt_row.addWidget(self._muted_label("Employee:"))
        self._emp_input = QLineEdit()
        self._emp_input.setPlaceholderText("Search name...")
        self._emp_input.setFixedWidth(180)
        filt_row.addWidget(self._emp_input)

        # Late
        filt_row.addWidget(self._muted_label("Late:"))
        self._late_combo = QComboBox()
        self._late_combo.addItems(["All", "YES", "NO"])
        self._late_combo.setFixedWidth(80)
        filt_row.addWidget(self._late_combo)

        # Buttons
        btn_apply = QPushButton("Apply Filters")
        btn_apply.clicked.connect(self.refresh)
        filt_row.addWidget(btn_apply)

        btn_clear = QPushButton("Clear Filters")
        btn_clear.clicked.connect(self._clear_filters)
        filt_row.addWidget(btn_clear)

        filt_row.addStretch()

        btn_export = QPushButton("Export Excel")
        btn_export.setObjectName("exportBtn")
        btn_export.clicked.connect(self._export)
        filt_row.addWidget(btn_export)

        root.addLayout(filt_row)

        # ── Table ──
        cols = AttendanceRecord.columns()
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self._table, stretch=1)

    def _muted_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
        return lbl

    # ── Data ──────────────────────────────────────────────────────────

    def refresh(self):
        df = get_attendance_df()
        logger.info("AttendancePage refresh: loaded %d records", len(df))

        # Date — ناخدو من QDateEdit بـ format YYYY-MM-DD
        selected_date = self._date_input.date()
        date_f = selected_date.toString("yyyy-MM-dd")

        emp_f  = self._emp_input.text().strip().lower()
        late_f = self._late_combo.currentText()

        if date_f:
            df = df[df["Date"].astype(str) == date_f]
        if emp_f:
            df = df[df["Employee Name"].astype(str).str.lower().str.contains(emp_f, na=False)]
        if late_f != "All":
            df = df[df["Late"].astype(str).str.upper() == late_f]

        logger.info("AttendancePage refresh: after filtering, %d records", len(df))

        cols = AttendanceRecord.columns()
        self._table.setRowCount(0)

        for _, row in df.iterrows():
            r = self._table.rowCount()
            self._table.insertRow(r)
            for c, col in enumerate(cols):
                val = str(row[col]) if pd.notna(row[col]) else ""
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(r, c, item)

        self._table.viewport().update()
        self._table.repaint()
        logger.info("AttendancePage refresh: table updated with %d rows", self._table.rowCount())

    def _clear_filters(self):
        self._date_input.setDate(QDate.currentDate())
        self._emp_input.clear()
        self._late_combo.setCurrentText("All")
        self.refresh()

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Attendance",
            "attendance.xlsx",
            "Excel files (*.xlsx)"
        )
        if path:
            df = get_attendance_df()
            df.to_excel(path, index=False)
            QMessageBox.information(self, "Exported", f"Attendance exported to:\n{path}")