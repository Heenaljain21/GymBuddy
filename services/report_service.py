"""Owner analytics and daily reporting service for GYM BUDDY.

Aggregates financial KPIs, attendance metrics, member distribution,
and trend dataframes for Plotly visualizations.
"""

from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, Any

import pandas as pd

from utils.security import get_supabase_client
from utils.date_utils import get_ist_today, days_remaining
from .payment_service import get_payments
from .inactivity_service import get_inactive_members
from .member_service import get_members


def _to_date(value) -> date | None:
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def get_dashboard_stats(gym_id: str) -> Dict[str, Any]:
    """Core KPI numbers for owner/staff dashboards."""
    client = get_supabase_client()
    today = get_ist_today()
    today_str = str(today)
    start_of_month = str(today.replace(day=1))

    stats: Dict[str, Any] = {
        "total_members": 0,
        "active_members": 0,
        "expiring_7_days": 0,
        "today_attendance": 0,
        "monthly_revenue": 0.0,
        "today_revenue": 0.0,
        "inactive_members": 0,
        "new_this_month": 0,
    }

    try:
        members = get_members(gym_id)
        stats["total_members"] = len(members)
        stats["active_members"] = sum(1 for m in members if m["membership_status"] in ("active", "expiring"))
        stats["expiring_7_days"] = sum(1 for m in members if m["membership_status"] == "expiring")
        stats["new_this_month"] = sum(1 for m in members if str(m.get("joined_date") or "") >= start_of_month)

        att = client.table("attendance").select("id").eq("gym_id", gym_id).eq("check_in_date", today_str).execute()
        stats["today_attendance"] = len(att.data or [])

        for p in get_payments(gym_id, start_date=start_of_month):
            amt = float(p.get("amount") or 0.0)
            stats["monthly_revenue"] += amt
            if str(p.get("payment_date")) == today_str:
                stats["today_revenue"] += amt

        stats["inactive_members"] = len(get_inactive_members(gym_id, threshold_days=7)["all_inactive"])
    except Exception:
        pass
    return stats


def get_daily_revenue_chart(gym_id: str, days: int = 30) -> pd.DataFrame:
    """Daily revenue for the last `days` days (inclusive of today)."""
    today = get_ist_today()
    start = today - timedelta(days=max(days, 1) - 1)
    buckets = {start + timedelta(days=i): 0.0 for i in range((today - start).days + 1)}
    for p in get_payments(gym_id, start_date=start, end_date=today):
        d = _to_date(p.get("payment_date"))
        if d in buckets:
            buckets[d] += float(p.get("amount") or 0.0)
    return pd.DataFrame([{"date": d, "amount": amt} for d, amt in buckets.items()])


def get_monthly_revenue_chart(gym_id: str, months: int = 6) -> pd.DataFrame:
    """Revenue grouped by calendar month for the last `months` months, in chronological order."""
    today = get_ist_today()
    keys = []
    y, m = today.year, today.month
    for _ in range(months):
        keys.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    keys.reverse()
    totals = {k: 0.0 for k in keys}
    for p in get_payments(gym_id):
        d = _to_date(p.get("payment_date"))
        if d and (d.year, d.month) in totals:
            totals[(d.year, d.month)] += float(p.get("amount") or 0.0)
    return pd.DataFrame([
        {"month": date(y, m, 1).strftime("%b %Y"), "amount": amt} for (y, m), amt in totals.items()
    ])


def get_attendance_trends(gym_id: str, days: int = 14) -> pd.DataFrame:
    """Daily check-in counts for the last `days` days (inclusive of today)."""
    client = get_supabase_client()
    today = get_ist_today()
    start = today - timedelta(days=max(days, 1) - 1)
    buckets = {start + timedelta(days=i): 0 for i in range((today - start).days + 1)}
    try:
        rows = client.table("attendance").select("check_in_date").eq("gym_id", gym_id).gte("check_in_date", str(start)).execute().data or []
    except Exception:
        rows = []
    for a in rows:
        d = _to_date(a.get("check_in_date"))
        if d in buckets:
            buckets[d] += 1
    return pd.DataFrame([{"date": d, "count": c} for d, c in buckets.items()])


def get_peak_hours(gym_id: str, days: int = 30) -> pd.DataFrame:
    """Check-in counts by hour of day over the last `days` days."""
    client = get_supabase_client()
    start = get_ist_today() - timedelta(days=days)
    try:
        rows = client.table("attendance").select("check_in_time").eq("gym_id", gym_id).gte("check_in_date", str(start)).execute().data or []
    except Exception:
        rows = []
    counts = {h: 0 for h in range(5, 23)}
    for r in rows:
        try:
            h = int(str(r.get("check_in_time"))[:2])
        except ValueError:
            continue
        if h in counts:
            counts[h] += 1
    return pd.DataFrame([{"hour": f"{(h % 12) or 12} {'AM' if h < 12 else 'PM'}", "count": c} for h, c in counts.items()])


def get_membership_distribution(gym_id: str) -> pd.DataFrame:
    """Number of members on each plan, counting only currently valid memberships."""
    members = get_members(gym_id)
    counts: Dict[str, int] = {}
    for m in members:
        if m["membership_status"] in ("active", "expiring"):
            counts[m["plan_name"]] = counts.get(m["plan_name"], 0) + 1
    return pd.DataFrame([{"plan": k, "count": v} for k, v in counts.items()], columns=["plan", "count"])


def get_member_growth_chart(gym_id: str, days: int = 180) -> pd.DataFrame:
    """Cumulative member count over time, based on each member's joining date."""
    today = get_ist_today()
    start = today - timedelta(days=days)
    joins = []
    for m in get_members(gym_id):
        d = _to_date(m.get("joined_date")) or _to_date(m.get("start_date")) or _to_date(m.get("created_at"))
        joins.append(d or today)
    joins.sort()
    base = sum(1 for d in joins if d < start)
    points = []
    step = max(days // 12, 1)
    cursor = start
    while cursor <= today:
        points.append({"date": cursor, "total": base + sum(1 for d in joins if start <= d <= cursor)})
        cursor += timedelta(days=step)
    if points[-1]["date"] != today:
        points.append({"date": today, "total": len(joins)})
    return pd.DataFrame(points)


def get_expiry_outlook(gym_id: str) -> pd.DataFrame:
    """Count of members whose plan ends in each upcoming week (next 4 weeks)."""
    buckets = {"This week": 0, "Next week": 0, "In 2 weeks": 0, "In 3 weeks": 0}
    labels = list(buckets)
    for m in get_members(gym_id):
        if m.get("expiry_date") and m["membership_status"] != "inactive":
            rem = days_remaining(m["expiry_date"])
            if 0 <= rem < 28:
                buckets[labels[rem // 7]] += 1
    return pd.DataFrame([{"week": k, "count": v} for k, v in buckets.items()])
