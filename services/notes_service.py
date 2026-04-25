import logging
import os
import shutil

import pandas as pd

from models.note import Note
from utils.file_utils import load_xlsx, save_xlsx, IMAGES_DIR
from utils.time_utils import now_datetime_str

logger = logging.getLogger(__name__)

NOTES_FILE = "notes.xlsx"


def _load_df() -> pd.DataFrame:
    return load_xlsx(NOTES_FILE, Note.columns())


def _save_df(df: pd.DataFrame):
    save_xlsx(NOTES_FILE, df)


def get_all_notes() -> pd.DataFrame:
    return _load_df()


def add_note(title: str, content: str, image_src: str = None) -> tuple[bool, str]:
    if not title.strip() or not content.strip():
        return False, "Title and content are required."

    image_dest = ""
    if image_src and os.path.isfile(image_src):
        fname = os.path.basename(image_src)
        image_dest = os.path.join(IMAGES_DIR, fname)
        if not os.path.exists(image_dest):
            shutil.copy2(image_src, image_dest)
        image_dest = fname  # store just the filename

    note = Note(
        title=title.strip(),
        date=now_datetime_str(),
        content=content.strip(),
        image_path=image_dest if image_dest else None,
    )

    df = _load_df()
    new_row = pd.DataFrame([note.to_row()], columns=Note.columns())
    df = pd.concat([df, new_row], ignore_index=True)
    _save_df(df)
    logger.info("Note added: %s", title)
    return True, "Note added successfully."


def get_note_by_index(idx: int) -> dict | None:
    df = _load_df()
    if 0 <= idx < len(df):
        row = df.iloc[idx]
        return {
            "title": str(row["Title"]),
            "date": str(row["Date"]),
            "content": str(row["Content"]),
            "image_path": str(row["Image Path"]) if pd.notna(row["Image Path"]) else "",
        }
    return None
