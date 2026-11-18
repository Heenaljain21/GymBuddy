"""PDF Receipt Generator for GYM BUDDY using ReportLab.

Generates professional receipt documents for membership fees in Indian Rupees.
"""

from __future__ import annotations
import io
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_receipt_pdf(payment_data: Dict[str, Any]) -> bytes:
    """Generate a clean PDF payment receipt and return bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Heading1"],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1E1B4B"),
        fontName="Helvetica-Bold",
        alignment=1,
    )
    
    subtitle_style = ParagraphStyle(
        "ReceiptSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
        alignment=1,
    )
    
    bold_style = ParagraphStyle(
        "ReceiptBold",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0F172A"),
    )
    
    normal_style = ParagraphStyle(
        "ReceiptNormal",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#334155"),
    )

    elements = []
    
    gym_name = payment_data.get("gym_name", "GYM BUDDY FITNESS")
    receipt_no = payment_data.get("receipt_no", "REC-0001")
    date_str = payment_data.get("payment_date", "Today")
    member_name = payment_data.get("member_name", "Member")
    member_code = payment_data.get("member_code", "GMB-000")
    plan_name = payment_data.get("plan_name", "Standard Membership")
    amount = payment_data.get("amount", 0.0)
    payment_method = payment_data.get("payment_method", "Cash")
    ref_no = payment_data.get("transaction_ref") or "N/A"
    
    elements.append(Paragraph(f"<b>{gym_name.upper()}</b>", title_style))
    elements.append(Paragraph("OFFICIAL PAYMENT RECEIPT", subtitle_style))
    elements.append(Spacer(1, 15))
    
    # Meta table
    meta_data = [
        [Paragraph(f"<b>Receipt No:</b> {receipt_no}", normal_style), Paragraph(f"<b>Date:</b> {date_str}", normal_style)],
        [Paragraph(f"<b>Member ID:</b> {member_code}", normal_style), Paragraph(f"<b>Payment Mode:</b> {payment_method}", normal_style)],
    ]
    t_meta = Table(meta_data, colWidths=[260, 260])
    t_meta.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 15))
    
    # Member details table
    items_data = [
        [Paragraph("<b>Description / Item</b>", bold_style), Paragraph("<b>Details</b>", bold_style), Paragraph("<b>Amount (INR)</b>", bold_style)],
        [Paragraph(f"Membership: {plan_name}", normal_style), Paragraph(f"Member: {member_name}", normal_style), Paragraph(f"Rs. {amount:,.2f}", bold_style)],
        [Paragraph(f"Reference: {ref_no}", normal_style), Paragraph("Status: Paid", normal_style), Paragraph("", normal_style)],
        [Paragraph("<b>TOTAL RECEIVED</b>", bold_style), Paragraph("", normal_style), Paragraph(f"<b>Rs. {amount:,.2f}</b>", bold_style)],
    ]
    
    t_items = Table(items_data, colWidths=[220, 180, 120])
    t_items.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("ALIGN", (2, 0), (2, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.HexColor("#8B5CF6")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F8FAFC")),
    ]))
    elements.append(t_items)
    elements.append(Spacer(1, 30))
    
    elements.append(Paragraph("<i>This is a computer-generated receipt for gym membership fees. Thank you for training with us!</i>", subtitle_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>GYM BUDDY</b> • Your Gym. Your Goals. One Smart Buddy.", subtitle_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
