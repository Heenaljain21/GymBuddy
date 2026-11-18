"""General helper functions for GYM BUDDY.

Provides currency formatting (₹), phone formatting, WhatsApp link generation,
and pagination utilities.
"""

from __future__ import annotations
import urllib.parse
from typing import Any, List, Optional
import pandas as pd
from .date_utils import format_date_display


def format_currency(amount: Optional[float | int | str]) -> str:
    """Format numeric amount into Indian Rupee format (e.g. ₹12,500.00)."""
    if amount is None or amount == "":
        return "₹0.00"
    try:
        val = float(amount)
        # Indian number format representation or standard formatted
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return f"₹{amount}"


def format_phone(phone: Optional[str]) -> str:
    """Format phone number to standard 10-digit Indian display."""
    if not phone:
        return "-"
    # Strip any non-digit
    digits = "".join(filter(str.isdigit, str(phone)))
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if len(digits) == 10:
        return f"+91 {digits[:5]} {digits[5:]}"
    return str(phone)


def clean_phone_for_whatsapp(phone: Optional[str]) -> str:
    """Convert phone to pure digits with 91 country code for wa.me links."""
    if not phone:
        return ""
    digits = "".join(filter(str.isdigit, str(phone)))
    if digits.startswith("91") and len(digits) == 12:
        return digits
    if len(digits) == 10:
        return f"91{digits}"
    return digits


def generate_whatsapp_link(phone: Optional[str], message: str) -> str:
    """Generate WhatsApp direct chat URL with prefilled text."""
    wa_phone = clean_phone_for_whatsapp(phone)
    if not wa_phone:
        return "#"
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{wa_phone}?text={encoded_msg}"


def format_date(dt: Any) -> str:
    """Alias for format_date_display."""
    return format_date_display(dt)


def paginate(items: List[Any], page: int, page_size: int = 10) -> List[Any]:
    """Slice an in-memory list for simple pagination."""
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]
