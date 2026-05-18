from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem,
    QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.attendance_service import get_dashboard_stats


ACCENT      = "#2B79FF"
BG_CARD     = "#FFFFFF"
BG_PAGE     = "#F0F2F5"
TEXT_MAIN   = "#111111"
TEXT_MUTED  = "#888888"
BORDER      = "#E4EAFF"


STYLESHEET = f"""
QWidget {{
    background: {BG_PAGE};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI';
}}
QFrame#kpiCard {{
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


class KpiCard(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setObjectName("kpiCard")
        self.setMinimumWidth(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        lbl_title.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent; border: none;")
        layout.addWidget(lbl_title)

        self._value_label = QLabel("0")
        self._value_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        self._value_label.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent; border: none;")
        layout.addWidget(self._value_label)

    def set_value(self, text: str):
        self._value_label.setText(text)


class DashboardPage(QWidget):
    """Real-time dashboard showing today's attendance summary."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLESHEET)
        self._kpi_cards: dict[str, KpiCard] = {}
        self._build_ui()
        self.refresh()

    # ── Build ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        kpi_defs = [
            ("total_employees", "Total Employees"),
            ("present_today",   "Present Today"),
            ("absent_today",    "Absent Today"),       # ← بدلنا worked hours
            ("late_today",      "Late Today"),
        ]
        for key, label in kpi_defs:
            card = KpiCard(label)
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            kpi_row.addWidget(card)
            self._kpi_cards[key] = card

        root.addLayout(kpi_row)

        section_lbl = QLabel("Late Employees Today")
        section_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        section_lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(section_lbl)

        cols = ["Name", "UID", "Entry Time"]
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(False)
        root.addWidget(self._table, stretch=1)

    # ── Refresh ───────────────────────────────────────────────────────

    def refresh(self):
        stats = get_dashboard_stats()

        self._kpi_cards["total_employees"].set_value(str(stats["total_employees"]))
        self._kpi_cards["present_today"].set_value(str(stats["present_today"]))
        self._kpi_cards["absent_today"].set_value(str(stats["absent_today"]))   # ← بدلنا
        self._kpi_cards["late_today"].set_value(str(stats["late_today"]))
        # ← مسحنا total_salary و total_worked_hours

        late_list = stats["late_employees"]
        self._table.setRowCount(0)

        for emp in late_list:
            row = self._table.rowCount()
            self._table.insertRow(row)
            for col, value in enumerate([emp["name"], emp["uid"], emp["entry"]]):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._table.setItem(row, col, item)

        self._table.viewport().update()
        self._table.repaint()