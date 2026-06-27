"""
services/bulletin_service.py
─────────────────────────────
Aggregates per-employee monthly data needed for the Bulletin de Paie PDF.
Returns one summary row per employee for a given month/year.
"""

from __future__ import annotations

import calendar
import logging
import pandas as pd

from services.monthly_report_service import (
    get_monthly_report,
    get_monthly_report_filtered,
    _get_total_advances,
    _get_total_primes,
)
from services.employee_service import get_employee_by_uid
from utils.pdf_generator import BulletinData, generate_bulletin_pdf

logger = logging.getLogger(__name__)


def _get_cin(uid: str) -> str:
    """Fetch CIN from employee service. Returns empty string if not found."""
    emp = get_employee_by_uid(str(uid))
    return emp.cin if emp else ""


def _get_employee_rates(uid: str) -> tuple[float, float]:
    emp = get_employee_by_uid(str(uid))
    if not emp:
        logger.warning("No employee found for UID: %s", uid)
        return 0.0, 0.0

    cnss_rate = emp.cnss_value if emp.cnss_enabled and emp.cnss_value is not None else 0.0
    amo_rate = emp.amo_value if emp.amo_enabled and emp.amo_value is not None else 0.0
    
    logger.debug(
        "Employee CNSS/AMO rates for UID %s: cnss_enabled=%s, cnss_value=%s, cnss_rate=%s | amo_enabled=%s, amo_value=%s, amo_rate=%s",
        uid, emp.cnss_enabled, emp.cnss_value, cnss_rate,
        emp.amo_enabled, emp.amo_value, amo_rate
    )
    
    return cnss_rate, amo_rate


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

    grp["CNSS Rate"] = grp["UID"].apply(lambda uid: _get_employee_rates(uid)[0])
    grp["AMO Rate"]  = grp["UID"].apply(lambda uid: _get_employee_rates(uid)[1])
    
    logger.debug("Bulletin rates loaded: %s", grp[["UID", "CNSS Rate", "AMO Rate"]].to_dict(orient="records"))

    # ── Calculs ───────────────────────────────────────────────────────
    grp["Salaire Base"] = (grp["Worked Hours"] * grp["Hourly Rate"]).round(2)

    # نعطيو list ديال UID واحد — متطابق مع signature الجديد
    grp["Prime"] = grp["UID"].apply(
        lambda uid: _get_total_primes(month, year, [str(uid)])
    )
    grp["Avance"] = grp["UID"].apply(
        lambda uid: _get_total_advances(month, year, [str(uid)])
    )

    grp["Salaire Brut"]   = (grp["Salaire Base"] + grp["Prime"]).round(2)
    grp["CNSS"]           = (grp["Salaire Brut"] * grp["CNSS Rate"]).round(2)
    grp["AMO"]            = (grp["Salaire Brut"] * grp["AMO Rate"]).round(2)
    grp["Total Retenues"] = (grp["CNSS"] + grp["AMO"] + grp["Avance"]).round(2)
    grp["Salaire Net"]    = (grp["Salaire Brut"] - grp["Total Retenues"]).clip(lower=0).round(2)

    return grp[[
        "UID", "CIN", "Employee Name", "Worked Hours", "Hourly Rate",
        "Salaire Base", "Prime", "Avance",
        "Salaire Brut", "CNSS", "AMO",
        "Total Retenues", "Salaire Net",
        "CNSS Rate", "AMO Rate",
    ]]


def generate_bulletins(
    month: int,
    year: int,
    uid_filter: str = "",
    name_filter: str = "",
) -> list[str]:
    """
    Generate PDF bulletins for the given month/year.
    If uid_filter or name_filter is provided, generate only for matching employees.
    Returns list of generated PDF file paths.
    """
    df = get_bulletin_summary(month, year)

    if df.empty:
        return []

    if uid_filter or name_filter:
        filtered = get_monthly_report_filtered(
            month=month,
            year=year,
            uid_filter=uid_filter,
            name_filter=name_filter,
        )
        exact_uids = (
            filtered["detail_rows"]["UID"].astype(str).unique().tolist()
            if not filtered["detail_rows"].empty else []
        )
        if not exact_uids:
            return []
        df = df[df["UID"].astype(str).isin(exact_uids)]

    paths = []
    for _, row in df.iterrows():
        logger.debug(
            "Creating bulletin for UID %s: cnss_rate=%s, amo_rate=%s",
            row["UID"], row.get("CNSS Rate", 0.0), row.get("AMO Rate", 0.0)
        )
        
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
            cnss_rate=row.get("CNSS Rate", 0.0),
            amo_rate=row.get("AMO Rate", 0.0),
        )
        path = generate_bulletin_pdf(data)
        paths.append(path)

    return paths