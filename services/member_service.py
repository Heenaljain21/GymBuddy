"""Member management service for GYM BUDDY.

Handles registration, unique member code generation, search, profile details,
membership linkage, and trainer assignment.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
import uuid
from utils.security import get_supabase_client
from utils.date_utils import get_ist_today, days_remaining


def _generate_member_code(gym_id: str) -> str:
    """Generate next sequential unique member code, e.g. GMB-2026-009."""
    client = get_supabase_client()
    prefix = f"GMB-{get_ist_today().year}-"
    try:
        res = client.table("members").select("member_code").eq("gym_id", gym_id).execute()
        numbers = []
        for r in res.data or []:
            code = r.get("member_code") or ""
            if code.startswith(prefix):
                try:
                    numbers.append(int(code.split("-")[-1]))
                except ValueError:
                    pass
        return f"{prefix}{(max(numbers) + 1 if numbers else 1):03d}"
    except Exception:
        return f"{prefix}{str(uuid.uuid4())[:4].upper()}"


def _digits(phone: str) -> str:
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    return digits[2:] if len(digits) == 12 and digits.startswith("91") else digits


def register_member(
    gym_id: str,
    form_data: Dict[str, Any],
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Register a new member, create active membership and payment record."""
    client = get_supabase_client()
    try:
        phone = _digits(form_data.get("phone", ""))
        dup = client.table("members").select("id, full_name").eq("gym_id", gym_id).eq("phone", phone).execute()
        if dup.data:
            return False, f"Phone {phone} is already registered to {dup.data[0].get('full_name')}.", None

        member_code = _generate_member_code(gym_id)
        member_id = str(uuid.uuid4())
        today = get_ist_today()

        member_payload = {
            "id": member_id,
            "gym_id": gym_id,
            "user_id": form_data.get("user_id"),
            "member_code": member_code,
            "full_name": (form_data.get("full_name") or "").strip(),
            "phone": phone,
            "email": (form_data.get("email") or "").strip() or None,
            "age": form_data.get("age"),
            "gender": form_data.get("gender"),
            "address": form_data.get("address"),
            "emergency_contact": _digits(form_data.get("emergency_contact", "")) or None,
            "qr_code_data": member_code,
            "is_active": True,
            "joined_date": str(today),
        }
        client.table("members").insert(member_payload).execute()

        plan_id = form_data.get("plan_id")
        if plan_id:
            duration_days = int(form_data.get("duration_days", 30))
            amount_paid = float(form_data.get("amount_paid", 0.0))
            start = form_data.get("start_date") or today
            if not isinstance(start, date):
                start = date.fromisoformat(str(start))
            end = start + timedelta(days=duration_days)

            client.table("member_memberships").insert({
                "id": str(uuid.uuid4()),
                "gym_id": gym_id,
                "member_id": member_id,
                "plan_id": plan_id,
                "start_date": str(start),
                "end_date": str(end),
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
                    "payment_method": form_data.get("payment_method", "Cash"),
                    "transaction_ref": form_data.get("transaction_ref", ""),
                    "receipt_no": f"REC-{today.year}-{str(uuid.uuid4())[:6].upper()}",
                    "remarks": "New member registration",
                }).execute()

            member_payload["expiry_date"] = str(end)

        return True, None, member_payload
    except Exception as e:
        return False, f"Registration failed: {e}", None


def _latest_memberships(memberships: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Map member_id -> the membership with the furthest end date."""
    latest: Dict[str, Dict[str, Any]] = {}
    for ms in memberships:
        mid = ms.get("member_id")
        if mid not in latest or str(ms.get("end_date") or "") > str(latest[mid].get("end_date") or ""):
            latest[mid] = ms
    return latest


def membership_status(member: Dict[str, Any]) -> str:
    """Derive a single display status: active / expiring / expired / no_plan / inactive."""
    if member.get("is_active") is False:
        return "inactive"
    expiry = member.get("expiry_date")
    if not expiry:
        return "no_plan"
    rem = days_remaining(expiry)
    if rem < 0:
        return "expired"
    if rem <= 7:
        return "expiring"
    return "active"


def get_members(gym_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
    """Fetch all members of a gym enriched with current plan, expiry, status and last visit."""
    client = get_supabase_client()
    try:
        q = client.table("members").select("*").eq("gym_id", gym_id)
        if active_only:
            q = q.eq("is_active", True)
        members = q.order("full_name").execute().data or []

        memberships = client.table("member_memberships").select("*").eq("gym_id", gym_id).execute().data or []
        plans = client.table("membership_plans").select("id, name").eq("gym_id", gym_id).execute().data or []
        attendance = client.table("attendance").select("member_id, check_in_date").eq("gym_id", gym_id).execute().data or []

        plan_names = {p["id"]: p["name"] for p in plans}
        latest = _latest_memberships(memberships)
        last_visit: Dict[str, str] = {}
        for a in attendance:
            mid, dt = a.get("member_id"), str(a.get("check_in_date") or "")
            if dt > last_visit.get(mid, ""):
                last_visit[mid] = dt

        for mem in members:
            ms = latest.get(mem["id"])
            if ms:
                mem["current_membership"] = ms
                mem["plan_id"] = ms.get("plan_id")
                mem["plan_name"] = plan_names.get(ms.get("plan_id"), "Standard")
                mem["start_date"] = ms.get("start_date")
                mem["expiry_date"] = ms.get("end_date")
            else:
                mem["plan_name"] = "No Plan"
                mem["expiry_date"] = None
            mem["membership_status"] = membership_status(mem)
            mem["last_visit"] = last_visit.get(mem["id"])

        return members
    except Exception:
        return []


def get_member(gym_id: str, member_id: str) -> Optional[Dict[str, Any]]:
    return next((m for m in get_members(gym_id) if m["id"] == member_id), None)


def search_members(gym_id: str, query: str, members: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """Search members by name, phone, or member code."""
    all_members = members if members is not None else get_members(gym_id)
    q = (query or "").strip().lower()
    if not q:
        return all_members
    return [
        m for m in all_members
        if q in (m.get("full_name") or "").lower()
        or q in (m.get("phone") or "")
        or q in (m.get("member_code") or "").lower()
    ]


def get_member_by_qr(gym_id: str, qr_data: str) -> Optional[Dict[str, Any]]:
    """Resolve member by scanned QR payload, member code, or phone number."""
    clean = (qr_data or "").strip()
    if not clean:
        return None
    upper, phone = clean.upper(), _digits(clean)
    for m in get_members(gym_id):
        if (m.get("qr_code_data") or "").upper() == upper or (m.get("member_code") or "").upper() == upper:
            return m
        if phone and len(phone) == 10 and m.get("phone") == phone:
            return m
    return None


def update_member(member_id: str, fields: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    try:
        get_supabase_client().table("members").update(fields).eq("id", member_id).execute()
        return True, None
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Trainer assignments
# ---------------------------------------------------------------------------

def get_trainers(gym_id: str) -> List[Dict[str, Any]]:
    client = get_supabase_client()
    try:
        return client.table("profiles").select("*").eq("gym_id", gym_id).eq("role", "trainer").order("full_name").execute().data or []
    except Exception:
        return []


def get_assignments(gym_id: str) -> Dict[str, str]:
    """Map member_id -> trainer_id for active assignments."""
    client = get_supabase_client()
    try:
        rows = client.table("trainer_assignments").select("*").eq("gym_id", gym_id).execute().data or []
    except Exception:
        return {}
    return {r["member_id"]: r["trainer_id"] for r in rows if r.get("is_active", True)}


def get_trainer_member_ids(gym_id: str, trainer_id: str) -> set:
    return {mid for mid, tid in get_assignments(gym_id).items() if tid == trainer_id}


def assign_trainer(gym_id: str, member_id: str, trainer_id: Optional[str]) -> Tuple[bool, Optional[str]]:
    """Assign (or unassign with None) a trainer to a member."""
    client = get_supabase_client()
    try:
        client.table("trainer_assignments").delete().eq("gym_id", gym_id).eq("member_id", member_id).execute()
        if trainer_id:
            client.table("trainer_assignments").insert({
                "id": str(uuid.uuid4()),
                "gym_id": gym_id,
                "trainer_id": trainer_id,
                "member_id": member_id,
                "assigned_date": str(get_ist_today()),
                "is_active": True,
            }).execute()
        return True, None
    except Exception as e:
        return False, str(e)
