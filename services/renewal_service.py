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


def get_expiring_memberships(gym_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """Categorize active memberships by days remaining to expiry."""
    client = get_supabase_client()
    today = get_ist_today()

    categories = {
        "within_7_days": [],
        "within_15_days": [],
        "within_30_days": [],
        "expired": [],
        "all": [],
    }

    try:
        # Fetch memberships and members
        mships = client.table("member_memberships").select("*").eq("gym_id", gym_id).execute().data or []
        members = client.table("members").select("id, full_name, phone, member_code").eq("gym_id", gym_id).execute().data or []
        plans = client.table("membership_plans").select("id, name, price, duration_days").eq("gym_id", gym_id).execute().data or []

        mem_map = {m["id"]: m for m in members}
        plan_map = {p["id"]: p for p in plans}

        for mship in mships:
            end_date_str = mship.get("end_date")
            rem = days_remaining(end_date_str)
            m_info = mem_map.get(mship.get("member_id"), {})
            p_info = plan_map.get(mship.get("plan_id"), {})

            item = {
                "membership_id": mship.get("id"),
                "member_id": mship.get("member_id"),
                "member_name": m_info.get("full_name", "Member"),
                "phone": m_info.get("phone", "-"),
                "member_code": m_info.get("member_code", "-"),
                "plan_id": mship.get("plan_id"),
                "plan_name": p_info.get("name", "Standard"),
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

        return categories
    except Exception:
        return categories


def renew_membership(
    gym_id: str,
    member_id: str,
    new_plan_id: str,
    amount_paid: float,
    payment_method: str = "Cash",
    transaction_ref: str = "",
) -> Tuple[bool, Optional[str]]:
    """Renew member membership, extend end_date, and record payment."""
    client = get_supabase_client()
    try:
        today = get_ist_today()
        # Fetch plan duration
        plan_res = client.table("membership_plans").select("*").eq("id", new_plan_id).execute()
        if not plan_res.data:
            return False, "Selected membership plan not found."
        plan = plan_res.data[0]
        duration_days = int(plan.get("duration_days", 30))

        # Check existing active membership
        existing_res = (
            client.table("member_memberships")
            .select("*")
            .eq("gym_id", gym_id)
            .eq("member_id", member_id)
            .execute()
        )
        existing = existing_res.data[0] if existing_res.data else None

        # Calculate new end date
        if existing and existing.get("end_date"):
            try:
                curr_end = date.fromisoformat(existing["end_date"])
                # If current membership hasn't expired yet, extend from current end date
                start_from = curr_end if curr_end > today else today
            except Exception:
                start_from = today
        else:
            start_from = today

        new_start = str(start_from)
        new_end = str(start_from + timedelta(days=duration_days))

        if existing:
            # Update current membership
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

        # Record payment
        receipt_no = f"REC-{today.year}-{str(uuid.uuid4())[:6].upper()}"
        client.table("payments").insert({
            "id": str(uuid.uuid4()),
            "gym_id": gym_id,
            "member_id": member_id,
            "amount": amount_paid,
            "payment_date": str(today),
            "payment_method": payment_method,
            "transaction_ref": transaction_ref,
            "receipt_no": receipt_no,
            "remarks": f"Renewal for plan: {plan.get('name')}",
        }).execute()

        # Log renewal record
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

        return True, None
    except Exception as e:
        return False, f"Renewal failed: {str(e)}"


def get_renewal_summary(gym_id: str) -> Dict[str, int]:
    """Return count breakdown of renewals."""
    cats = get_expiring_memberships(gym_id)
    return {
        "within_7_days": len(cats["within_7_days"]),
        "within_15_days": len(cats["within_15_days"]),
        "within_30_days": len(cats["within_30_days"]),
        "expired": len(cats["expired"]),
        "total": len(cats["all"]),
    }
