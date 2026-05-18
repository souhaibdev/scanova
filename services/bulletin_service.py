"""
services/bulletin_service.py
─────────────────────────────
Aggregates per-employee monthly data needed for the Bulletin de Paie PDF.
Returns one summary row per employee for a given month/year.
"""

from __future__ import annotations

import calendar
import pandas as pd

from services.monthly_report_service import get_monthly_report, _get_total_advances
from services.primes_service import get_all_primes
from services.employee_service import get_employee_by_uid
from utils.pdf_generator import BulletinData, generate_bulletin_pdf


def _get_total_primes_for_emp(uid: str, month: int, year: int) -> float:
    """Total primes for a given employee in a given month."""
    try:
        df = get_all_primes()
        if df.empty:
            return 0.0
        month_name = calendar.month_name[month]
        df = df[
            (df["Month"].astype(str) == month_name) &
            (df["Year"].astype(str)  == str(year))  &
            (df["UID"].astype(str)   == str(uid))
        ]
        return round(float(pd.to_numeric(df["Amount"], errors="coerce").sum()), 2)
    except Exception:
        return 0.0


def _get_cin(uid: str) -> str:
    """Fetch CIN from employee service. Returns empty string if not found."""
    emp = get_employee_by_uid(str(uid))
    return emp.cin if emp else ""


def get_bulletin_summary(month: int, year: int) -> pd.DataFrame:
    """
    Returns a DataFrame with one row per employee.

    Columns:
        UID, CIN, Employee Name,
        Worked Hours, Hourly Rate,
        Salaire Base, Prime, Avance,
        Salaire Brut, CNSS, AMO,
        Total Retenues, Salaire Net,
    """
    result = get_monthly_report(month, year)
    df = result["detail_rows"].copy()

    if df.empty:
        return pd.DataFrame(columns=[
            "UID", "CIN", "Employee Name", "Worked Hours", "Hourly Rate",
            "Salaire Base", "Prime", "Avance",
            "Salaire Brut", "CNSS", "AMO",
            "Total Retenues", "Salaire Net",
        ])

    # ── Numeric cols ──────────────────────────────────────────────────
    df["Worked Hours"] = pd.to_numeric(df["Worked Hours"], errors="coerce").fillna(0)
    df["Hourly Rate"]  = pd.to_numeric(df["Hourly Rate"],  errors="coerce").fillna(0)

    # ── Group by employee ─────────────────────────────────────────────
    grp = (
        df.groupby(["UID", "Employee Name"], as_index=False)
        .agg(
            Worked_Hours=("Worked Hours", "sum"),
            Hourly_Rate =("Hourly Rate",  "first"),
        )
    )
    grp.rename(columns={"Worked_Hours": "Worked Hours",
                         "Hourly_Rate":  "Hourly Rate"}, inplace=True)

    # ── CIN ───────────────────────────────────────────────────────────
    grp["CIN"] = grp["UID"].apply(_get_cin)

    # ── Calculs ───────────────────────────────────────────────────────
    CNSS_RATE = 0.0448
    AMO_RATE  = 0.0226

    grp["Salaire Base"]   = (grp["Worked Hours"] * grp["Hourly Rate"]).round(2)
    grp["Prime"]          = grp["UID"].apply(
        lambda uid: _get_total_primes_for_emp(str(uid), month, year)
    )
    grp["Avance"]         = grp["UID"].apply(
        lambda uid: _get_total_advances(month, year, str(uid))
    )
    grp["Salaire Brut"]   = (grp["Salaire Base"] + grp["Prime"]).round(2)
    grp["CNSS"]           = (grp["Salaire Brut"] * CNSS_RATE).round(2)
    grp["AMO"]            = (grp["Salaire Brut"] * AMO_RATE).round(2)
    grp["Total Retenues"] = (grp["CNSS"] + grp["AMO"] + grp["Avance"]).round(2)
    grp["Salaire Net"]    = (grp["Salaire Brut"] - grp["Total Retenues"]).clip(lower=0).round(2)

    return grp[[
        "UID", "CIN", "Employee Name", "Worked Hours", "Hourly Rate",
        "Salaire Base", "Prime", "Avance",
        "Salaire Brut", "CNSS", "AMO",
        "Total Retenues", "Salaire Net",
    ]]


def generate_bulletins(month: int, year: int, uid_filter: str = "") -> list[str]:
    """
    Generate PDF bulletins for the given month/year.
    If uid_filter is provided, generate only for that employee.
    Returns list of generated PDF file paths.
    """
    df = get_bulletin_summary(month, year)

    if df.empty:
        return []

    if uid_filter:
        df = df[df["UID"].astype(str) == uid_filter]

    paths = []
    for _, row in df.iterrows():
        data = BulletinData(
            uid=row["UID"],
            cin=row["CIN"],
            nom_prenom=row["Employee Name"],
            mois=month,
            annee=year,
            heures_travaillees=row["Worked Hours"],
            taux_horaire=row["Hourly Rate"],
            prime=row["Prime"],
            avance=row["Avance"],
        )
        path = generate_bulletin_pdf(data)
        paths.append(path)

    return paths