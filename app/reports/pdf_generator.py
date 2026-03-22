"""
PDF generator — produces workload report from snapshot data using reportlab.

Generates a landscape A4 PDF with:
  - Institutional header
  - Faculty workload table matching the Excel column structure
  - Proper wrapping and borders
  - Valid %PDF header (no corruption)
"""

from __future__ import annotations
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Semester Roman numeral mapping
ROMAN = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI",
          "I": "I", "II": "II", "III": "III", "IV": "IV", "V": "V", "VI": "VI"}


def _to_roman(val: str) -> str:
    s = str(val).strip()
    return ROMAN.get(s, s)


def generate_pdf_from_snapshot(
    snapshot_data: list[dict],
    academic_year: str,
    semester_type: str,
) -> bytes:
    """
    Generate a landscape A4 PDF workload report from snapshot JSON.
    Zero database queries.

    Returns:
        PDF file as bytes (starts with %PDF)
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    )

    output = io.BytesIO()
    page_w, page_h = landscape(A4)

    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "WLTitle", parent=styles["Heading1"],
        fontSize=14, alignment=1, spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "WLSubtitle", parent=styles["Heading2"],
        fontSize=11, alignment=1, spaceAfter=2,
    )
    cell_style = ParagraphStyle(
        "WLCell", parent=styles["Normal"],
        fontSize=7, leading=8, wordWrap="CJK",
    )
    cell_center = ParagraphStyle(
        "WLCellCenter", parent=cell_style,
        alignment=1,
    )

    elements = []

    # ── Header ──
    elements.append(Paragraph("HINDUSTAN INSTITUTE OF TECHNOLOGY AND SCIENCE", title_style))
    elements.append(Paragraph("SCHOOL OF BASIC AND APPLIED SCIENCES", subtitle_style))
    elements.append(Paragraph("DEPARTMENT NAME: COMPUTER APPLICATIONS", subtitle_style))
    sem_label = "EVEN" if semester_type == "EVEN" else "ODD"
    elements.append(Paragraph(
        f"MASTER WORKLOAD - {sem_label} SEMESTER {academic_year}", subtitle_style
    ))
    elements.append(Spacer(1, 4 * mm))

    # ── Column headers ──
    col_headers = [
        "S.No", "Emp\nCode", "Faculty Name", "Desig.",
        "UG/\nPG", "Programme", "Cat.", "Sem", "Sec",
        "Str.", "Code", "Course Name", "Cplx",
        "Cr", "L", "T", "P", "L+T+P", "TCH",
        "Min\nWL", "Dev", "Remarks", "Other\nAcad", "Total\nWL",
    ]

    header_row = [Paragraph(f"<b>{h}</b>", cell_center) for h in col_headers]

    # ── Build data rows ──
    table_data = [header_row]
    serial = 0

    for block in snapshot_data:
        serial += 1
        subjects = block.get("subjects", [])
        if not subjects:
            subjects = [{}]

        for i, subj in enumerate(subjects):
            has_course = bool(subj.get("course_code"))
            row = []

            # Cols 1-4: faculty info (only on first row)
            if i == 0:
                row.append(Paragraph(str(serial), cell_center))
                row.append(Paragraph(str(block.get("emp_code", "")), cell_style))
                row.append(Paragraph(str(block.get("faculty_name", "")), cell_style))
                row.append(Paragraph(str(block.get("designation", "")), cell_style))
            else:
                row.extend([Paragraph("", cell_style)] * 4)

            if has_course:
                row.append(Paragraph(str(subj.get("ug_pg", "")), cell_center))
                row.append(Paragraph(str(subj.get("programme", "")), cell_style))
                row.append(Paragraph(str(subj.get("course_category", "")), cell_center))
                row.append(Paragraph(_to_roman(str(subj.get("semester", ""))), cell_center))
                row.append(Paragraph(str(subj.get("section", "")), cell_center))
                row.append(Paragraph(str(subj.get("student_strength", "")), cell_center))
                row.append(Paragraph(str(subj.get("course_code", "")), cell_style))
                row.append(Paragraph(str(subj.get("course_name", "")), cell_style))
                row.append(Paragraph(str(subj.get("complexity", "")), cell_center))
                row.append(Paragraph(str(subj.get("credits", "")), cell_center))
                row.append(Paragraph(str(subj.get("l", "")), cell_center))
                row.append(Paragraph(str(subj.get("t", "")), cell_center))
                row.append(Paragraph(str(subj.get("p", "")), cell_center))
                row.append(Paragraph(str(subj.get("ltp", "")), cell_center))
                row.append(Paragraph(str(subj.get("tch", "")), cell_center))
            else:
                row.extend([Paragraph("", cell_style)] * 15)

            # Cols 20-24: faculty summary (only on first row)
            if i == 0:
                row.append(Paragraph(str(block.get("min_workload", "")), cell_center))
                row.append(Paragraph(str(block.get("deviation", "")), cell_center))
                row.append(Paragraph(str(block.get("remarks", "")), cell_style))
                row.append(Paragraph(str(block.get("other_academic", "")), cell_center))
                row.append(Paragraph(str(block.get("total_workload", "")), cell_center))
            else:
                row.extend([Paragraph("", cell_style)] * 5)

            table_data.append(row)

    # ── Column widths (proportional to page width) ──
    available_w = page_w - 20 * mm
    col_widths = [
        14, 28, 62, 42,       # S.No, Emp Code, Name, Desig
        18, 50, 22, 16, 16,   # UG/PG, Programme, Cat, Sem, Sec
        18, 34, 72, 20,       # Str, Code, Course Name, Cplx
        16, 12, 12, 12, 22, 22,  # Cr, L, T, P, L+T+P, TCH
        24, 22, 48, 24, 24,   # MinWL, Dev, Remarks, Other, Total
    ]
    total_units = sum(col_widths)
    col_widths_scaled = [(w / total_units) * available_w for w in col_widths]

    table = Table(table_data, colWidths=col_widths_scaled, repeatRows=1)

    style = TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Data rows
        ("FONTSIZE", (0, 1), (-1, -1), 6.5),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
    ])

    # Alternating row colors
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F2F2F2"))

    table.setStyle(style)
    elements.append(table)

    doc.build(elements)
    output.seek(0)
    return output.getvalue()
