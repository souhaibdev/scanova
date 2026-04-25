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


# ── Public API ────────────────────────────────────────────────────────────────

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
        }
    }
    Filters by a single employee UID if uid is provided (passed via filter).
    Period: date(year, month, 1)  <=  Date  <  date(year, next_month, 1)
    """
    df = get_attendance_df()

    # ── Normalise Date column ─────────────────────────────────────────
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

    # ── Period bounds ─────────────────────────────────────────────────
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    mask = (df["Date"] >= start) & (df["Date"] < end)
    df = df[mask].copy()

    # ── Stats ─────────────────────────────────────────────────────────
    # Total calendar working days in the period (Mon–Fri only, or all days?)
    # Here we count ALL calendar days in the period; adjust if needed.
    total_days_in_period = (end - start).days

    jours_travailles = int(df["Date"].nunique()) if not df.empty else 0

    jours_absents = max(total_days_in_period - jours_travailles, 0)

    if "Late" in df.columns:
        jours_late = int(
            df[df["Late"].astype(str).str.upper() == "YES"]["Date"].nunique()
        )
    else:
        jours_late = 0

    total_salary = (
        pd.to_numeric(df["Total Salary"], errors="coerce").sum()
        if "Total Salary" in df.columns
        else 0.0
    )

    stats = {
        "jours_travailles": jours_travailles,
        "jours_absents":    jours_absents,
        "jours_late":       jours_late,
        "total_salary":     round(float(total_salary), 2),
    }

    return {"detail_rows": df, "stats": stats}


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

    # Recompute stats on filtered data
    month_start = date(year, month, 1)
    month_end   = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
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

    return {
        "detail_rows": df,
        "stats": {
            "jours_travailles": jours_travailles,
            "jours_absents":    jours_absents,
            "jours_late":       jours_late,
            "total_salary":     round(float(total_salary), 2),
        },
    }