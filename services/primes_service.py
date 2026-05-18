import logging
from datetime import datetime

import pandas as pd

from utils.file_utils import load_xlsx, save_xlsx
from utils.time_utils import now_date_str

logger = logging.getLogger(__name__)

PRIMES_FILE = "primes.xlsx"

COLUMNS = ["UID", "Employee Name", "Amount", "Date", "Note", "Month", "Year"]


def _load_df() -> pd.DataFrame:
    return load_xlsx(PRIMES_FILE, COLUMNS)


def _save_df(df: pd.DataFrame):
    save_xlsx(PRIMES_FILE, df)


def get_all_primes() -> pd.DataFrame:
    return _load_df()


def get_primes_for_month(month_name: str, year: str) -> pd.DataFrame:
    df = _load_df()
    if df.empty:
        return df
    return df[
        (df["Month"].astype(str) == str(month_name)) &
        (df["Year"].astype(str) == str(year))
    ].copy()


def get_total_primes(uid: str, month_name: str, year: str) -> float:
    df = get_primes_for_month(month_name, year)
    if df.empty:
        return 0.0
    subset = df[df["UID"].astype(str) == str(uid)]
    return round(pd.to_numeric(subset["Amount"], errors="coerce").sum(), 2)


def add_prime(uid: str, employee_name: str, amount: float, note: str = "") -> tuple[bool, str]:
    try:
        df = _load_df()
        date_str = now_date_str()
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        month = date_obj.strftime("%B")
        year  = date_obj.strftime("%Y")

        # Clean UID: remove duplicates and extra spaces
        uid_parts = uid.split()
        uid_clean = uid_parts[0] if uid_parts else uid

        new_row = pd.DataFrame(
            [[uid_clean, employee_name, str(amount), date_str, note, month, year]],
            columns=COLUMNS,
        )
        df = pd.concat([df, new_row], ignore_index=True)
        _save_df(df)
        logger.info("Prime added for %s (%s): %s DH", employee_name, uid_clean, amount)
        return True, f"Prime of {amount} DH added for {employee_name}."
    except Exception as e:
        logger.error("Error adding prime: %s", e)
        return False, f"Error: {e}"


def delete_prime(index: int) -> tuple[bool, str]:
    try:
        df = _load_df()
        if index < 0 or index >= len(df):
            return False, "Invalid record index."
        employee_name = df.iloc[index]["Employee Name"]
        df = df.drop(index).reset_index(drop=True)
        _save_df(df)
        logger.info("Prime deleted for %s", employee_name)
        return True, "Prime deleted."
    except Exception as e:
        logger.error("Error deleting prime: %s", e)
        return False, f"Error: {e}"