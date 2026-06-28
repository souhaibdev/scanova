import logging

import pandas as pd

from models.attendance_record import AttendanceRecord
from models.employee import Employee
from services.attendance_cleanup_service import cleanup_old_attendance_months
from services.employee_service import get_employee_by_uid
from translation_manager import TranslationManager
from utils.file_utils import load_xlsx, save_xlsx
from utils.storage import ATTENDANCE_FILE
from utils.time_utils import (
    now_date_str,
    now_time_str,
    calc_worked_hours,
    is_late,
    minutes_between,
)

logger = logging.getLogger(__name__)
MIN_STAY_MINUTES = 15  # minimum minutes between entry and exit
_translator = TranslationManager.instance()


def _load_df() -> pd.DataFrame:
    return load_xlsx(ATTENDANCE_FILE, AttendanceRecord.columns())


def _save_df(df: pd.DataFrame):
    save_xlsx(ATTENDANCE_FILE, df)


def _ensure_monthly_cleanup() -> None:
    """Run monthly cleanup once per process to keep current and previous months only."""
    try:
        cleanup_old_attendance_months()
    except Exception as exc:
        logger.exception("Monthly attendance cleanup failed: %s", exc)


def process_scan(uid: str) -> dict:
    """Process a UID scan. Returns a result dict for UI feedback."""
    logger.info("Processing scan for UID: %s", uid)
    _ensure_monthly_cleanup()

    if not uid or not uid.strip():
        logger.warning("Empty or whitespace-only UID received: %r", uid)
        return {
            "success": False,
            "message": _translator.t("service.invalid_uid"),
            "action": "invalid_uid",
            "uid": uid,
        }

    employee = get_employee_by_uid(uid)
    if employee is None:
        logger.warning("Unregistered UID scanned: %s", uid)
        return {
            "success": False,
            "message": _translator.t("service.uid_not_registered", uid=uid),
            "action": "unknown",
            "uid": uid,
        }

    logger.info("Employee found for UID %s: %s", uid, employee.full_name)

    today = now_date_str()
    current_time = now_time_str()
    df = _load_df()
    logger.info("Loaded attendance data: %d records", len(df))

    # Check for existing record today
    mask = (df["UID"].astype(str) == str(uid)) & (df["Date"].astype(str) == today)
    today_records = df[mask]

    if today_records.empty:
        # ── ENTRY ──────────────────────────────────────────────
        late = is_late(current_time, employee.expected_start_time)
        new_row = pd.DataFrame(
            [[uid, employee.full_name, today, current_time, "", "", employee.hourly_rate, "", "YES" if late else "NO"]],
            columns=AttendanceRecord.columns(),
        )
        df = pd.concat([df, new_row], ignore_index=True)
        _save_df(df)
        logger.info("ENTRY recorded for %s (%s)", employee.full_name, uid)
        return {
            "success": True,
            "action": "entry",
            "employee": employee.full_name,
            "uid": uid,
            "time": current_time,
            "late": late,
            "message": _translator.t("service.entry_recorded", employee=employee.full_name),
        }

    else:
        last_idx = today_records.index[-1]
        exit_val = str(df.at[last_idx, "Exit Time"]).strip()

        # Already checked out
        if exit_val and exit_val not in ("", "nan", "None"):
            logger.info("Already checked out today: %s (%s)", employee.full_name, uid)
            return {
                "success": False,
                "action": "already_done",
                "employee": employee.full_name,
                "uid": uid,
                "message": _translator.t("service.already_checked_out", employee=employee.full_name),
            }

        # ── EXIT — enforce 15-minute minimum ───────────────────
        entry_time_str = str(df.at[last_idx, "Entry Time"])
        mins_stayed = minutes_between(entry_time_str, current_time)

        if mins_stayed < MIN_STAY_MINUTES:
            remaining = MIN_STAY_MINUTES - mins_stayed
            logger.info(
                "Exit too soon for %s: only %d min elapsed", employee.full_name, mins_stayed
            )
            return {
                "success": False,
                "action": "too_soon",
                "employee": employee.full_name,
                "uid": uid,
                "message": _translator.t(
                    "service.exit_too_soon",
                    employee=employee.full_name,
                    mins_stayed=mins_stayed,
                    remaining=remaining,
                ),
            }

        worked = calc_worked_hours(entry_time_str, current_time)
        salary = worked * employee.hourly_rate

        df.at[last_idx, "Exit Time"] = current_time
        df.at[last_idx, "Worked Hours"] = str(worked)
        df.at[last_idx, "Total Salary"] = str(salary)
        _save_df(df)
        logger.info("EXIT recorded for %s (%s)", employee.full_name, uid)
        return {
            "success": True,
            "action": "exit",
            "employee": employee.full_name,
            "uid": uid,
            "time": current_time,
            "worked_hours": worked,
            "salary": salary,
            "message": _translator.t("service.exit_recorded", employee=employee.full_name, worked=worked, salary=salary),
        }


def get_attendance_df() -> pd.DataFrame:
    return _load_df()


def get_today_attendance() -> pd.DataFrame:
    df = _load_df()
    today = now_date_str()
    return df[df["Date"].astype(str) == today]


def get_attendance_by_date(date_str: str) -> pd.DataFrame:
    """Filter attendance by a specific date (YYYY-MM-DD)."""
    df = _load_df()
    return df[df["Date"].astype(str) == date_str]


def get_dashboard_stats() -> dict:
    from services.employee_service import employee_count

    df = _load_df()
    today = now_date_str()
    today_df = df[df["Date"].astype(str) == today]

    present = len(today_df)
    late_df = today_df[today_df["Late"].astype(str).str.upper() == "YES"]
    late_count = len(late_df)

    worked_total = 0
    salary_total = 0.0
    for _, row in today_df.iterrows():
        try:
            wh = row["Worked Hours"]
            if pd.notna(wh) and str(wh).strip():
                worked_total += int(float(str(wh)))
        except (ValueError, TypeError):
            pass
        try:
            sal = row["Total Salary"]
            if pd.notna(sal) and str(sal).strip():
                salary_total += float(str(sal))
        except (ValueError, TypeError):
            pass

    late_employees = []
    for _, row in late_df.iterrows():
        late_employees.append({
            "name": str(row["Employee Name"]),
            "uid": str(row["UID"]),
            "entry": str(row["Entry Time"]),
        })

    total_employees = employee_count()
    absent_today = max(total_employees - present, 0)

    return {
        "total_employees": total_employees,
        "present_today": present,
        "absent_today": absent_today,
        "late_today": late_count,
        "total_worked_hours": worked_total,
        "total_salary": salary_total,
        "late_employees": late_employees,
    }