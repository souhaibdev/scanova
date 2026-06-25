# import os

# from PyQt6.QtWidgets import (
#     QWidget, QVBoxLayout, QHBoxLayout, QLabel,
#     QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
#     QHeaderView, QFrame, QTextEdit, QFileDialog, QMessageBox,
#     QSizePolicy
# )
# from PyQt6.QtCore import Qt
# from PyQt6.QtGui import QFont

# import pandas as pd

# from services import notes_service
# from utils.file_utils import IMAGES_DIR


# ACCENT     = "#2B79FF"
# BG_CARD    = "#FFFFFF"
# BG_PAGE    = "#F0F2F5"
# TEXT_MAIN  = "#111111"
# TEXT_MUTED = "#888888"
# BORDER     = "#E4EAFF"


# STYLESHEET = f"""
# QWidget {{
#     background: {BG_PAGE};
#     color: {TEXT_MAIN};
#     font-family: 'Segoe UI';
# }}
# QLineEdit, QTextEdit {{
#     background: {BG_CARD};
#     border: 1.5px solid {BORDER};
#     border-radius: 8px;
#     padding: 6px 10px;
#     font-size: 13px;
#     color: {TEXT_MAIN};
# }}
# QLineEdit:focus, QTextEdit:focus {{
#     border-color: {ACCENT};
# }}
# QFrame#detailCard {{
#     background: {BG_CARD};
#     border: 1.5px solid {BORDER};
#     border-radius: 12px;
# }}
# QPushButton {{
#     background: {BG_CARD};
#     border: 1.5px solid {BORDER};
#     border-radius: 8px;
#     padding: 6px 14px;
#     font-size: 13px;
#     font-weight: 600;
#     color: {TEXT_MAIN};
# }}
# QPushButton:hover {{
#     background: #EBF2FF;
#     border-color: {ACCENT};
#     color: {ACCENT};
# }}
# QPushButton#addBtn {{
#     background: {ACCENT};
#     border-color: {ACCENT};
#     color: #FFFFFF;
# }}
# QPushButton#addBtn:hover {{
#     background: #1A65E0;
# }}
# QTableWidget {{
#     background: {BG_CARD};
#     border: 1.5px solid {BORDER};
#     border-radius: 12px;
#     gridline-color: {BORDER};
#     font-size: 13px;
# }}
# QTableWidget::item {{
#     padding: 8px 12px;
# }}
# QTableWidget::item:selected {{
#     background: #EBF2FF;
#     color: {TEXT_MAIN};
# }}
# QHeaderView::section {{
#     background: #F5F8FF;
#     color: {TEXT_MUTED};
#     font-size: 11px;
#     font-weight: 600;
#     padding: 8px 12px;
#     border: none;
#     border-bottom: 1px solid {BORDER};
#     text-transform: uppercase;
#     letter-spacing: 0.4px;
# }}
# QScrollBar:vertical {{
#     width: 6px;
#     background: transparent;
# }}
# QScrollBar::handle:vertical {{
#     background: {BORDER};
#     border-radius: 3px;
# }}
# """


# class NotesPage(QWidget):
#     """Notes management — add, view, detail with optional images."""

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setStyleSheet(STYLESHEET)
#         self._selected_image_path: str = ""
#         self._build_ui()
#         self.refresh()

#     # ── Build ─────────────────────────────────────────────────────────

#     def _build_ui(self):
#         root = QVBoxLayout(self)
#         root.setContentsMargins(20, 20, 20, 20)
#         root.setSpacing(14)

#         # Title
#         title = QLabel("Notes")
#         title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
#         title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
#         root.addWidget(title)

#         # Body: list (left) + detail form (right)
#         body = QHBoxLayout()
#         body.setSpacing(16)
#         root.addLayout(body, stretch=1)

#         # ── Notes list ────────────────────────────
#         self._table = QTableWidget(0, 2)
#         self._table.setHorizontalHeaderLabels(["Title", "Date"])
#         self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
#         self._table.verticalHeader().setVisible(False)
#         self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
#         self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
#         self._table.itemSelectionChanged.connect(self._on_select)
#         body.addWidget(self._table, stretch=2)

#         # ── Detail / Add form ─────────────────────
#         detail_card = QFrame()
#         detail_card.setObjectName("detailCard")
#         detail_card.setFixedWidth(280)
#         detail_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

#         form = QVBoxLayout(detail_card)
#         form.setContentsMargins(16, 16, 16, 16)
#         form.setSpacing(8)

#         # Card title
#         card_title = QLabel("Note Details")
#         card_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
#         card_title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
#         form.addWidget(card_title)

#         # Title input
#         form.addWidget(self._muted_label("Title"))
#         self._title_input = QLineEdit()
#         self._title_input.setPlaceholderText("Note title...")
#         form.addWidget(self._title_input)

#         # Content input
#         form.addWidget(self._muted_label("Content"))
#         self._content_input = QTextEdit()
#         self._content_input.setPlaceholderText("Write your note here...")
#         self._content_input.setMinimumHeight(140)
#         form.addWidget(self._content_input, stretch=1)

#         # Image label
#         self._image_label = QLabel("No image selected")
#         self._image_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
#         self._image_label.setWordWrap(True)
#         form.addWidget(self._image_label)

#         # Buttons row
#         btn_row = QHBoxLayout()
#         btn_row.setSpacing(8)

#         btn_browse = QPushButton("Browse Image")
#         btn_browse.clicked.connect(self._browse_image)
#         btn_row.addWidget(btn_browse)

#         btn_add = QPushButton("Add Note")
#         btn_add.setObjectName("addBtn")
#         btn_add.clicked.connect(self._add_note)
#         btn_row.addWidget(btn_add)

#         btn_clear = QPushButton("Clear")
#         btn_clear.clicked.connect(self._clear_form)
#         btn_row.addWidget(btn_clear)

#         form.addLayout(btn_row)

#         # Date label
#         self._date_label = QLabel("")
#         self._date_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; background: transparent;")
#         form.addWidget(self._date_label)

#         body.addWidget(detail_card, stretch=0)

#     def _muted_label(self, text: str) -> QLabel:
#         lbl = QLabel(text)
#         lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; background: transparent;")
#         return lbl

#     # ── Refresh ───────────────────────────────────────────────────────

#     def refresh(self):
#         self._table.setRowCount(0)
#         df = notes_service.get_all_notes()
#         for idx, row in df.iterrows():
#             r = self._table.rowCount()
#             self._table.insertRow(r)
#             for c, val in enumerate([
#                 str(row["Title"]) if pd.notna(row["Title"]) else "",
#                 str(row["Date"])  if pd.notna(row["Date"])  else "",
#             ]):
#                 item = QTableWidgetItem(val)
#                 item.setData(Qt.ItemDataRole.UserRole, idx)  # store original index
#                 item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
#                 self._table.setItem(r, c, item)

#     def _on_select(self):
#         rows = self._table.selectedItems()
#         if not rows:
#             return
#         # Retrieve original df index stored in column 0
#         idx = self._table.item(self._table.currentRow(), 0).data(Qt.ItemDataRole.UserRole)
#         note = notes_service.get_note_by_index(idx)
#         if note is None:
#             return
#         self._title_input.setText(note["title"])
#         self._content_input.setPlainText(note["content"])
#         self._date_label.setText(f"Date: {note['date']}")
#         self._image_label.setText(f"Image: {note['image_path']}" if note["image_path"] else "No image")

#     # ── Actions ───────────────────────────────────────────────────────

#     def _browse_image(self):
#         path, _ = QFileDialog.getOpenFileName(
#             self,
#             "Select Image",
#             "",
#             "Images (*.png *.jpg *.jpeg *.gif *.bmp)"
#         )
#         if path:
#             self._selected_image_path = path
#             self._image_label.setText(os.path.basename(path))

#     def _add_note(self):
#         title   = self._title_input.text().strip()
#         content = self._content_input.toPlainText().strip()
#         if not title or not content:
#             QMessageBox.warning(self, "Validation", "Title and content are required.")
#             return
#         ok, msg = notes_service.add_note(title, content, self._selected_image_path or None)
#         if ok:
#             self.refresh()
#             self._clear_form()
#             QMessageBox.information(self, "Success", msg)
#         else:
#             QMessageBox.warning(self, "Error", msg)

#     def _clear_form(self):
#         self._title_input.clear()
#         self._content_input.clear()
#         self._image_label.setText("No image selected")
#         self._date_label.setText("")
#         self._selected_image_path = ""




"""
ui/notes_page.py
─────────────────
Advances / Notes page:
  • Left  : searchable employee list (live filter, no button)
  • Right : advance form (amount + note) + history table
  • Click on history row → fills form fields
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QMessageBox, QSizePolicy, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from services.advances_service import get_all_advances, add_advance, delete_advance
from services import employee_service
from translation_manager import TranslationManager

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


class NotesPage(QWidget):
    """Advances / Notes page with live employee search."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._translator = TranslationManager.instance()
        self.setStyleSheet(STYLESHEET)
        self._selected_uid: str = ""
        self._selected_name: str = ""
        self._selected_history_index: int = -1
        self._all_employees: list[tuple[str, str]] = []
        self._build_ui()
        self._translator.language_changed.connect(self._refresh_dynamic_translations)
        self.refresh()

    # ── Build ─────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        title = QLabel(self._translator.t("notes.title"))
        self._translator.bind_text(title, "notes.title")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        root.addWidget(title)

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

        lbl = QLabel(self._translator.t("notes.select_employee"))
        self._translator.bind_text(lbl, "notes.select_employee")
        lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        ll.addWidget(lbl)

        self._search_input = QLineEdit()
        self._translator.bind_placeholder(self._search_input, "notes.search.placeholder")
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

        self._selected_lbl = QLabel(self._translator.t("notes.selected.select_employee"))
        self._selected_lbl.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._selected_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        right.addWidget(self._selected_lbl)

        # Form card
        form_card = QFrame()
        form_card.setObjectName("card")
        fl = QHBoxLayout(form_card)
        fl.setContentsMargins(16, 14, 16, 14)
        fl.setSpacing(12)

        fl.addWidget(self._muted("notes.field.amount"))
        self._amount_input = QLineEdit()
        self._translator.bind_placeholder(self._amount_input, "notes.placeholder.amount")
        self._amount_input.setFixedWidth(110)
        fl.addWidget(self._amount_input)

        fl.addWidget(self._muted("notes.field.note"))
        self._note_input = QLineEdit()
        self._translator.bind_placeholder(self._note_input, "notes.placeholder.note")
        fl.addWidget(self._note_input, stretch=1)

        self._save_btn = QPushButton(self._translator.t("notes.button.save"))
        self._translator.bind_text(self._save_btn, "notes.button.save")
        self._save_btn.setObjectName("saveBtn")
        self._save_btn.clicked.connect(self._save_advance)
        fl.addWidget(self._save_btn)

        self._del_btn = QPushButton(self._translator.t("notes.button.delete"))
        self._translator.bind_text(self._del_btn, "notes.button.delete")
        self._del_btn.setObjectName("delBtn")
        self._del_btn.clicked.connect(self._delete_advance)
        self._del_btn.setVisible(False)
        fl.addWidget(self._del_btn)

        btn_clear = QPushButton(self._translator.t("notes.button.clear"))
        self._translator.bind_text(btn_clear, "notes.button.clear")
        btn_clear.clicked.connect(self._clear_form)
        fl.addWidget(btn_clear)

        right.addWidget(form_card)

        hist_lbl = QLabel(self._translator.t("notes.history.title"))
        self._translator.bind_text(hist_lbl, "notes.history.title")
        hist_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hist_lbl.setStyleSheet(f"color: {TEXT_MAIN}; background: transparent;")
        right.addWidget(hist_lbl)

        cols = [
            "notes.table.uid",
            "notes.table.employee_name",
            "notes.table.amount",
            "notes.table.date",
            "notes.table.note",
            "notes.table.month",
            "notes.table.year",
        ]
        self._hist_table = QTableWidget(0, len(cols))
        self._translator.bind_table_headers(self._hist_table, cols)
        self._hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._hist_table.verticalHeader().setVisible(False)
        self._hist_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._hist_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._hist_table.itemSelectionChanged.connect(self._on_history_select)
        right.addWidget(self._hist_table, stretch=1)

        body.addLayout(right, stretch=1)

    def _muted(self, text: str) -> QLabel:
        lbl = QLabel(self._translator.t(text))
        self._translator.bind_text(lbl, text)
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
        previous_uid = self._selected_uid
        filtered = [
            (uid, name) for uid, name in self._all_employees
            if q in name.lower() or q in uid.lower()
        ] if q else self._all_employees

        self._emp_table.blockSignals(True)
        self._emp_table.setRowCount(0)
        
        # Add "All Employees" option at the top
        r = self._emp_table.rowCount()
        self._emp_table.insertRow(r)
        all_item = QTableWidgetItem(self._translator.t("notes.selected.all_employees"))
        all_item.setData(Qt.ItemDataRole.UserRole, "*all*")
        all_item.setToolTip(self._translator.t("notes.tooltip.show_all"))
        self._emp_table.setItem(r, 0, all_item)
        
        # Add filtered employees
        for uid, name in filtered:
            r = self._emp_table.rowCount()
            self._emp_table.insertRow(r)
            item = QTableWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, uid)
            item.setToolTip(f"UID: {uid}")
            self._emp_table.setItem(r, 0, item)
            if uid == previous_uid:
                self._emp_table.selectRow(r)

        if previous_uid == "*all*":
            self._emp_table.selectRow(0)
        self._emp_table.blockSignals(False)

    def _load_history(self, uid_filter: str = ""):
        self._hist_table.setRowCount(0)
        
        # Only load history if an employee is selected
        if not uid_filter or not uid_filter.strip():
            return
        
        df = get_all_advances()
        if df.empty:
            return
        
        # Filter by selected employee UID or show all if "*all*"
        if uid_filter != "*all*":
            df = df[df["UID"].astype(str) == uid_filter]

        src_cols     = ["UID", "Employee Name", "Amount", "Date", "Note", "Month", "Year"]

        for idx, row in df.iterrows():
            r = self._hist_table.rowCount()
            self._hist_table.insertRow(r)
            for c, col in enumerate(src_cols):
                val = str(row.get(col, ""))
                item = QTableWidgetItem(val)
                item.setData(Qt.ItemDataRole.UserRole, idx)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
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
            self._selected_lbl.setText(self._translator.t("notes.selected.all_employees"))
        else:
            self._selected_lbl.setText(f"{self._selected_name}")
        self._selected_lbl.setStyleSheet(
            f"color: {ACCENT}; font-size: 14px; font-weight: 700; background: transparent;"
        )
        self._load_history(uid_filter=self._selected_uid)
        self._clear_form()

    # ── History selection ──────────────────────────────────────────────

    def _on_history_select(self):
        items = self._hist_table.selectedItems()
        if not items:
            self._del_btn.setVisible(False)
            return
        row = self._hist_table.currentRow()

        uid_item    = self._hist_table.item(row, 0)
        name_item   = self._hist_table.item(row, 1)
        amount_item = self._hist_table.item(row, 2)
        note_item   = self._hist_table.item(row, 4)

        self._selected_history_index = uid_item.data(Qt.ItemDataRole.UserRole) if uid_item else -1

        # Fill form with row data
        self._amount_input.setText(amount_item.text() if amount_item else "")
        self._note_input.setText(note_item.text() if note_item else "")

        # Sync employee banner
        uid  = uid_item.text()  if uid_item  else ""
        name = name_item.text() if name_item else ""
        if uid:
            self._selected_uid  = uid
            self._selected_name = name
            self._selected_lbl.setText(f"{name}")
            self._selected_lbl.setStyleSheet(
                f"color: {ACCENT}; font-size: 14px; font-weight: 700; background: transparent;"
            )

        self._del_btn.setVisible(True)

    # ── Actions ───────────────────────────────────────────────────────

    def _save_advance(self):
        if not self._selected_uid or self._selected_uid == "*all*":
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("notes.validation.select_employee"),
            )
            return
        amount_str = self._amount_input.text().strip()
        note       = self._note_input.text().strip()
        if not amount_str:
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("notes.validation.enter_amount"),
            )
            return
        try:
            amount = float(amount_str)
        except ValueError:
            QMessageBox.warning(
                self,
                self._translator.t("common.validation"),
                self._translator.t("notes.validation.amount_number"),
            )
            return

        ok, msg = add_advance(self._selected_uid, self._selected_name, amount, note)
        if ok:
            QMessageBox.information(self, self._translator.t("common.success"), msg)
            self._clear_form()
            self._load_history(uid_filter=self._selected_uid)
        else:
            QMessageBox.warning(self, self._translator.t("common.error"), msg)

    def _delete_advance(self):
        if self._selected_history_index < 0:
            return
        reply = QMessageBox.question(
            self,
            self._translator.t("common.confirm"),
            self._translator.t("notes.confirm.delete"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        ok, msg = delete_advance(self._selected_history_index)
        if ok:
            self._clear_form()
            self._load_history(uid_filter=self._selected_uid)
        else:
            QMessageBox.warning(self, self._translator.t("common.error"), msg)

    def _clear_form(self):
        self._amount_input.clear()
        self._note_input.clear()
        self._selected_history_index = -1
        self._del_btn.setVisible(False)
        self._hist_table.clearSelection()

    def _refresh_dynamic_translations(self):
        if not self._selected_uid:
            self._selected_lbl.setText(self._translator.t("notes.selected.select_employee"))
            self._selected_lbl.setStyleSheet(f"color: {TEXT_MUTED}; background: transparent;")
        elif self._selected_uid == "*all*":
            self._selected_name = self._translator.t("notes.selected.all_employees")
            self._selected_lbl.setText(self._selected_name)
        self._filter_employees(self._search_input.text())
