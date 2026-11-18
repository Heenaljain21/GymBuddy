"""Attendance tracking service for GYM BUDDY.

Handles QR & manual check-in, duplicate prevention per day,
daily registers, and attendance history analytics.
"""

from __future__ import annotations
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
import uuid
from utils.security import get_supabase_client
from utils.date_utils import get_ist_today, get_ist_now


def is_already_checked_in(gym_id: str, member_id: str, check_date: Optional[date] = None) -> bool:
    """Check if member has already checked in on the given date."""
    client = get_supabase_client()
    target_date = str(check_date or get_ist_today())
    try:
        res = (
            client.table("attendance")
            .select("id")
            .eq("gym_id", gym_id)
            .eq("member_id", member_id)
            .eq("check_in_date", target_date)
            .execute()
        )
        return bool(res.data and len(res.data) > 0)
    except Exception:
        return False


def check_in(
    gym_id: str,
    member_id: str,
    method: str = "qr_code",
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Record member gym check-in with validation."""
    client = get_supabase_client()
    today = get_ist_today()
    now_time = get_ist_now().strftime("%H:%M:%S")

    # 1. Check duplicate
    if is_already_checked_in(gym_id, member_id, today):
        return False, "Member has already checked in today! ⚠️", None

    try:
        payload = {
            "id": str(uuid.uuid4()),
            "gym_id": gym_id,
            "member_id": member_id,
            "check_in_date": str(today),
            "check_in_time": now_time,
            "method": method,
        }
        res = client.table("attendance").insert(payload).execute()
        record = res.data[0] if (res.data and len(res.data) > 0) else payload
        return True, "Check-in recorded successfully! 🎉", record
    except Exception as e:
        return False, f"Failed to record check-in: {str(e)}", None


def get_today_attendance(gym_id: str, filter_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """Fetch all check-in entries for a specific date enriched with member details."""
    client = get_supabase_client()
    target_date = str(filter_date or get_ist_today())
    try:
        att_res = (
            client.table("attendance")
            .select("*")
            .eq("gym_id", gym_id)
            .eq("check_in_date", target_date)
            .order("check_in_time", desc=True)
            .execute()
        )
        records = att_res.data or []

        # Enrich with member names and phone numbers
        members_res = client.table("members").select("id, full_name, phone, member_code").eq("gym_id", gym_id).execute()
        mem_map = {m["id"]: m for m in (members_res.data or [])}

        for r in records:
            m = mem_map.get(r.get("member_id"), {})
            r["member_name"] = m.get("full_name", "Unknown Member")
            r["member_phone"] = m.get("phone", "-")
            r["member_code"] = m.get("member_code", "-")

        return records
    except Exception:
        return []


def get_member_attendance(gym_id: str, member_id: str, limit: int = 30) -> List[Dict[str, Any]]:
    """Fetch attendance history for an individual member."""
    client = get_supabase_client()
    try:
        res = (
            client.table("attendance")
            .select("*")
            .eq("gym_id", gym_id)
            .eq("member_id", member_id)
            .order("check_in_date", desc=True)
            .limit(limit)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def get_monthly_attendance_count(gym_id: str, member_id: str) -> int:
    """Return count of check-ins for the current month for a member."""
    today = get_ist_today()
    start_of_month = str(today.replace(day=1))
    client = get_supabase_client()
    try:
        res = (
            client.table("attendance")
            .select("id")
            .eq("gym_id", gym_id)
            .eq("member_id", member_id)
            .gte("check_in_date", start_of_month)
            .execute()
        )
        return len(res.data or [])
    except Exception:
        return 0
