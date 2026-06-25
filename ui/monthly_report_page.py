"""
ui/monthly_report_page.py
──────────────────────────
Monthly attendance report:
  • Filters: Month, Year, UID, Name, Late
  • Stats cards row 1: Jours travaillés / Absents / Late / Total Salary
  • Stats cards row 2: Total Advances / Total Primes / Net Salary
  • Detail table: UID, Employee Name, Date, Entry, Exit,
                  Worked Hours, Hourly Rate, Total Salary, Late
"""

from __future__ import annotations

import calendar
from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from translation_manager import TranslationManager

# ── Palette ───────────────────────────────────────────────────────────────────
ACCENT      = "#2B79FF"
BG_PAGE     = "#F0F2F5"
BG_CARD     = "#FFFFFF"
TEXT_MAIN   = "#111111"
TEXT_MUTED  = "#888888"
BORDER      = "#E4EAFF"
GREEN       = "#1AAA6E"
AMBER       = "#D97A00"
RED         = "#E53935"
PURPLE      = "#7C4DFF"

STYLESHEET = f"""
QWidget {{
    background: {BG_PAGE};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI';
}}
QLineEdit, QComboBox {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 5px 10px;
    font-size: 13px;
    color: {TEXT_MAIN};
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; padding-right: 8px; }}

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
QPushButton#applyBtn {{
    background: {ACCENT};
    border-color: {ACCENT};
    color: #FFFFFF;
}}
QPushButton#applyBtn:hover {{ background: #1A65E0; }}

QFrame#statCard {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
}}

QTableWidget {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
    gridline-color: {BORDER};
    font-size: 13px;
}}
QTableWidget::item {{ padding: 7px 10px; }}
QTableWidget::item:selected {{ background: #EBF2FF; color: {TEXT_MAIN}; }}
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
QScrollBar:vertical {{ width: 6px; background: transparent; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 3px; }}
"""


# ── Stat Card ─────────────────────────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, label_key: str, translator: TranslationManager, accent: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._label_key = label_key
        self._translator = translator

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        lbl = QLabel(self._translator.t(self._label_key).upper())
        self._label = lbl
        lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 0.5px; background: transparent;"
        )
        lay.addWidget(lbl)

        self._val = QLabel("-")
        self._val.setStyleSheet(
            f"color: {accent}; font-size: 24px; font-weight: 700; background: transparent;"
        )
        lay.addWidget(self._val)

    def set_value(self, text: str):
        self._val.setText(text)

    def refresh_translation(self):
        self._label.setText(self._translator.t(self._label_key).upper())


# ── Monthly Report Page ───────────────────────────────────────────────────────

class MonthlyReportPage(QWidget):
    """Monthly attendance report with filters and stats."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._translator = TranslationManager.instance()
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self._translator.language_changed.connect(self._refresh_dynamic_translations)
        self.refresh()

    # ── Build ──────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── Title ──
        title = QLabel(self._translator.t("monthly.title"))
        self._translator.bind_text(title, "monthly.title")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

        # ── Filter row ──
        frow = QHBoxLayout()
        frow.setSpacing(10)

        today = date.today()

        # Month
        frow.addWidget(self._muted("monthly.filter.month"))
        self._month_combo = QComboBox()
        month_items = [(f"month.{calendar.month_name[i].lower()}", i) for i in range(1, 13)]
        self._translator.bind_combo_items(self._month_combo, month_items)
        self._month_combo.setCurrentIndex(today.month - 1)
        self._month_combo.setFixedWidth(120)
        frow.addWidget(self._month_combo)

        # Year
        frow.addWidget(self._muted("monthly.filter.year"))
        self._year_combo = QComboBox()
        for y in range(today.year - 3, today.year + 2):
            self._year_combo.addItem(str(y), y)
        self._year_combo.setCurrentText(str(today.year))
        self._year_combo.setFixedWidth(80)
        frow.addWidget(self._year_combo)

        # UID
        frow.addWidget(self._muted("monthly.filter.uid"))
        self._uid_input = QLineEdit()
        self._translator.bind_placeholder(self._uid_input, "monthly.filter.uid")
        self._uid_input.setFixedWidth(120)
        frow.addWidget(self._uid_input)

        # Name
        frow.addWidget(self._muted("monthly.filter.name"))
        self._name_input = QLineEdit()
        self._translator.bind_placeholder(self._name_input, "monthly.filter.name")
        self._name_input.setFixedWidth(150)
        frow.addWidget(self._name_input)

        # Late
        frow.addWidget(self._muted("monthly.filter.late"))
        self._late_combo = QComboBox()
        self._translator.bind_combo_items(self._late_combo, [
            ("monthly.filter.all", "All"),
            ("monthly.filter.yes", "YES"),
            ("monthly.filter.no", "NO"),
        ])
        self._late_combo.setFixedWidth(80)
        frow.addWidget(self._late_combo)

        # Buttons
        btn_apply = QPushButton(self._translator.t("monthly.button.apply"))
        self._translator.bind_text(btn_apply, "monthly.button.apply")
        btn_apply.setObjectName("applyBtn")
        btn_apply.clicked.connect(self.refresh)
        frow.addWidget(btn_apply)

        btn_clear = QPushButton(self._translator.t("monthly.button.clear"))
        self._translator.bind_text(btn_clear, "monthly.button.clear")
        btn_clear.clicked.connect(self._clear_filters)
        frow.addWidget(btn_clear)

        frow.addStretch()
        root.addLayout(frow)

        # ── Stat cards row 1: attendance ──
        cards_row1 = QHBoxLayout()
        cards_row1.setSpacing(12)

        self._card_travailles = StatCard("monthly.stat.days_worked", self._translator, GREEN)
        self._card_absents    = StatCard("monthly.stat.days_absent", self._translator, RED)
        self._card_late       = StatCard("monthly.stat.late_days", self._translator, AMBER)
        self._card_salary     = StatCard("monthly.stat.total_salary", self._translator, ACCENT)

        for card in (self._card_travailles, self._card_absents,
                     self._card_late, self._card_salary):
            cards_row1.addWidget(card)

        root.addLayout(cards_row1)

        # ── Stat cards row 2: advances / primes / net ──
        cards_row2 = QHBoxLayout()
        cards_row2.setSpacing(12)

        self._card_advances = StatCard("monthly.stat.total_advances", self._translator, RED)
        self._card_primes   = StatCard("monthly.stat.total_primes", self._translator, GREEN)
        self._card_net      = StatCard("monthly.stat.net_salary", self._translator, ACCENT)

        for card in (self._card_advances, self._card_primes, self._card_net):
            cards_row2.addWidget(card)

        cards_row2.addStretch()
        root.addLayout(cards_row2)

        # ── Table ──
        cols = [
            "report.employee.table.uid",
            "report.employee.table.employee_name",
            "report.employee.table.date",
            "report.employee.table.entry_time",
            "report.employee.table.exit_time",
            "report.employee.table.worked_hours",
            "report.employee.table.hourly_rate",
            "report.employee.table.total_salary",
            "report.employee.table.late",
        ]
        self._table = QTableWidget(0, len(cols))
        self._translator.bind_table_headers(self._table, cols)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self._table, stretch=1)

    def _muted(self, text_key: str) -> QLabel:
        lbl = QLabel(self._translator.t(text_key))
        self._translator.bind_text(lbl, text_key)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
        return lbl

    # ── Data ───────────────────────────────────────────────────────────

    def refresh(self):
        from services.monthly_report_service import get_monthly_report_filtered

        month = self._month_combo.currentData()
        year  = self._year_combo.currentData()

        result = get_monthly_report_filtered(
            month       = month,
            year        = year,
            uid_filter  = self._uid_input.text().strip(),
            name_filter = self._name_input.text().strip(),
            late_filter = self._late_combo.currentData(),
        )

        stats = result["stats"]
        df    = result["detail_rows"]

        # Row 1
        self._card_travailles.set_value(str(stats["jours_travailles"]))
        self._card_absents.set_value(str(stats["jours_absents"]))
        self._card_late.set_value(str(stats["jours_late"]))
        self._card_salary.set_value(f"DH {stats['total_salary']:.2f}")

        # Row 2
        self._card_advances.set_value(f"-DH {stats.get('total_advances', 0.0):.2f}")
        self._card_primes.set_value(f"+DH {stats.get('total_primes', 0.0):.2f}")
        self._card_net.set_value(f"DH {stats.get('net_salary', stats['total_salary']):.2f}")

        # Table
        cols = ["UID", "Employee Name", "Date", "Entry Time",
                "Exit Time", "Worked Hours", "Hourly Rate", "Total Salary", "Late"]

        self._table.setRowCount(0)
        for _, row in df.iterrows():
            r = self._table.rowCount()
            self._table.insertRow(r)
            for c, col in enumerate(cols):
                raw = row.get(col, "")
                val = str(raw) if raw is not None and str(raw) != "nan" else ""
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == "Late" and val.upper() == "YES":
                    item.setForeground(QColor(AMBER))
                    item.setBackground(QColor("#FFF4E5"))
                self._table.setItem(r, c, item)

        self._table.viewport().update()

    def _clear_filters(self):
        today = date.today()
        self._month_combo.setCurrentIndex(today.month - 1)
        self._year_combo.setCurrentText(str(today.year))
        self._uid_input.clear()
        self._name_input.clear()
        all_index = self._late_combo.findData("All")
        if all_index >= 0:
            self._late_combo.setCurrentIndex(all_index)
        self.refresh()

    def _refresh_dynamic_translations(self):
        for card in (
            self._card_travailles,
            self._card_absents,
            self._card_late,
            self._card_salary,
            self._card_advances,
            self._card_primes,
            self._card_net,
        ):
            card.refresh_translation()
