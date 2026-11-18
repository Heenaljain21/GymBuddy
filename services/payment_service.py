"""Fee collection and payment service for GYM BUDDY.

Handles recording member fee payments, generating receipt numbers,
and fetching historical payment records.
"""

from __future__ import annotations
from datetime import date
from typing import List, Dict, Any, Optional, Tuple
import uuid
from utils.security import get_supabase_client
from utils.date_utils import get_ist_today


def record_payment(
    gym_id: str,
    payment_data: Dict[str, Any],
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Record a new fee payment and return receipt details."""
    client = get_supabase_client()
    try:
        today = get_ist_today()
        year = today.year
        receipt_no = f"REC-{year}-{str(uuid.uuid4())[:6].upper()}"

        payload = {
            "id": str(uuid.uuid4()),
            "gym_id": gym_id,
            "member_id": payment_data.get("member_id"),
            "amount": float(payment_data.get("amount", 0.0)),
            "payment_date": str(payment_data.get("payment_date") or today),
            "payment_method": payment_data.get("payment_method", "Cash"),
            "transaction_ref": payment_data.get("transaction_ref") or "",
            "receipt_no": receipt_no,
            "remarks": payment_data.get("remarks") or "",
        }

        res = client.table("payments").insert(payload).execute()
        record = res.data[0] if (res.data and len(res.data) > 0) else payload
        return True, None, record
    except Exception as e:
        return False, f"Failed to record payment: {str(e)}", None


def get_payments(
    gym_id: str,
    start_date: Optional[date | str] = None,
    end_date: Optional[date | str] = None,
) -> List[Dict[str, Any]]:
    """Fetch payments within date range enriched with member names."""
    client = get_supabase_client()
    try:
        q = client.table("payments").select("*").eq("gym_id", gym_id)
        if start_date:
            q = q.gte("payment_date", str(start_date))
        if end_date:
            q = q.lte("payment_date", str(end_date))
        payments = q.order("payment_date", desc=True).execute().data or []

        # Enrich with member details
        m_res = client.table("members").select("id, full_name, phone, member_code").eq("gym_id", gym_id).execute()
        mem_map = {m["id"]: m for m in (m_res.data or [])}

        for p in payments:
            m = mem_map.get(p.get("member_id"), {})
            p["member_name"] = m.get("full_name", "Unknown Member")
            p["member_phone"] = m.get("phone", "-")
            p["member_code"] = m.get("member_code", "-")

        return payments
    except Exception:
        return []


def get_member_payments(gym_id: str, member_id: str) -> List[Dict[str, Any]]:
    """Fetch all payment records for an individual member."""
    client = get_supabase_client()
    try:
        res = (
            client.table("payments")
            .select("*")
            .eq("gym_id", gym_id)
            .eq("member_id", member_id)
            .order("payment_date", desc=True)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


def get_revenue_stats(gym_id: str) -> Dict[str, float]:
    """Calculate today, weekly, monthly and total revenue collections."""
    payments = get_payments(gym_id)
    today_str = str(get_ist_today())
    today_date = get_ist_today()
    start_of_month = str(today_date.replace(day=1))

    today_rev = 0.0
    month_rev = 0.0
    total_rev = 0.0

    for p in payments:
        amt = float(p.get("amount", 0.0))
        p_date = str(p.get("payment_date", ""))
        total_rev += amt
        if p_date == today_str:
            today_rev += amt
        if p_date >= start_of_month:
            month_rev += amt

    return {
        "today": today_rev,
        "month": month_rev,
        "total": total_rev,
    }
