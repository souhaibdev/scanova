import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QTextEdit, QFileDialog, QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import pandas as pd

from services import notes_service
from utils.file_utils import IMAGES_DIR


ACCENT     = "#2B79FF"
BG_CARD    = "#FFFFFF"
BG_PAGE    = "#F0F2F5"
TEXT_MAIN  = "#111111"
TEXT_MUTED = "#888888"
BORDER     = "#E4EAFF"


STYLESHEET = f"""
QWidget {{
    background: {BG_PAGE};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI';
}}
QLineEdit, QTextEdit {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 13px;
    color: {TEXT_MAIN};
}}
QLineEdit:focus, QTextEdit:focus {{
    border-color: {ACCENT};
}}
QFrame#detailCard {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
}}
QPushButton {{
    background: {BG_CARD};
    border: 1.5px solid {BORDER};
    border-radius: 8px;
    padding: 6px 14px;
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


class NotesPage(QWidget):
    """Notes management — add, view, detail with optional images."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(STYLESHEET)
        self._selected_image_path: str = ""
        self._build_ui()
        self.refresh()

    # ── Build ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # Title
        title = QLabel("Notes")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

        # Body: list (left) + detail form (right)
        body = QHBoxLayout()
        body.setSpacing(16)
        root.addLayout(body, stretch=1)

        # ── Notes list ────────────────────────────
        self._table = QTableWidget(0, 2)
        self._table.setHorizontalHeaderLabels(["Title", "Date"])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.itemSelectionChanged.connect(self._on_select)
        body.addWidget(self._table, stretch=2)

        # ── Detail / Add form ─────────────────────
        detail_card = QFrame()
        detail_card.setObjectName("detailCard")
        detail_card.setFixedWidth(280)
        detail_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        form = QVBoxLayout(detail_card)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(8)

        # Card title
        card_title = QLabel("Note Details")
        card_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        card_title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        form.addWidget(card_title)

        # Title input
        form.addWidget(self._muted_label("Title"))
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Note title...")
        form.addWidget(self._title_input)

        # Content input
        form.addWidget(self._muted_label("Content"))
        self._content_input = QTextEdit()
        self._content_input.setPlaceholderText("Write your note here...")
        self._content_input.setMinimumHeight(140)
        form.addWidget(self._content_input, stretch=1)

        # Image label
        self._image_label = QLabel("No image selected")
        self._image_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        self._image_label.setWordWrap(True)
        form.addWidget(self._image_label)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_browse = QPushButton("Browse Image")
        btn_browse.clicked.connect(self._browse_image)
        btn_row.addWidget(btn_browse)

        btn_add = QPushButton("Add Note")
        btn_add.setObjectName("addBtn")
        btn_add.clicked.connect(self._add_note)
        btn_row.addWidget(btn_add)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self._clear_form)
        btn_row.addWidget(btn_clear)

        form.addLayout(btn_row)

        # Date label
        self._date_label = QLabel("")
        self._date_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: transparent;")
        form.addWidget(self._date_label)

        body.addWidget(detail_card, stretch=0)

    def _muted_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
        return lbl

    # ── Refresh ───────────────────────────────────────────────────────

    def refresh(self):
        self._table.setRowCount(0)
        df = notes_service.get_all_notes()
        for idx, row in df.iterrows():
            r = self._table.rowCount()
            self._table.insertRow(r)
            for c, val in enumerate([
                str(row["Title"]) if pd.notna(row["Title"]) else "",
                str(row["Date"])  if pd.notna(row["Date"])  else "",
            ]):
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, idx)  # store original index
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                self._table.setItem(r, c, item)

    def _on_select(self):
        rows = self._table.selectedItems()
        if not rows:
            return
        # Retrieve original df index stored in column 0
        idx = self._table.item(self._table.currentRow(), 0).data(Qt.ItemDataRole.UserRole)
        note = notes_service.get_note_by_index(idx)
        if note is None:
            return
        self._title_input.setText(note["title"])
        self._content_input.setPlainText(note["content"])
        self._date_label.setText(f"Date: {note['date']}")
        self._image_label.setText(f"Image: {note['image_path']}" if note["image_path"] else "No image")

    # ── Actions ───────────────────────────────────────────────────────

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if path:
            self._selected_image_path = path
            self._image_label.setText(os.path.basename(path))

    def _add_note(self):
        title   = self._title_input.text().strip()
        content = self._content_input.toPlainText().strip()
        if not title or not content:
            QMessageBox.warning(self, "Validation", "Title and content are required.")
            return
        ok, msg = notes_service.add_note(title, content, self._selected_image_path or None)
        if ok:
            self.refresh()
            self._clear_form()
            QMessageBox.information(self, "Success", msg)
        else:
            QMessageBox.warning(self, "Error", msg)

    def _clear_form(self):
        self._title_input.clear()
        self._content_input.clear()
        self._image_label.setText("No image selected")
        self._date_label.setText("")
        self._selected_image_path = ""