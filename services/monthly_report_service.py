"""
services/monthly_report_service.py
───────────────────────────────────
Returns per-employee monthly attendance stats + daily detail rows.
Salary period: 1st of selected month → 1st of next month (exclusive).
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta

import pandas as pd

from services.attendance_service import get_attendance_df
from services.advances_service import get_all_advances
from services.primes_service import get_all_primes


# ── Public API ────────────────────────────────────────────────────────────────

def _get_total_advances(month: int, year: int, exact_uids: list[str] | None = None) -> float:
    """
    Calculate total advances for a given month/year.
    If exact_uids is provided, filter only those UIDs.
    """
    try:
        df = get_all_advances()
        if df.empty:
            return 0.0

        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        month_name = calendar.month_name[month]

        mask = (df["Month"].astype(str) == month_name) & (df["Year"] == year)
        df = df[mask]

        if exact_uids is not None:
            df = df[df["UID"].astype(str).isin(exact_uids)]

        total = pd.to_numeric(df["Amount"], errors="coerce").sum()
        return float(total) if pd.notna(total) else 0.0
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Error calculating advances: %s", e)
        return 0.0


def _get_total_primes(month: int, year: int, exact_uids: list[str] | None = None) -> float:
    """
    Calculate total primes for a given month/year.
    If exact_uids is provided, filter only those UIDs.
    """
    try:
        df = get_all_primes()
        if df.empty:
            return 0.0

        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        month_name = calendar.month_name[month]

        mask = (df["Month"].astype(str) == month_name) & (df["Year"] == year)
        df = df[mask]

        if exact_uids is not None:
            df = df[df["UID"].astype(str).isin(exact_uids)]

        total = pd.to_numeric(df["Amount"], errors="coerce").sum()
        return float(total) if pd.notna(total) else 0.0
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Error calculating primes: %s", e)
        return 0.0


def get_monthly_report(month: int, year: int) -> dict:
    """
    Returns:
    {
        "detail_rows": pd.DataFrame,   # one row per worked day
        "stats": {
            "jours_travailles": int,
            "jours_absents":    int,
            "jours_late":       int,
            "total_salary":     float,
            "total_advances":   float,
            "total_primes":     float,
            "net_salary":       float,
        }
    }
    Period: date(year, month, 1)  <=  Date  <  date(year, next_month, 1)
    """
    df = get_attendance_df()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

    start = date(year, month, 1)
    end   = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    df    = df[(df["Date"] >= start) & (df["Date"] < end)].copy()

    total_days_in_period = (end - start).days
    jours_travailles     = int(df["Date"].nunique()) if not df.empty else 0
    jours_absents        = max(total_days_in_period - jours_travailles, 0)
    jours_late           = (
        int(df[df["Late"].astype(str).str.upper() == "YES"]["Date"].nunique())
        if "Late" in df.columns else 0
    )
    total_salary = (
        pd.to_numeric(df["Total Salary"], errors="coerce").sum()
        if "Total Salary" in df.columns else 0.0
    )

    # No filter — pass None to get totals for all employees
    total_advances = _get_total_advances(month, year)
    total_primes   = _get_total_primes(month, year)
    net_salary     = round(float(total_salary) - total_advances + total_primes, 2)

    return {
        "detail_rows": df,
        "stats": {
            "jours_travailles": jours_travailles,
            "jours_absents":    jours_absents,
            "jours_late":       jours_late,
            "total_salary":     round(float(total_salary), 2),
            "total_advances":   round(total_advances, 2),
            "total_primes":     round(total_primes, 2),
            "net_salary":       net_salary,
        },
    }


def get_monthly_report_filtered(
    month: int,
    year: int,
    uid_filter: str = "",
    name_filter: str = "",
    late_filter: str = "All",   # "All" | "YES" | "NO"
) -> dict:
    """
    Same as get_monthly_report but with optional column filters applied
    BEFORE computing stats, so stats reflect the filtered subset.
    """
    result = get_monthly_report(month, year)
    df = result["detail_rows"].copy()

    if uid_filter:
        df = df[df["UID"].astype(str).str.contains(uid_filter, case=False, na=False)]
    if name_filter:
        df = df[df["Employee Name"].astype(str).str.lower().str.contains(name_filter.lower(), na=False)]
    if late_filter != "All":
        df = df[df["Late"].astype(str).str.upper() == late_filter.upper()]

    # ── Extract exact UIDs from filtered attendance ───────────────────
    # كنخرجو الـ UIDs الحقيقية من الـ df المفيلترة
    # هكذا advances/primes كيتفيلترو على نفس الموظفين بالضبط
    exact_uids  = df["UID"].astype(str).unique().tolist() if not df.empty else []
    uids_to_pass = exact_uids if (uid_filter or name_filter) else None

    # ── Recompute stats on filtered data ──────────────────────────────
    month_start          = date(year, month, 1)
    month_end            = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
    total_days_in_period = (month_end - month_start).days

    jours_travailles = int(df["Date"].nunique()) if not df.empty else 0
    jours_absents    = max(total_days_in_period - jours_travailles, 0)
    jours_late       = (
        int(df[df["Late"].astype(str).str.upper() == "YES"]["Date"].nunique())
        if "Late" in df.columns and not df.empty else 0
    )
    total_salary = (
        pd.to_numeric(df["Total Salary"], errors="coerce").sum()
        if "Total Salary" in df.columns else 0.0
    )

    total_advances = _get_total_advances(month, year, uids_to_pass)
    total_primes   = _get_total_primes(month, year, uids_to_pass)
    net_salary     = round(float(total_salary) - total_advances + total_primes, 2)

    return {
        "detail_rows": df,
        "stats": {
            "jours_travailles": jours_travailles,
            "jours_absents":    jours_absents,
            "jours_late":       jours_late,
            "total_salary":     round(float(total_salary), 2),
            "total_advances":   round(total_advances, 2),
            "total_primes":     round(total_primes, 2),
            "net_salary":       net_salary,
        },
    }