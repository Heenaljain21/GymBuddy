"""Membership renewal management service for GYM BUDDY.

Categorizes memberships approaching expiry (7, 15, 30 days, expired),
executes plan renewals, and tracks renewal history.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import uuid
from utils.security import get_supabase_client
from utils.date_utils import get_ist_today, days_remaining
from .member_service import _latest_memberships


def get_expiring_memberships(gym_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Bucket each member's current membership by days remaining (buckets are exclusive)."""
    client = get_supabase_client()
    categories: Dict[str, List[Dict[str, Any]]] = {
        "within_7_days": [],
        "within_15_days": [],
        "within_30_days": [],
        "expired": [],
        "all": [],
    }

    try:
        mships = client.table("member_memberships").select("*").eq("gym_id", gym_id).execute().data or []
        members = client.table("members").select("*").eq("gym_id", gym_id).execute().data or []
        plans = client.table("membership_plans").select("*").eq("gym_id", gym_id).execute().data or []
    except Exception:
        return categories

    mem_map = {m["id"]: m for m in members}
    plan_map = {p["id"]: p for p in plans}

    for mid, mship in _latest_memberships(mships).items():
        m_info = mem_map.get(mid)
        if not m_info:
            continue
        end_date_str = mship.get("end_date")
        rem = days_remaining(end_date_str)
        p_info = plan_map.get(mship.get("plan_id"), {})
        item = {
            "membership_id": mship.get("id"),
            "member_id": mid,
            "member_name": m_info.get("full_name", "Member"),
            "phone": m_info.get("phone", "-"),
            "member_code": m_info.get("member_code", "-"),
            "plan_id": mship.get("plan_id"),
            "plan_name": p_info.get("name", "Standard"),
            "plan_price": float(p_info.get("price") or 0),
            "start_date": mship.get("start_date"),
            "expiry_date": end_date_str,
            "days_remaining": rem,
            "status": "expired" if rem < 0 else "active",
        }
        categories["all"].append(item)
        if rem < 0:
            categories["expired"].append(item)
        elif rem <= 7:
            categories["within_7_days"].append(item)
        elif rem <= 15:
            categories["within_15_days"].append(item)
        elif rem <= 30:
            categories["within_30_days"].append(item)

    for k in categories:
        categories[k].sort(key=lambda x: x["days_remaining"])
    return categories


def renew_membership(
    gym_id: str,
    member_id: str,
    new_plan_id: str,
    amount_paid: float,
    payment_method: str = "Cash",
    transaction_ref: str = "",
) -> Tuple[bool, Optional[str]]:
    """Renew a membership: extend from the current end date (or today if lapsed) and record payment."""
    client = get_supabase_client()
    try:
        today = get_ist_today()
        plan_res = client.table("membership_plans").select("*").eq("id", new_plan_id).execute()
        if not plan_res.data:
            return False, "Selected membership plan not found."
        plan = plan_res.data[0]
        duration_days = int(plan.get("duration_days", 30))

        existing_rows = client.table("member_memberships").select("*").eq("gym_id", gym_id).eq("member_id", member_id).execute().data or []
        existing = _latest_memberships(existing_rows).get(member_id)

        start_from = today
        if existing and existing.get("end_date"):
            try:
                curr_end = date.fromisoformat(str(existing["end_date"])[:10])
                if curr_end > today:
                    start_from = curr_end
            except ValueError:
                pass

        new_start = str(start_from if not existing or start_from == today else existing.get("start_date"))
        new_end = str(start_from + timedelta(days=duration_days))

        if existing:
            client.table("member_memberships").update({
                "plan_id": new_plan_id,
                "start_date": new_start,
                "end_date": new_end,
                "status": "active",
                "amount_paid": amount_paid,
            }).eq("id", existing["id"]).execute()
        else:
            client.table("member_memberships").insert({
                "id": str(uuid.uuid4()),
                "gym_id": gym_id,
                "member_id": member_id,
                "plan_id": new_plan_id,
                "start_date": new_start,
                "end_date": new_end,
                "status": "active",
                "amount_paid": amount_paid,
            }).execute()

        if amount_paid > 0:
            client.table("payments").insert({
                "id": str(uuid.uuid4()),
                "gym_id": gym_id,
                "member_id": member_id,
                "amount": amount_paid,
                "payment_date": str(today),
                "payment_method": payment_method,
                "transaction_ref": transaction_ref,
                "receipt_no": f"REC-{today.year}-{str(uuid.uuid4())[:6].upper()}",
                "remarks": f"Renewal: {plan.get('name')}",
            }).execute()

        client.table("renewal_records").insert({
            "id": str(uuid.uuid4()),
            "gym_id": gym_id,
            "member_id": member_id,
            "old_plan_id": existing.get("plan_id") if existing else None,
            "new_plan_id": new_plan_id,
            "renewal_date": str(today),
            "amount_paid": amount_paid,
            "new_end_date": new_end,
        }).execute()

        # A renewed member is, by definition, an active member again.
        client.table("members").update({"is_active": True}).eq("id", member_id).execute()
        return True, None
    except Exception as e:
        return False, f"Renewal failed: {e}"


def get_renewal_summary(gym_id: str) -> Dict[str, int]:
    cats = get_expiring_memberships(gym_id)
    return {
        "within_7_days": len(cats["within_7_days"]),
        "within_15_days": len(cats["within_15_days"]),
        "within_30_days": len(cats["within_30_days"]),
        "expired": len(cats["expired"]),
        "total": len(cats["all"]),
    }
