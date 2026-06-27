"""
utils/pdf_generator.py
───────────────────────
Generates a Bulletin de Paie PDF (matching the Excel layout)
using ReportLab.

Usage:
    from utils.pdf_generator import generate_bulletin_pdf
    path = generate_bulletin_pdf(data)
"""

from __future__ import annotations
import os
import tempfile
import logging
import uuid
import time
from dataclasses import dataclass, field
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Spacer, Paragraph
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

# ── Taux fixes ────────────────────────────────────────────────────────────────
CNSS_PATRONAL   = 0.0000   # à adapter
AMO_PATRONAL    = 0.0000   # à adapter
AF_PATRONAL     = 0.0000   # Allocations familiales
TFP_PATRONAL    = 0.0000   # Taxe de formation professionnelle

# ── Palette ───────────────────────────────────────────────────────────────────
BLUE_HEADER  = colors.HexColor("#2B79FF")
RED_LABEL    = colors.HexColor("#E53935")
LIGHT_BLUE   = colors.HexColor("#EBF2FF")
LIGHT_PINK   = colors.HexColor("#FFE4E4")
WHITE        = colors.white
BLACK        = colors.black
GREY_BG      = colors.HexColor("#F5F8FF")


@dataclass
class BulletinData:
    # Société
    nom_societe:   str = "NIZARO MODE"
    adresse:       str = "ZONE DES ACTIVITES AL AWAMA N°58"
    tel:           str = ""
    fax:           str = ""

    # Employé
    uid:           str = ""
    cin:           str = ""
    nom_prenom:    str = ""
    adresse_emp:   str = ""
    situation_fam: str = ""
    num_cnss:      str = ""

    # Période
    mois:          int = 1
    annee:         int = 2026

    # Paie
    heures_travaillees: float = 0.0
    taux_horaire:       float = 0.0
    prime:              float = 0.0
    avance:             float = 0.0
    cnss_rate:          float = 0.0
    amo_rate:           float = 0.0


def _mois_label(m: int) -> str:
    mois = ["Janvier","Février","Mars","Avril","Mai","Juin",
            "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
    return mois[m - 1] if 1 <= m <= 12 else str(m)


def generate_bulletin_pdf(data: BulletinData) -> str:
    """
    Generate a Bulletin de Paie PDF.
    Returns the path to the generated file.
    """
    # ── Logging des taux ───────────────────────────────────────────────
    logger.debug(
        "Bulletin PDF generation for UID %s: cnss_rate=%s, amo_rate=%s",
        data.uid, data.cnss_rate, data.amo_rate
    )
    
    # ── Calculs ───────────────────────────────────────────────────────
    salaire_base = round(data.heures_travaillees * data.taux_horaire, 2)
    salaire_brut = round(salaire_base + data.prime, 2)

    cnss_sal  = round(salaire_brut * data.cnss_rate, 2)
    amo_sal   = round(salaire_brut * data.amo_rate,  2)
    total_ret = round(cnss_sal + amo_sal + data.avance, 2)
    
    logger.debug(
        "Bulletin calculations for UID %s: salaire_brut=%s, cnss_sal=%s (rate=%s), amo_sal=%s (rate=%s)",
        data.uid, salaire_brut, cnss_sal, data.cnss_rate, amo_sal, data.amo_rate
    )

    cnss_pat  = round(salaire_brut * CNSS_PATRONAL, 2)
    amo_pat   = round(salaire_brut * AMO_PATRONAL,  2)
    af_pat    = round(salaire_brut * AF_PATRONAL,   2)
    tfp_pat   = round(salaire_brut * TFP_PATRONAL,  2)

    salaire_net = round(salaire_brut - total_ret, 2)
    periode     = f"{_mois_label(data.mois)}/{data.annee}"

    # ── Output path ───────────────────────────────────────────────────
    fname = f"bulletin_{data.uid}_{data.annee}_{data.mois:02d}.pdf"
    path  = os.path.join(tempfile.gettempdir(), fname)

    # Try to remove the old file to avoid permission errors
    # If removal fails, use a unique filename to avoid conflicts
    old_path = path
    attempt = 0
    max_attempts = 3
    
    while attempt < max_attempts:
        try:
            if os.path.exists(path):
                os.remove(path)
            break  # Successfully removed or file doesn't exist
        except PermissionError:
            attempt += 1
            if attempt < max_attempts:
                # Small delay before retry
                time.sleep(0.2)
            else:
                # All removal attempts failed, use a unique path
                unique_id = uuid.uuid4().hex[:8]
                path = os.path.join(tempfile.gettempdir(), 
                                   f"bulletin_{data.uid}_{data.annee}_{data.mois:02d}_{unique_id}.pdf")
                logger.warning(
                    "Could not remove old PDF %s, using unique path instead: %s",
                    old_path, path
                )

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm,
    )

    story = []

    def para(text, size=9, bold=False, color=BLACK, align=TA_LEFT):
        return Paragraph(text, ParagraphStyle(
            "custom",
            fontSize=size,
            leading=size + 3,
            textColor=color,
            fontName="Helvetica-Bold" if bold else "Helvetica",
            alignment=align,
        ))

    def fmt(v):
        return f"{v:.2f}" if isinstance(v, float) else str(v)

    def empty_row():
        return [para("", size=9)] * 7

    W = 18 * cm   # usable width

    # ══════════════════════════════════════════════════════════════════
    # BLOC 1 — En-tête société + titre
    # ══════════════════════════════════════════════════════════════════
    header_data = [
        [
            para(f"Nom de société   <b>{data.nom_societe}</b>", size=9),
            para("BULLETIN DE PAIE", size=13, bold=True, color=WHITE, align=TA_CENTER),
        ],
        [
            para(f"Adresse   <b>{data.adresse}</b>", size=9),
            para("", size=9),
        ],
        [
            para(f"Tel   {data.tel}", size=9),
            para(f"Periode de paie  {periode}", size=9, align=TA_CENTER),
        ],
        [
            para(f"Fax   {data.fax}", size=9),
            para("", size=9),
        ],
    ]
    header_table = Table(header_data, colWidths=[W * 0.55, W * 0.45])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",   (1, 0), (1, 0),   BLUE_HEADER),
        ("BACKGROUND",   (1, 2), (1, 3),   LIGHT_BLUE),
        ("BOX",          (0, 0), (-1, -1), 0.5, BLACK),
        ("INNERGRID",    (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.3*cm))

    # ══════════════════════════════════════════════════════════════════
    # BLOC 2 — Infos employé
    # ══════════════════════════════════════════════════════════════════
    emp_data = [
        [
            para("Nom et Prénom :",      bold=True, size=9),
            para(data.nom_prenom,        size=9),
            para("N° C.I.N :",           bold=True, size=9),
            para(data.cin,               size=9),
        ],
        [
            para("Adresse :",            bold=True, size=9),
            para(data.adresse_emp,       size=9),
            para("N° Employé :",         bold=True, size=9),
            para(data.uid,               size=9),
        ],
        [
            para("Situation familiale :",bold=True, size=9),
            para(data.situation_fam,     size=9),
            para("",                     size=9),
            para("",                     size=9),
        ],
        [
            para("N° CNSS :",            bold=True, size=9),
            para(data.num_cnss,          size=9),
            para("",                     size=9),
            para("",                     size=9),
        ],
    ]
    emp_table = Table(emp_data, colWidths=[W*0.22, W*0.28, W*0.18, W*0.32])
    emp_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 0.5, BLACK),
        ("INNERGRID",    (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(emp_table)
    story.append(Spacer(1, 0.3*cm))

    # ══════════════════════════════════════════════════════════════════
    # BLOC 3 — Tableau principal
    # ══════════════════════════════════════════════════════════════════
    col_w = [W*0.30, W*0.12, W*0.10, W*0.12, W*0.12, W*0.12, W*0.12]

    main_header = [
        [
            para("Libellé",         bold=True, size=8, align=TA_CENTER),
            para("Nombre ou\nbase", bold=True, size=8, align=TA_CENTER),
            para("Part Salariale",  bold=True, size=8, align=TA_CENTER),
            para("",  size=8),
            para("",  size=8),
            para("Part Patronale",  bold=True, size=8, align=TA_CENTER),
            para("",  size=8),
        ],
        [
            para("",          size=8),
            para("",          size=8),
            para("Taux",      bold=True, size=8, align=TA_CENTER),
            para("Gains",     bold=True, size=8, align=TA_CENTER),
            para("Retenues",  bold=True, size=8, align=TA_CENTER),
            para("Taux",      bold=True, size=8, align=TA_CENTER),
            para("Montant",   bold=True, size=8, align=TA_CENTER),
        ],
    ]

    rows = [
        # ── Salaire de base ───────────────────────────────────────────
        [
            para("Salaire de base", size=9, color=RED_LABEL),
            para(fmt(data.heures_travaillees), size=9, align=TA_CENTER),
            para(fmt(data.taux_horaire),       size=9, align=TA_CENTER),
            para(fmt(salaire_base),            size=9, align=TA_CENTER),
            para("", size=9),
            para("", size=9),
            para("", size=9),
        ],
        empty_row(),

        # ── Prime ─────────────────────────────────────────────────────
        [
            para("PRIME", size=9),
            para("0",     size=9, align=TA_CENTER),
            para("0,00",  size=9, align=TA_CENTER),
            para(fmt(data.prime), size=9, align=TA_CENTER),
            para("", size=9),
            para("", size=9),
            para("", size=9),
        ],
        empty_row(),

        # ── Salaire Brut ──────────────────────────────────────────────
        [
            para("Salaire Brut", size=9, color=RED_LABEL),
            para("", size=9),
            para("", size=9),
            para(fmt(salaire_brut), size=9, align=TA_CENTER),
            para("", size=9),
            para("", size=9),
            para("", size=9),
        ],
        empty_row(),

        # ── CNSS ──────────────────────────────────────────────────────
        [
            para("CNSS", size=9),
            para(fmt(salaire_brut),              size=9, align=TA_CENTER),
            para(f"{data.cnss_rate*100:.2f}%",    size=9, align=TA_CENTER),
            para("",                             size=9),
            para(fmt(cnss_sal),                  size=9, align=TA_CENTER),
            para(f"{CNSS_PATRONAL*100:.2f}%",    size=9, align=TA_CENTER),
            para(fmt(cnss_pat),                  size=9, align=TA_CENTER),
        ],
        empty_row(),

        # ── AMO ───────────────────────────────────────────────────────
        [
            para("AMO", size=9),
            para(fmt(salaire_brut),              size=9, align=TA_CENTER),
            para(f"{data.amo_rate*100:.2f}%",     size=9, align=TA_CENTER),
            para("",                             size=9),
            para(fmt(amo_sal),                   size=9, align=TA_CENTER),
            para(f"{AMO_PATRONAL*100:.2f}%",     size=9, align=TA_CENTER),
            para(fmt(amo_pat),                   size=9, align=TA_CENTER),
        ],
        empty_row(),

        # ── Allocations familiales ────────────────────────────────────
        [
            para("Allocations familiale", size=9),
            para(fmt(salaire_brut),              size=9, align=TA_CENTER),
            para("", size=9),
            para("", size=9),
            para("", size=9),
            para(f"{AF_PATRONAL*100:.2f}%",      size=9, align=TA_CENTER),
            para(fmt(af_pat),                    size=9, align=TA_CENTER),
        ],
        empty_row(),

        # ── TFP ───────────────────────────────────────────────────────
        [
            para("Taxe de formation professionnelle", size=9),
            para(fmt(salaire_brut),              size=9, align=TA_CENTER),
            para("", size=9),
            para("", size=9),
            para("", size=9),
            para(f"{TFP_PATRONAL*100:.2f}%",     size=9, align=TA_CENTER),
            para(fmt(tfp_pat),                   size=9, align=TA_CENTER),
        ],
        empty_row(),

        # ── Total Retenues ────────────────────────────────────────────
        [
            para("Total Retenues AVANCE", size=9),
            para("", size=9),
            para("", size=9),
            para("", size=9),
            para(fmt(total_ret),                 size=9, align=TA_CENTER),
            para("",                             size=9),
            para(fmt(cnss_pat + amo_pat + af_pat + tfp_pat), size=9, align=TA_CENTER),
        ],
    ]

    all_rows = main_header + rows
    main_table = Table(all_rows, colWidths=col_w)
    main_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 0.5, BLACK),
        ("INNERGRID",    (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("SPAN",         (2, 0), (4, 0)),          # Part Salariale
        ("SPAN",         (5, 0), (6, 0)),          # Part Patronale
        ("BACKGROUND",   (0, 0), (-1, 1),  GREY_BG),
        ("BACKGROUND",   (3, 2), (3, -1),  LIGHT_BLUE),
        ("BACKGROUND",   (4, 2), (4, -1),  LIGHT_PINK),
        ("BACKGROUND",   (5, 2), (6, -1),  LIGHT_PINK),
    ]))
    story.append(main_table)
    story.append(Spacer(1, 0.4*cm))

    # ══════════════════════════════════════════════════════════════════
    # BLOC 4 — Salaire Net + signature
    # ══════════════════════════════════════════════════════════════════
    net_data = [
        [
            para("", size=9),
            para(f"Salaire Net :    <b>{fmt(salaire_net)}</b>", size=11, color=RED_LABEL),
        ],
        [
            para("", size=9),
            para("Par : Virement / Espèce", size=9),
        ],
    ]
    net_table = Table(net_data, colWidths=[W*0.55, W*0.45])
    net_table.setStyle(TableStyle([
        ("BOX",          (1, 0), (1, -1), 0.5, BLACK),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(net_table)
    story.append(Spacer(1, 0.5*cm))

    # ══════════════════════════════════════════════════════════════════
    # BLOC 5 — Zone signature employé
    # ══════════════════════════════════════════════════════════════════
    sig_data = [
        [
            para("Signature de l'employé :", bold=True, size=9),
            para("", size=9),
            para("Cachet et Signature de l'employeur :", bold=True, size=9),
            para("", size=9),
        ],
        [
            para("", size=9),
            para("", size=9),
            para("", size=9),
            para("", size=9),
        ],
        [
            para("", size=9),
            para("", size=9),
            para("", size=9),
            para("", size=9),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[W*0.22, W*0.28, W*0.28, W*0.22])
    sig_table.setStyle(TableStyle([
        ("BOX",          (0, 0), (-1, -1), 0.5, BLACK),
        ("INNERGRID",    (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 20),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(sig_table)

    doc.build(story)
    return path