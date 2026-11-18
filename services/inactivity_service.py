"""Inactive and missing members tracking service for GYM BUDDY.

Identifies absent gym members by days inactive (7-14, 15-30, 30+, never attended),
generates retention WhatsApp communications, and tracks follow-up records.
"""

from __future__ import annotations
from datetime import date, datetime
from typing import List, Dict, Any, Optional, Tuple
import uuid
from utils.security import get_supabase_client
from utils.date_utils import get_ist_today, days_since


def get_inactive_members(
    gym_id: str,
    threshold_days: int = 14,
) -> Dict[str, List[Dict[str, Any]]]:
    """Identify absent members grouped by duration of absence."""
    client = get_supabase_client()
    today = get_ist_today()

    categories = {
        "7_to_14_days": [],
        "15_to_30_days": [],
        "over_30_days": [],
        "never_attended": [],
        "all_inactive": [],
    }

    try:
        # Fetch active members
        members = client.table("members").select("*").eq("gym_id", gym_id).eq("is_active", True).execute().data or []
        attendance = client.table("attendance").select("*").eq("gym_id", gym_id).order("check_in_date", desc=True).execute().data or []
        followups = client.table("inactivity_followups").select("*").eq("gym_id", gym_id).execute().data or []

        # Find latest attendance per member
        last_visit_map = {}
        for a in attendance:
            mid = a.get("member_id")
            if mid not in last_visit_map:
                last_visit_map[mid] = a.get("check_in_date")

        # Find latest follow up per member
        follow_map = {}
        for f in followups:
            mid = f.get("member_id")
            if mid not in follow_map:
                follow_map[mid] = f

        for m in members:
            mid = m.get("id")
            last_date = last_visit_map.get(mid)
            f_info = follow_map.get(mid, {})

            if not last_date:
                # Never attended
                item = {
                    "member_id": mid,
                    "member_name": m.get("full_name"),
                    "phone": m.get("phone"),
                    "member_code": m.get("member_code"),
                    "last_visit": "Never",
                    "days_inactive": 999,
                    "contact_status": f_info.get("status", "pending"),
                    "last_note": f_info.get("notes", ""),
                }
                categories["never_attended"].append(item)
                categories["all_inactive"].append(item)
            else:
                elapsed = days_since(last_date)
                if elapsed >= 7:
                    item = {
                        "member_id": mid,
                        "member_name": m.get("full_name"),
                        "phone": m.get("phone"),
                        "member_code": m.get("member_code"),
                        "last_visit": last_date,
                        "days_inactive": elapsed,
                        "contact_status": f_info.get("status", "pending"),
                        "last_note": f_info.get("notes", ""),
                    }
                    categories["all_inactive"].append(item)
                    if 7 <= elapsed <= 14:
                        categories["7_to_14_days"].append(item)
                    elif 15 <= elapsed <= 30:
                        categories["15_to_30_days"].append(item)
                    else:
                        categories["over_30_days"].append(item)

        # Sort by days inactive descending
        for k in categories:
            categories[k].sort(key=lambda x: x["days_inactive"], reverse=True)

        return categories
    except Exception:
        return categories


def log_followup(
    gym_id: str,
    member_id: str,
    contacted_by: str,
    status: str,
    notes: str,
    channel: str = "whatsapp",
) -> Tuple[bool, Optional[str]]:
    """Save an outreach attempt or response note."""
    client = get_supabase_client()
    try:
        today = str(get_ist_today())
        payload = {
            "id": str(uuid.uuid4()),
            "gym_id": gym_id,
            "member_id": member_id,
            "contacted_by": contacted_by,
            "contact_date": today,
            "channel": channel,
            "status": status,
            "notes": notes,
        }
        client.table("inactivity_followups").insert(payload).execute()
        return True, None
    except Exception as e:
        return False, f"Failed to log followup: {str(e)}"
