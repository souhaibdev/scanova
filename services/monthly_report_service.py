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
from services.primes_service import get_all_primes              # ← زيد


# ── Public API ────────────────────────────────────────────────────────────────

def _get_total_advances(month: int, year: int, uid_filter: str = "") -> float:
    """
    Calculate total advances deducted for a given month/year.
    Optionally filter by UID if provided.
    """
    try:
        df_advances = get_all_advances()
        if df_advances.empty:
            return 0.0
        
        # Filter by month and year
        df_advances["Year"] = pd.to_numeric(df_advances["Year"], errors="coerce")
        df_advances["Month_str"] = df_advances.get("Month", "")
        
        # Convert month number to month name
        month_name = calendar.month_name[month]
        
        # Filter by month name and year
        mask = (df_advances["Month_str"] == month_name) & (df_advances["Year"] == year)
        df_filtered = df_advances[mask]
        
        # Filter by UID if provided
        if uid_filter:
            df_filtered = df_filtered[df_filtered["UID"].astype(str) == uid_filter]
        
        # Sum the amounts
        total = pd.to_numeric(df_filtered["Amount"], errors="coerce").sum()
        return float(total) if pd.notna(total) else 0.0
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Error calculating advances: %s", str(e))
        return 0.0


def _get_total_primes(month: int, year: int, uid_filter: str = "") -> float:   # ← زيد
    """
    Calculate total primes added for a given month/year.
    Optionally filter by UID if provided.
    """
    try:
        df_primes = get_all_primes()
        if df_primes.empty:
            return 0.0

        df_primes["Year"] = pd.to_numeric(df_primes["Year"], errors="coerce")
        month_name = calendar.month_name[month]

        mask = (df_primes["Month"].astype(str) == month_name) & (df_primes["Year"] == year)
        df_filtered = df_primes[mask]

        if uid_filter:
            df_filtered = df_filtered[df_filtered["UID"].astype(str) == uid_filter]

        total = pd.to_numeric(df_filtered["Amount"], errors="coerce").sum()
        return float(total) if pd.notna(total) else 0.0
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Error calculating primes: %s", str(e))
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

    total_advances = _get_total_advances(month, year)
    total_primes   = _get_total_primes(month, year)                # ← زيد
    net_salary     = round(float(total_salary) - total_advances + total_primes, 2)  # ← زيد

    stats = {
        "jours_travailles": jours_travailles,
        "jours_absents":    jours_absents,
        "jours_late":       jours_late,
        "total_salary":     round(float(total_salary), 2),
        "total_advances":   round(total_advances, 2),              # ← زيد
        "total_primes":     round(total_primes, 2),                # ← زيد
        "net_salary":       net_salary,                            # ← زيد
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

    total_advances = _get_total_advances(month, year, uid_filter)
    total_primes   = _get_total_primes(month, year, uid_filter)    # ← زيد
    net_salary     = round(float(total_salary) - total_advances + total_primes, 2)  # ← زيد

    return {
        "detail_rows": df,
        "stats": {
            "jours_travailles": jours_travailles,
            "jours_absents":    jours_absents,
            "jours_late":       jours_late,
            "total_salary":     round(float(total_salary), 2),
            "total_advances":   round(total_advances, 2),          # ← زيد
            "total_primes":     round(total_primes, 2),            # ← زيد
            "net_salary":       net_salary,                        # ← زيد
        },
    }