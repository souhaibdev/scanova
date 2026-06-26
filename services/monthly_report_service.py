"""
services/monthly_report_service.py

Attendance report service.

- Calls with month/year keep the original monthly behavior used by Employee Report.
- Calls without month/year return the rolling last 15 days report used by MonthlyReportPage.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

import pandas as pd

from services.attendance_service import get_attendance_df
from services.advances_service import get_all_advances
from services.primes_service import get_all_primes


def _last_15_day_range() -> tuple[date, date]:
    end = date.today()
    start = end - timedelta(days=14)
    return start, end


def _monthly_range(month: int, year: int) -> tuple[date, date]:
    start = date(year, month, 1)
    end = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    return start, end


def _attendance_for_range(start: date, end: date, inclusive_end: bool) -> pd.DataFrame:
    df = get_attendance_df()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

    if inclusive_end:
        return df[(df["Date"] >= start) & (df["Date"] <= end)].copy()
    return df[(df["Date"] >= start) & (df["Date"] < end)].copy()


def _sum_amounts_for_dates(
    df: pd.DataFrame,
    start: date,
    end: date,
    exact_uids: list[str] | None = None,
) -> float:
    if df.empty:
        return 0.0

    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    df = df[(df["Date"] >= start) & (df["Date"] <= end)]

    if exact_uids is not None:
        df = df[df["UID"].astype(str).isin(exact_uids)]

    total = pd.to_numeric(df["Amount"], errors="coerce").sum()
    return float(total) if pd.notna(total) else 0.0


def _sum_amounts_for_month(
    df: pd.DataFrame,
    month: int,
    year: int,
    exact_uids: list[str] | None = None,
) -> float:
    if df.empty:
        return 0.0

    df = df.copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    month_name = calendar.month_name[month]
    df = df[(df["Month"].astype(str) == month_name) & (df["Year"] == year)]

    if exact_uids is not None:
        df = df[df["UID"].astype(str).isin(exact_uids)]

    total = pd.to_numeric(df["Amount"], errors="coerce").sum()
    return float(total) if pd.notna(total) else 0.0


def _get_total_advances_for_dates(
    start: date,
    end: date,
    exact_uids: list[str] | None = None,
) -> float:
    try:
        return _sum_amounts_for_dates(get_all_advances(), start, end, exact_uids)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Error calculating advances: %s", e)
        return 0.0


def _get_total_primes_for_dates(
    start: date,
    end: date,
    exact_uids: list[str] | None = None,
) -> float:
    try:
        return _sum_amounts_for_dates(get_all_primes(), start, end, exact_uids)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Error calculating primes: %s", e)
        return 0.0


def _get_total_advances_for_month(
    month: int,
    year: int,
    exact_uids: list[str] | None = None,
) -> float:
    try:
        return _sum_amounts_for_month(get_all_advances(), month, year, exact_uids)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Error calculating advances: %s", e)
        return 0.0


def _get_total_primes_for_month(
    month: int,
    year: int,
    exact_uids: list[str] | None = None,
) -> float:
    try:
        return _sum_amounts_for_month(get_all_primes(), month, year, exact_uids)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Error calculating primes: %s", e)
        return 0.0


def _get_total_advances(
    month: int,
    year: int,
    exact_uids: list[str] | None = None,
) -> float:
    return _get_total_advances_for_month(month, year, exact_uids)


def _get_total_primes(
    month: int,
    year: int,
    exact_uids: list[str] | None = None,
) -> float:
    return _get_total_primes_for_month(month, year, exact_uids)


def _build_stats(
    df: pd.DataFrame,
    total_days_in_period: int,
    total_advances: float,
    total_primes: float,
) -> dict:
    jours_travailles = int(df["Date"].nunique()) if not df.empty else 0
    jours_absents = max(total_days_in_period - jours_travailles, 0)
    jours_late = (
        int(df[df["Late"].astype(str).str.upper() == "YES"]["Date"].nunique())
        if "Late" in df.columns and not df.empty else 0
    )
    total_salary = (
        pd.to_numeric(df["Total Salary"], errors="coerce").sum()
        if "Total Salary" in df.columns else 0.0
    )
    net_salary = round(float(total_salary) - total_advances + total_primes, 2)

    return {
        "jours_travailles": jours_travailles,
        "jours_absents": jours_absents,
        "jours_late": jours_late,
        "total_salary": round(float(total_salary), 2),
        "total_advances": round(total_advances, 2),
        "total_primes": round(total_primes, 2),
        "net_salary": net_salary,
    }


def _get_rolling_report(exact_uids: list[str] | None = None) -> dict:
    start, end = _last_15_day_range()
    df = _attendance_for_range(start, end, inclusive_end=True)
    total_advances = _get_total_advances_for_dates(start, end, exact_uids)
    total_primes = _get_total_primes_for_dates(start, end, exact_uids)

    stats = _build_stats(
        df=df,
        total_days_in_period=(end - start).days + 1,
        total_advances=total_advances,
        total_primes=total_primes,
    )
    stats["start_date"] = start
    stats["end_date"] = end

    return {"detail_rows": df, "stats": stats}


def _get_month_report(
    month: int,
    year: int,
    exact_uids: list[str] | None = None,
) -> dict:
    start, end = _monthly_range(month, year)
    df = _attendance_for_range(start, end, inclusive_end=False)
    total_advances = _get_total_advances_for_month(month, year, exact_uids)
    total_primes = _get_total_primes_for_month(month, year, exact_uids)

    return {
        "detail_rows": df,
        "stats": _build_stats(
            df=df,
            total_days_in_period=(end - start).days,
            total_advances=total_advances,
            total_primes=total_primes,
        ),
    }


def get_monthly_report(month: int | None = None, year: int | None = None) -> dict:
    if month is not None and year is not None:
        return _get_month_report(month, year)
    return _get_rolling_report()


def get_monthly_report_filtered(
    month: int | None = None,
    year: int | None = None,
    uid_filter: str = "",
    name_filter: str = "",
    late_filter: str = "All",
) -> dict:
    """
    Apply optional UID, name, and late filters before computing stats.

    If month/year are provided, the original monthly behavior is used.
    If month/year are omitted, the rolling last 15 days behavior is used.
    """
    is_monthly = month is not None and year is not None
    result = _get_month_report(month, year) if is_monthly else _get_rolling_report()
    df = result["detail_rows"].copy()

    if uid_filter:
        df = df[df["UID"].astype(str).str.contains(uid_filter, case=False, na=False)]
    if name_filter:
        df = df[df["Employee Name"].astype(str).str.contains(name_filter, case=False, na=False)]
    if late_filter != "All":
        df = df[df["Late"].astype(str).str.upper() == late_filter.upper()]

    exact_uids = df["UID"].astype(str).unique().tolist() if not df.empty else []
    uids_to_pass = exact_uids if (uid_filter or name_filter) else None

    if is_monthly:
        start, end = _monthly_range(month, year)
        total_advances = _get_total_advances_for_month(month, year, uids_to_pass)
        total_primes = _get_total_primes_for_month(month, year, uids_to_pass)
        stats = _build_stats(
            df=df,
            total_days_in_period=(end - start).days,
            total_advances=total_advances,
            total_primes=total_primes,
        )
    else:
        start, end = _last_15_day_range()
        total_advances = _get_total_advances_for_dates(start, end, uids_to_pass)
        total_primes = _get_total_primes_for_dates(start, end, uids_to_pass)
        stats = _build_stats(
            df=df,
            total_days_in_period=(end - start).days + 1,
            total_advances=total_advances,
            total_primes=total_primes,
        )
        stats["start_date"] = start
        stats["end_date"] = end

    return {"detail_rows": df, "stats": stats}
