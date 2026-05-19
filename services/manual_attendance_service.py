"""
services/manual_attendance_service.py
──────────────────────────────────────
Manual entry/exit recording for employees who forgot to scan.
Reuses the same attendance.xlsx and AttendanceRecord columns.
"""

from __future__ import annotations
import logging
from datetime import date

import pandas as pd

from models.attendance_record import AttendanceRecord
from services.employee_service import get_all_employees, get_employee_by_uid
from utils.file_utils import load_xlsx, save_xlsx
from utils.time_utils import calc_worked_hours, is_late

logger = logging.getLogger(__name__)

from utils.storage import ATTENDANCE_FILE


def _load_df() -> pd.DataFrame:
    return load_xlsx(ATTENDANCE_FILE, AttendanceRecord.columns())


def _save_df(df: pd.DataFrame):
    save_xlsx(ATTENDANCE_FILE, df)


def add_manual_record(
    uid: str,
    date_str: str,
    entry_time: str,
    exit_time: str,
) -> tuple[bool, str]:
    """
    Add a manual attendance record for an employee.
    - No record today      → creates new row (entry only or full)
    - Entry but no exit    → fills in exit time on existing row
    - Already complete     → returns error
    Returns (success, message).
    """
    # ── Validate employee ─────────────────────────────────────────────
    employee = get_employee_by_uid(uid)
    if employee is None:
        return False, f"UID '{uid}' is not registered."

    # ── Validate entry time ───────────────────────────────────────────
    try:
        h_entry, m_entry = map(int, entry_time.split(":"))
    except Exception:
        return False, "Entry time must be in HH:MM format."

    entry_minutes = h_entry * 60 + m_entry

    # ── Validate exit time (optional) ─────────────────────────────────
    exit_minutes = None
    if exit_time and exit_time.strip():
        try:
            h_exit, m_exit = map(int, exit_time.split(":"))
        except Exception:
            return False, "Exit time must be in HH:MM format."

        exit_minutes = h_exit * 60 + m_exit

        if exit_minutes <= entry_minutes:
            return False, "Exit time must be after entry time."

        if (exit_minutes - entry_minutes) < 15:
            return False, "Minimum stay is 15 minutes."

    # ── Load attendance ───────────────────────────────────────────────
    df   = _load_df()
    mask = (
        (df["UID"].astype(str)  == str(uid)) &
        (df["Date"].astype(str) == date_str)
    )
    existing = df[mask]

    # ── Case 1: existing row — fill missing exit ───────────────────────
    if not existing.empty:
        last_idx = existing.index[-1]
        exit_val = str(df.at[last_idx, "Exit Time"]).strip()

        if exit_val and exit_val not in ("", "nan", "None"):
            return False, f"{employee.full_name} already has a complete record on {date_str}."

        if not exit_time or not exit_time.strip():
            return False, "This employee already has an entry. Please provide an exit time."

        existing_entry = str(df.at[last_idx, "Entry Time"]).strip()
        worked         = calc_worked_hours(existing_entry, exit_time)
        total_salary   = round(worked * employee.hourly_rate, 2)

        df.at[last_idx, "Exit Time"]    = exit_time
        df.at[last_idx, "Worked Hours"] = str(worked)
        df.at[last_idx, "Total Salary"] = str(total_salary)
        _save_df(df)

        logger.info(
            "Manual exit added: %s (%s) on %s — %s→%s | %.2fh | DH%.2f",
            employee.full_name, uid, date_str, existing_entry, exit_time, worked, total_salary,
        )
        return True, (
            f"Exit recorded for {employee.full_name} on {date_str} — "
            f"{existing_entry}→{exit_time} | {worked}h | DH{total_salary:.2f}"
        )

    # ── Case 2: no record — create new row ────────────────────────────
    late = is_late(entry_time, employee.expected_start_time)

    if exit_minutes is not None:
        worked       = calc_worked_hours(entry_time, exit_time)
        total_salary = round(worked * employee.hourly_rate, 2)
        worked_str   = str(worked)
        salary_str   = str(total_salary)
        exit_str     = exit_time
    else:
        worked       = None
        total_salary = None
        worked_str   = ""
        salary_str   = ""
        exit_str     = ""

    new_row = pd.DataFrame(
        [[
            uid,
            employee.full_name,
            date_str,
            entry_time,
            exit_str,
            worked_str,
            employee.hourly_rate,
            salary_str,
            "YES" if late else "NO",
        ]],
        columns=AttendanceRecord.columns(),
    )
    df = pd.concat([df, new_row], ignore_index=True)
    _save_df(df)

    if exit_minutes is not None:
        logger.info(
            "Manual record added: %s (%s) on %s — %s→%s | %.2fh | DH%.2f",
            employee.full_name, uid, date_str, entry_time, exit_time, worked, total_salary,
        )
        return True, (
            f"Record added for {employee.full_name} on {date_str} — "
            f"{entry_time}→{exit_time} | {worked}h | DH{total_salary:.2f}"
        )
    else:
        logger.info(
            "Manual entry recorded (no exit): %s (%s) on %s — %s",
            employee.full_name, uid, date_str, entry_time,
        )
        return True, (
            f"Entry recorded for {employee.full_name} on {date_str} "
            f"at {entry_time} (no exit time set)"
        )


def get_missing_employees(date_str: str = "") -> pd.DataFrame:
    """
    Returns employees who:
    - Have no record at all today  → Status: No Record
    - Have entry but no exit today → Status: Missing Exit
    """
    if not date_str:
        date_str = date.today().strftime("%Y-%m-%d")

    all_employees = get_all_employees()
    df            = _load_df()
    today_df      = df[df["Date"].astype(str) == date_str]

    rows = []
    for emp in all_employees:
        emp_records = today_df[today_df["UID"].astype(str) == emp.uid]

        if emp_records.empty:
            rows.append({
                "UID":           emp.uid,
                "CIN":           emp.cin,
                "Employee Name": emp.full_name,
                "Entry Time":    "",
                "Status":        "No Record",
            })
        else:
            last     = emp_records.iloc[-1]
            exit_val = str(last.get("Exit Time", "")).strip()
            if not exit_val or exit_val in ("", "nan", "None"):
                rows.append({
                    "UID":           emp.uid,
                    "CIN":           emp.cin,
                    "Employee Name": emp.full_name,
                    "Entry Time":    str(last.get("Entry Time", "")),
                    "Status":        "Missing Exit",
                })

    return pd.DataFrame(rows, columns=["UID", "CIN", "Employee Name", "Entry Time", "Status"])