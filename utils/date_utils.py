"""Date and Time utilities for GYM BUDDY.

Handles Indian Standard Time (IST, UTC+5:30), date formatting,
days calculation for memberships, and range helpers.
"""

from __future__ import annotations
from datetime import datetime, date, time, timedelta
from typing import Optional, Tuple
try:
    from zoneinfo import ZoneInfo
    IST_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    IST_TZ = None


def get_ist_now() -> datetime:
    """Return current timestamp in IST."""
    if IST_TZ is not None:
        return datetime.now(IST_TZ)
    return datetime.utcnow() + timedelta(hours=5, minutes=30)


def get_ist_today() -> date:
    """Return current date in IST."""
    return get_ist_now().date()


def format_date_display(dt: Optional[date | datetime | str]) -> str:
    """Format date to friendly Indian format: DD Mon YYYY (e.g. 18 Nov 2026)."""
    if dt is None:
        return "-"
    if isinstance(dt, str):
        try:
            # Handle YYYY-MM-DD or ISO strings
            clean_str = dt.split("T")[0].split(" ")[0]
            dt = datetime.strptime(clean_str, "%Y-%m-%d").date()
        except Exception:
            return dt
    if isinstance(dt, datetime):
        dt = dt.date()
    return dt.strftime("%d %b %Y")


def format_time_display(dt: Optional[datetime | str]) -> str:
    """Format time to 12-hour AM/PM format (e.g. 07:30 AM)."""
    if dt is None:
        return "-"
    if isinstance(dt, str):
        raw = dt.strip()
        try:
            # Full ISO timestamp (e.g. 2026-11-18T07:30:00+05:30)
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Postgres TIME column (e.g. 07:30:00 or 07:30:00.123456)
                dt = time.fromisoformat(raw)
            except ValueError:
                return raw
    return dt.strftime("%I:%M %p")


def days_remaining(expiry_date: Optional[date | str]) -> int:
    """Return number of days remaining until expiry. Negative if expired."""
    if expiry_date is None:
        return 0
    if isinstance(expiry_date, str):
        try:
            clean_str = expiry_date.split("T")[0].split(" ")[0]
            expiry_date = datetime.strptime(clean_str, "%Y-%m-%d").date()
        except Exception:
            return 0
    if isinstance(expiry_date, datetime):
        expiry_date = expiry_date.date()
    
    today = get_ist_today()
    delta = (expiry_date - today).days
    return delta


def days_since(past_date: Optional[date | datetime | str]) -> int:
    """Return number of days elapsed since given date."""
    if past_date is None:
        return 999
    if isinstance(past_date, str):
        try:
            clean_str = past_date.split("T")[0].split(" ")[0]
            past_date = datetime.strptime(clean_str, "%Y-%m-%d").date()
        except Exception:
            return 999
    if isinstance(past_date, datetime):
        past_date = past_date.date()
        
    today = get_ist_today()
    return max(0, (today - past_date).days)


def get_date_range(filter_type: str) -> Tuple[date, date]:
    """Return (start_date, end_date) for named date range filters."""
    today = get_ist_today()
    f = filter_type.lower()
    
    if "today" in f:
        return today, today
    elif "yesterday" in f:
        y = today - timedelta(days=1)
        return y, y
    elif "7" in f:
        return today - timedelta(days=7), today
    elif "30" in f:
        return today - timedelta(days=30), today
    elif "month" in f:
        first_of_month = today.replace(day=1)
        return first_of_month, today
    else:
        return today - timedelta(days=30), today
