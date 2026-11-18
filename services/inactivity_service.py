"""Inactive and missing members tracking service for GYM BUDDY.

Identifies absent gym members by days inactive (7-14, 15-30, 30+, never attended),
generates retention WhatsApp communications, and tracks follow-up records.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import uuid
from utils.security import get_supabase_client
from utils.date_utils import get_ist_today, days_since

NEVER = 999


def get_inactive_members(
    gym_id: str,
    threshold_days: int = 7,
) -> Dict[str, List[Dict[str, Any]]]:
    """Identify active members absent for at least `threshold_days`, grouped by absence length."""
    client = get_supabase_client()
    categories: Dict[str, List[Dict[str, Any]]] = {
        "7_to_14_days": [],
        "15_to_30_days": [],
        "over_30_days": [],
        "never_attended": [],
        "all_inactive": [],
    }

    try:
        members = client.table("members").select("*").eq("gym_id", gym_id).eq("is_active", True).execute().data or []
        attendance = client.table("attendance").select("member_id, check_in_date").eq("gym_id", gym_id).execute().data or []
        followups = client.table("inactivity_followups").select("*").eq("gym_id", gym_id).execute().data or []
    except Exception:
        return categories

    last_visit: Dict[str, str] = {}
    for a in attendance:
        mid, dt = a.get("member_id"), str(a.get("check_in_date") or "")
        if dt > last_visit.get(mid, ""):
            last_visit[mid] = dt

    # Latest follow-up per member (by contact date, then insertion order).
    latest_follow: Dict[str, Dict[str, Any]] = {}
    for f in followups:
        mid = f.get("member_id")
        if mid not in latest_follow or str(f.get("contact_date") or "") >= str(latest_follow[mid].get("contact_date") or ""):
            latest_follow[mid] = f

    for m in members:
        mid = m.get("id")
        last = last_visit.get(mid)
        elapsed = days_since(last) if last else NEVER
        if elapsed < threshold_days:
            continue
        follow = latest_follow.get(mid, {})
        item = {
            "member_id": mid,
            "member_name": m.get("full_name"),
            "phone": m.get("phone"),
            "member_code": m.get("member_code"),
            "joined_date": m.get("joined_date"),
            "last_visit": last,
            "days_inactive": elapsed,
            "contact_status": follow.get("status", "pending"),
            "last_note": follow.get("notes", ""),
            "last_contact_date": follow.get("contact_date"),
        }
        categories["all_inactive"].append(item)
        if elapsed == NEVER:
            categories["never_attended"].append(item)
        elif elapsed <= 14:
            categories["7_to_14_days"].append(item)
        elif elapsed <= 30:
            categories["15_to_30_days"].append(item)
        else:
            categories["over_30_days"].append(item)

    for k in categories:
        categories[k].sort(key=lambda x: x["days_inactive"], reverse=True)
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
        client.table("inactivity_followups").insert({
            "id": str(uuid.uuid4()),
            "gym_id": gym_id,
            "member_id": member_id,
            "contacted_by": contacted_by,
            "contact_date": str(get_ist_today()),
            "channel": channel,
            "status": status,
            "notes": notes,
        }).execute()
        return True, None
    except Exception as e:
        return False, f"Failed to log follow-up: {e}"
