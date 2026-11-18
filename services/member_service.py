"""Member management service for GYM BUDDY.

Handles registration, unique member code generation, search, profile details,
and membership linkage.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import uuid
from utils.security import get_supabase_client
from utils.date_utils import get_ist_today


def _generate_member_code(gym_id: str) -> str:
    """Generate next sequential unique member code, e.g. GMB-2026-009."""
    client = get_supabase_client()
    today = get_ist_today()
    year = today.year
    prefix = f"GMB-{year}-"
    try:
        res = client.table("members").select("member_code").eq("gym_id", gym_id).execute()
        existing = [r.get("member_code", "") for r in (res.data or []) if r.get("member_code", "").startswith(prefix)]
        numbers = []
        for c in existing:
            try:
                num = int(c.split("-")[-1])
                numbers.append(num)
            except Exception:
                pass
        next_num = max(numbers) + 1 if numbers else 1
        return f"{prefix}{next_num:03d}"
    except Exception:
        return f"{prefix}{str(uuid.uuid4())[:4].upper()}"


def register_member(
    gym_id: str,
    form_data: Dict[str, Any],
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Register a new member, create active membership and payment record."""
    client = get_supabase_client()
    try:
        phone = form_data.get("phone", "").strip()
        # Check duplicate phone in same gym
        dup = client.table("members").select("id").eq("gym_id", gym_id).eq("phone", phone).execute()
        if dup.data and len(dup.data) > 0:
            return False, f"A member with phone number {phone} is already registered.", None

        member_code = _generate_member_code(gym_id)
        member_id = str(uuid.uuid4())

        member_payload = {
            "id": member_id,
            "gym_id": gym_id,
            "user_id": form_data.get("user_id"),
            "member_code": member_code,
            "full_name": form_data.get("full_name"),
            "phone": phone,
            "email": form_data.get("email") or None,
            "age": form_data.get("age"),
            "gender": form_data.get("gender"),
            "address": form_data.get("address"),
            "emergency_contact": form_data.get("emergency_contact"),
            "qr_code_data": member_code,
            "is_active": True,
        }

        m_res = client.table("members").insert(member_payload).execute()

        # Link plan if provided
        plan_id = form_data.get("plan_id")
        if plan_id:
            duration_days = int(form_data.get("duration_days", 30))
            amount_paid = float(form_data.get("amount_paid", 0.0))
            start_date = form_data.get("start_date") or get_ist_today()
            if isinstance(start_date, date):
                start_date_str = str(start_date)
                end_date_str = str(start_date + timedelta(days=duration_days))
            else:
                start_date_str = str(start_date)
                end_date_str = str(date.fromisoformat(start_date_str) + timedelta(days=duration_days))

            membership_payload = {
                "id": str(uuid.uuid4()),
                "gym_id": gym_id,
                "member_id": member_id,
                "plan_id": plan_id,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "status": "active",
                "amount_paid": amount_paid,
            }
            client.table("member_memberships").insert(membership_payload).execute()

            # Record initial payment
            payment_method = form_data.get("payment_method", "Cash")
            receipt_no = f"REC-{get_ist_today().year}-{str(uuid.uuid4())[:6].upper()}"
            payment_payload = {
                "id": str(uuid.uuid4()),
                "gym_id": gym_id,
                "member_id": member_id,
                "amount": amount_paid,
                "payment_date": start_date_str,
                "payment_method": payment_method,
                "transaction_ref": form_data.get("transaction_ref", ""),
                "receipt_no": receipt_no,
            }
            client.table("payments").insert(payment_payload).execute()

        return True, None, member_payload
    except Exception as e:
        return False, f"Registration failed: {str(e)}", None


def get_members(gym_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
    """Fetch all members of a gym with their current membership status."""
    client = get_supabase_client()
    try:
        q = client.table("members").select("*").eq("gym_id", gym_id)
        if active_only:
            q = q.eq("is_active", True)
        members = q.order("full_name").execute().data or []

        # Enrich with current membership
        memberships = client.table("member_memberships").select("*").eq("gym_id", gym_id).execute().data or []
        plans = client.table("membership_plans").select("*").eq("gym_id", gym_id).execute().data or []
        plan_dict = {p["id"]: p for p in plans}
        m_dict = {m["member_id"]: m for m in memberships}

        for mem in members:
            mem_ship = m_dict.get(mem["id"])
            if mem_ship:
                mem["current_membership"] = mem_ship
                mem["plan_name"] = plan_dict.get(mem_ship.get("plan_id"), {}).get("name", "Standard")
                mem["expiry_date"] = mem_ship.get("end_date")
                mem["membership_status"] = mem_ship.get("status", "active")
            else:
                mem["plan_name"] = "No Plan"
                mem["expiry_date"] = None
                mem["membership_status"] = "inactive"

        return members
    except Exception:
        return []


def search_members(gym_id: str, query: str) -> List[Dict[str, Any]]:
    """Search members by name, phone, or member code."""
    all_members = get_members(gym_id)
    if not query:
        return all_members
    q = query.strip().lower()
    return [
        m for m in all_members
        if q in m.get("full_name", "").lower()
        or q in m.get("phone", "")
        or q in m.get("member_code", "").lower()
    ]


def get_member_by_qr(gym_id: str, qr_data: str) -> Optional[Dict[str, Any]]:
    """Resolve member by scanned QR code data or member code."""
    clean_data = qr_data.strip()
    all_members = get_members(gym_id)
    for m in all_members:
        if m.get("qr_code_data") == clean_data or m.get("member_code") == clean_data or m.get("phone") == clean_data:
            return m
    return None
