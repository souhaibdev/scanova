# import logging
# import os
# import shutil

# import pandas as pd

# from models.note import Note
# from utils.file_utils import load_xlsx, save_xlsx, IMAGES_DIR
# from utils.time_utils import now_datetime_str

# logger = logging.getLogger(__name__)

# NOTES_FILE = "notes.xlsx"


# def _load_df() -> pd.DataFrame:
#     return load_xlsx(NOTES_FILE, Note.columns())


# def _save_df(df: pd.DataFrame):
#     save_xlsx(NOTES_FILE, df)


# def get_all_notes() -> pd.DataFrame:
#     return _load_df()


# def add_note(title: str, content: str, image_src: str = None) -> tuple[bool, str]:
#     if not title.strip() or not content.strip():
#         return False, "Title and content are required."

#     image_dest = ""
#     if image_src and os.path.isfile(image_src):
#         fname = os.path.basename(image_src)
#         image_dest = os.path.join(IMAGES_DIR, fname)
#         if not os.path.exists(image_dest):
#             shutil.copy2(image_src, image_dest)
#         image_dest = fname  # store just the filename

#     note = Note(
#         title=title.strip(),
#         date=now_datetime_str(),
#         content=content.strip(),
#         image_path=image_dest if image_dest else None,
#     )

#     df = _load_df()
#     new_row = pd.DataFrame([note.to_row()], columns=Note.columns())
#     df = pd.concat([df, new_row], ignore_index=True)
#     _save_df(df)
#     logger.info("Note added: %s", title)
#     return True, "Note added successfully."


# def get_note_by_index(idx: int) -> dict | None:
#     df = _load_df()
#     if 0 <= idx < len(df):
#         row = df.iloc[idx]
#         return {
#             "title": str(row["Title"]),
#             "date": str(row["Date"]),
#             "content": str(row["Content"]),
#             "image_path": str(row["Image Path"]) if pd.notna(row["Image Path"]) else "",
#         }
#     return None







"""
services/advances_service.py
─────────────────────────────
Manages employee advances stored in advances.xlsx
 
CSV columns:
    UID | Employee Name | Amount | Date | Note | Month | Year
"""
 
from __future__ import annotations
  
import logging
from datetime import date
  
import pandas as pd
  
from translation_manager import TranslationManager
from utils.file_utils import load_xlsx, save_xlsx
  
logger = logging.getLogger(__name__)
  
ADVANCES_FILE = "advances.xlsx"
  
COLUMNS = ["UID", "Employee Name", "Amount", "Date", "Note", "Month", "Year"]
  
_translator = TranslationManager.instance()
 
 
# ── Internal helpers ──────────────────────────────────────────────────────────
 
def _load_df() -> pd.DataFrame:
    return load_xlsx(ADVANCES_FILE, COLUMNS)
 
 
def _save_df(df: pd.DataFrame):
    save_xlsx(ADVANCES_FILE, df)
 
 
# ── Public API ────────────────────────────────────────────────────────────────
 
def get_all_advances() -> pd.DataFrame:
    """Return all advances."""
    return _load_df()
 
 
def get_advances_for_month(month: int, year: int) -> pd.DataFrame:
    """Return advances whose Month/Year match."""
    df = _load_df()
    if df.empty:
        return df
    df["Month"] = pd.to_numeric(df["Month"], errors="coerce")
    df["Year"]  = pd.to_numeric(df["Year"],  errors="coerce")
    return df[(df["Month"] == month) & (df["Year"] == year)].copy()
 
 
def get_total_advances(uid: str, month: int, year: int) -> float:
    """Total advances for a given employee in a given month."""
    df = get_advances_for_month(month, year)
    if df.empty:
        return 0.0
    emp = df[df["UID"].astype(str) == str(uid)]
    return round(pd.to_numeric(emp["Amount"], errors="coerce").sum(), 2)
 
 
def add_advance(uid: str, employee_name: str, amount: float, note: str = "") -> tuple[bool, str]:
    """Record a new advance for an employee."""
    if amount <= 0:
        return False, _translator.t("service.amount_must_be_positive")
 
    today = date.today()
    new_row = {
        "UID":           str(uid),
        "Employee Name": str(employee_name),
        "Amount":        str(round(amount, 2)),
        "Date":          str(today),
        "Note":          str(note),
        "Month":         str(today.month),
        "Year":          str(today.year),
    }
 
    df = _load_df()
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    _save_df(df)
    logger.info("Advance recorded: %s DH for %s (%s)", amount, employee_name, uid)
    return True, _translator.t("service.advance_recorded", amount=amount, employee_name=employee_name)
 
 
def delete_advance(index: int) -> tuple[bool, str]:
    """Delete an advance by its DataFrame index."""
    df = _load_df()
    if index < 0 or index >= len(df):
        return False, _translator.t("service.invalid_index")
    df = df.drop(index=index).reset_index(drop=True)
    _save_df(df)
    logger.info("Advance deleted at index %d", index)
    return True, _translator.t("service.advance_deleted")
