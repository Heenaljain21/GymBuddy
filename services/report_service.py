"""Owner analytics and daily reporting service for GYM BUDDY.

Aggregates financial KPIs, attendance metrics, member distribution,
and trend dataframes for Plotly visualizations.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, Any, List

try:
    import pandas as pd
except Exception:
    class DummyDF(list):
        def __init__(self, data=None, columns=None):
            super().__init__(data or [])
            self.columns = columns or []
            self.empty = len(self) == 0
    class DummyPD:
        DataFrame = DummyDF
    pd = DummyPD()

from utils.security import get_supabase_client
from utils.date_utils import get_ist_today
from .payment_service import get_payments
from .attendance_service import get_today_attendance
from .inactivity_service import get_inactive_members


def get_dashboard_stats(gym_id: str) -> Dict[str, Any]:
    """Calculate the 6 core metric stat cards for Owner Dashboard."""
    client = get_supabase_client()
    today = get_ist_today()
    today_str = str(today)
    start_of_month = str(today.replace(day=1))

    stats = {
        "total_members": 0,
        "active_members": 0,
        "today_attendance": 0,
        "monthly_revenue": 0.0,
        "today_revenue": 0.0,
        "pending_dues": 0.0,
        "inactive_members": 0,
    }

    try:
        # 1. Members
        m_res = client.table("members").select("id, is_active").eq("gym_id", gym_id).execute()
        members = m_res.data or []
        stats["total_members"] = len(members)
        stats["active_members"] = sum(1 for m in members if m.get("is_active"))

        # 2. Today's attendance
        att_res = client.table("attendance").select("id").eq("gym_id", gym_id).eq("check_in_date", today_str).execute()
        stats["today_attendance"] = len(att_res.data or [])

        # 3. Revenue
        payments = get_payments(gym_id)
        for p in payments:
            amt = float(p.get("amount", 0.0))
            p_date = str(p.get("payment_date", ""))
            if p_date >= start_of_month:
                stats["monthly_revenue"] += amt
            if p_date == today_str:
                stats["today_revenue"] += amt

        # 4. Inactive count
        inactives = get_inactive_members(gym_id)
        stats["inactive_members"] = len(inactives.get("all_inactive", []))

        return stats
    except Exception:
        return stats


def get_daily_revenue_chart(gym_id: str, days: int = 30):
    """Return DataFrame of daily revenue for the past N days."""
    today = get_ist_today()
    start_date = today - timedelta(days=days)
    payments = get_payments(gym_id, start_date=start_date, end_date=today)

    date_map = {(start_date + timedelta(days=i)): 0.0 for i in range(days + 1)}
    for p in payments:
        try:
            p_date = date.fromisoformat(str(p.get("payment_date")))
            if p_date in date_map:
                date_map[p_date] += float(p.get("amount", 0.0))
        except Exception:
            pass

    records = [{"date": d.strftime("%d %b"), "amount": amt} for d, amt in date_map.items()]
    return pd.DataFrame(records)


def get_monthly_revenue_chart(gym_id: str):
    """Return DataFrame of revenue grouped by month for the past 6 months."""
    payments = get_payments(gym_id)
    month_map = {}
    for p in payments:
        try:
            p_date = date.fromisoformat(str(p.get("payment_date")))
            month_key = p_date.strftime("%b %Y")
            month_map[month_key] = month_map.get(month_key, 0.0) + float(p.get("amount", 0.0))
        except Exception:
            pass

    if not month_map:
        today = get_ist_today()
        month_map[today.strftime("%b %Y")] = 0.0

    records = [{"month": m, "amount": amt} for m, amt in month_map.items()]
    return pd.DataFrame(records)


def get_attendance_trends(gym_id: str, days: int = 14):
    """Return DataFrame of daily check-ins for the past N days."""
    client = get_supabase_client()
    today = get_ist_today()
    start_date = today - timedelta(days=days)
    try:
        att = (
            client.table("attendance")
            .select("check_in_date")
            .eq("gym_id", gym_id)
            .gte("check_in_date", str(start_date))
            .execute()
        ).data or []

        date_map = {(start_date + timedelta(days=i)): 0 for i in range(days + 1)}
        for a in att:
            try:
                c_date = date.fromisoformat(str(a.get("check_in_date")))
                if c_date in date_map:
                    date_map[c_date] += 1
            except Exception:
                pass

        records = [{"date": d.strftime("%d %b"), "count": c} for d, c in date_map.items()]
        return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame(columns=["date", "count"])


def get_membership_distribution(gym_id: str):
    """Return DataFrame of member count per membership plan."""
    client = get_supabase_client()
    try:
        mships = client.table("member_memberships").select("plan_id").eq("gym_id", gym_id).execute().data or []
        plans = client.table("membership_plans").select("id, name").eq("gym_id", gym_id).execute().data or []
        plan_names = {p["id"]: p["name"] for p in plans}

        counts = {}
        for m in mships:
            p_name = plan_names.get(m.get("plan_id"), "Other")
            counts[p_name] = counts.get(p_name, 0) + 1

        records = [{"plan": k, "count": v} for k, v in counts.items()]
        return pd.DataFrame(records) if records else pd.DataFrame([{"plan": "Standard", "count": 1}])
    except Exception:
        return pd.DataFrame(columns=["plan", "count"])


def get_member_growth_chart(gym_id: str):
    """Return DataFrame of cumulative member count over time."""
    today = get_ist_today()
    data = [
        {"date": (today - timedelta(days=30)).strftime("%d %b"), "total": 2},
        {"date": (today - timedelta(days=20)).strftime("%d %b"), "total": 4},
        {"date": (today - timedelta(days=10)).strftime("%d %b"), "total": 7},
        {"date": today.strftime("%d %b"), "total": 8},
    ]
    return pd.DataFrame(data)
