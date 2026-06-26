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

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

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
    def __init__(self, label: str, accent: str, parent=None):
        super().__init__(parent)
        self.setObjectName("statCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        lbl = QLabel(label.upper())
        lbl.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 0.5px; background: transparent;"
        )
        lay.addWidget(lbl)

        self._val = QLabel("—")
        self._val.setStyleSheet(
            f"color: {accent}; font-size: 24px; font-weight: 700; background: transparent;"
        )
        lay.addWidget(self._val)

    def set_value(self, text: str):
        self._val.setText(text)


# ── Last 15 Days Report Page ──────────────────────────────────────────────────

class MonthlyReportPage(QWidget):
    """Rolling last 15 days attendance report with filters and stats."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLESHEET)
        self._build_ui()
        self.refresh()

    # ── Build ──────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ── Title ──
        title = QLabel("Last 15 Days Report")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

        # ── Filter row ──
        frow = QHBoxLayout()
        frow.setSpacing(10)

        # UID
        frow.addWidget(self._muted("UID:"))
        self._uid_input = QLineEdit()
        self._uid_input.setPlaceholderText("Filter UID...")
        self._uid_input.setFixedWidth(120)
        frow.addWidget(self._uid_input)

        # Name
        frow.addWidget(self._muted("Name:"))
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Filter name...")
        self._name_input.setFixedWidth(150)
        frow.addWidget(self._name_input)

        # Late
        frow.addWidget(self._muted("Late:"))
        self._late_combo = QComboBox()
        self._late_combo.addItems(["All", "YES", "NO"])
        self._late_combo.setFixedWidth(80)
        frow.addWidget(self._late_combo)

        # Buttons
        btn_apply = QPushButton("Apply")
        btn_apply.setObjectName("applyBtn")
        btn_apply.clicked.connect(self.refresh)
        frow.addWidget(btn_apply)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._clear_filters)
        frow.addWidget(btn_clear)

        frow.addStretch()
        root.addLayout(frow)

        # ── Stat cards row 1: attendance ──
        cards_row1 = QHBoxLayout()
        cards_row1.setSpacing(12)

        self._card_travailles = StatCard("Jours travaillés", GREEN)
        self._card_absents    = StatCard("Jours absents",    RED)
        self._card_late       = StatCard("Jours late",       AMBER)
        self._card_salary     = StatCard("Total Salary",     ACCENT)

        for card in (self._card_travailles, self._card_absents,
                     self._card_late, self._card_salary):
            cards_row1.addWidget(card)

        root.addLayout(cards_row1)

        # ── Stat cards row 2: advances / primes / net ──
        cards_row2 = QHBoxLayout()
        cards_row2.setSpacing(12)

        self._card_advances = StatCard("Total Advances", RED)
        self._card_primes   = StatCard("Total Primes",   GREEN)
        self._card_net      = StatCard("Net Salary",     ACCENT)

        for card in (self._card_advances, self._card_primes, self._card_net):
            cards_row2.addWidget(card)

        cards_row2.addStretch()
        root.addLayout(cards_row2)

        # ── Table ──
        cols = ["UID", "Employee Name", "Date", "Entry Time",
                "Exit Time", "Worked Hours", "Hourly Rate", "Total Salary", "Late"]
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        root.addWidget(self._table, stretch=1)

    def _muted(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; background: transparent;")
        return lbl

    # ── Data ───────────────────────────────────────────────────────────

    def refresh(self):
        from services.monthly_report_service import get_monthly_report_filtered

        result = get_monthly_report_filtered(
            uid_filter  = self._uid_input.text().strip(),
            name_filter = self._name_input.text().strip(),
            late_filter = self._late_combo.currentText(),
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
        self._uid_input.clear()
        self._name_input.clear()
        self._late_combo.setCurrentText("All")
        self.refresh()
