"""PDF Receipt Generator for GYM BUDDY using ReportLab.

Generates professional receipt documents for membership fees in Indian Rupees.
"""

from __future__ import annotations
import io
from typing import Dict, Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

INK = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#64748B")
BRAND = colors.HexColor("#6D28D9")
LINE = colors.HexColor("#E2E8F0")


def _p(text: Any, style: ParagraphStyle) -> Paragraph:
    """Paragraph with user text escaped (ReportLab parses mini-XML)."""
    return Paragraph(escape("" if text is None else str(text)), style)


def generate_receipt_pdf(payment_data: Dict[str, Any]) -> bytes:
    """Generate a clean A4 PDF payment receipt and return its bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48,
                            title=f"Receipt {payment_data.get('receipt_no', '')}")
    base = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=base["Heading1"], fontSize=20, leading=24, textColor=INK, fontName="Helvetica-Bold", spaceAfter=2)
    sub = ParagraphStyle("s", parent=base["Normal"], fontSize=9.5, textColor=MUTED, leading=13)
    label = ParagraphStyle("l", parent=base["Normal"], fontSize=8.5, textColor=MUTED, fontName="Helvetica-Bold", leading=11)
    body = ParagraphStyle("b", parent=base["Normal"], fontSize=10.5, textColor=INK, leading=14)
    bold = ParagraphStyle("bb", parent=body, fontName="Helvetica-Bold")
    right_bold = ParagraphStyle("rb", parent=bold, alignment=2)
    tag = ParagraphStyle("tag", parent=base["Normal"], fontSize=10, textColor=BRAND, fontName="Helvetica-Bold", alignment=2)

    amount = float(payment_data.get("amount") or 0.0)
    amount_txt = f"Rs. {amount:,.2f}"

    header = Table(
        [[[_p(payment_data.get("gym_name", "GYM BUDDY"), title), _p(payment_data.get("gym_address", ""), sub)],
          [Paragraph("PAYMENT RECEIPT", tag), _p(payment_data.get("receipt_no", ""), ParagraphStyle("rn", parent=sub, alignment=2))]]],
        colWidths=[330, 170],
    )
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, 0), 2, BRAND), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))

    meta = Table(
        [
            [_p("RECEIVED FROM", label), _p("MEMBER ID", label), _p("DATE", label), _p("PAYMENT MODE", label)],
            [_p(payment_data.get("member_name", "Member"), bold), _p(payment_data.get("member_code", "-"), body),
             _p(payment_data.get("payment_date", "-"), body), _p(payment_data.get("payment_method", "Cash"), body)],
        ],
        colWidths=[170, 110, 110, 110],
    )
    meta.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))

    items = Table(
        [
            [_p("DESCRIPTION", label), _p("REFERENCE", label), Paragraph("AMOUNT", ParagraphStyle("al", parent=label, alignment=2))],
            [_p(f"Membership fee: {payment_data.get('plan_name') or 'Gym membership'}", body),
             _p(payment_data.get("transaction_ref") or "-", body), _p(amount_txt, right_bold)],
            [_p(payment_data.get("remarks") or "", sub), "", ""],
            [_p("Total received", bold), "", _p(amount_txt, right_bold)],
        ],
        colWidths=[260, 130, 110],
    )
    items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, LINE),
        ("LINEABOVE", (0, -1), (-1, -1), 1.2, INK),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    elements = [
        header, Spacer(1, 18), meta, Spacer(1, 18), items, Spacer(1, 28),
        Paragraph("Status: <b>PAID</b>. This is a computer-generated receipt and does not require a signature.", sub),
        Spacer(1, 6),
        Paragraph("Thank you for training with us! Powered by GYM BUDDY.", sub),
    ]
    doc.build(elements)
    return buffer.getvalue()
