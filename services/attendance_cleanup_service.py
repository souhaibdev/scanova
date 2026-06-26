import logging
from datetime import datetime, date
from typing import Optional

import pandas as pd

from models.attendance_record import AttendanceRecord
from utils.file_utils import load_xlsx, save_xlsx
from utils.storage import ATTENDANCE_FILE

logger = logging.getLogger(__name__)


def should_keep_month(month_key: str, current_date: Optional[date] = None) -> bool:
    """Return True when a month key should be retained."""
    if current_date is None:
        current_date = date.today()

    try:
        month_dt = datetime.strptime(month_key, "%Y-%m").date()
    except ValueError:
        return False

    current_year, current_month = current_date.year, current_date.month
    previous_year = current_year if current_month > 1 else current_year - 1
    previous_month = current_month - 1 if current_month > 1 else 12

    keep_months = {
        (current_year, current_month),
        (previous_year, previous_month),
    }
    return (month_dt.year, month_dt.month) in keep_months


def cleanup_old_attendance_months() -> int:
    """Delete attendance rows for months older than the previous month using SQL-style filtering."""
    try:
        df = load_xlsx(ATTENDANCE_FILE, AttendanceRecord.columns())
        if df.empty:
            return 0

        current_date = date.today()
        current_month_key = current_date.strftime("%Y-%m")
        current_year, current_month = current_date.year, current_date.month
        previous_year = current_year if current_month > 1 else current_year - 1
        previous_month = current_month - 1 if current_month > 1 else 12

        months_to_keep = {
            current_month_key,
            f"{previous_year:04d}-{previous_month:02d}",
        }

        before_count = len(df)
        df = df[df["Date"].astype(str).str.slice(0, 7).isin(months_to_keep)]
        deleted_count = before_count - len(df)

        if deleted_count > 0:
            save_xlsx(ATTENDANCE_FILE, df)
            logger.info("Deleted %d attendance records from older months.", deleted_count)
        else:
            logger.info("No attendance records deleted during monthly cleanup.")
        return deleted_count
    except Exception as exc:
        logger.exception("Attendance monthly cleanup failed: %s", exc)
        return 0
