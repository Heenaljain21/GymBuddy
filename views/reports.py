"""SCREEN 10 – Owner reports: revenue, footfall, plan mix, growth and upcoming expiries."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.ui import ctx, page_header, require_role, stat_cards
from components.charts import bar_chart, line_chart, donut_chart, LIME, AMBER
from services.report_service import (
    get_dashboard_stats, get_daily_revenue_chart, get_monthly_revenue_chart, get_attendance_trends,
    get_membership_distribution, get_member_growth_chart, get_peak_hours, get_expiry_outlook,
)
from services.payment_service import get_payments
from utils.helpers import format_currency
from utils.date_utils import get_ist_today
from datetime import timedelta

require_role("owner")
c = ctx()
page_header("Reports", f"How {c.gym_name} is performing.", eyebrow="Insights")

horizon = st.segmented_control("Horizon", ["7 days", "30 days", "90 days"], default="30 days", label_visibility="collapsed") or "30 days"
days = int(horizon.split()[0])
today = get_ist_today()

stats = get_dashboard_stats(c.gym_id)
period_pay = get_payments(c.gym_id, start_date=today - timedelta(days=days - 1))
prev_pay = get_payments(c.gym_id, start_date=today - timedelta(days=2 * days - 1), end_date=today - timedelta(days=days))
period_rev = sum(float(p.get("amount") or 0) for p in period_pay)
prev_rev = sum(float(p.get("amount") or 0) for p in prev_pay)
delta = f"{'▲' if period_rev >= prev_rev else '▼'} {abs(period_rev - prev_rev) / prev_rev * 100:.0f}% vs previous {days}d" if prev_rev else "No previous data"
att = get_attendance_trends(c.gym_id, days=days)
avg_daily = att["count"].mean() if not att.empty else 0

stat_cards([
    {"label": f"Revenue · {horizon}", "value": format_currency(period_rev).replace(".00", ""), "icon": "💰", "accent": "lime", "sub": delta},
    {"label": "Avg check-ins / day", "value": f"{avg_daily:.1f}", "icon": "📋", "accent": "cyan", "sub": f"{int(att['count'].sum()) if not att.empty else 0} visits in {horizon}"},
    {"label": "Active members", "value": stats["active_members"], "icon": "⚡", "accent": "purple", "sub": f"{stats['new_this_month']} joined this month"},
    {"label": "Avg ticket", "value": format_currency(period_rev / len(period_pay) if period_pay else 0).replace(".00", ""), "icon": "🧾", "accent": "blue", "sub": f"{len(period_pay)} payments"},
    {"label": "At risk", "value": stats["inactive_members"], "icon": "🔔", "accent": "pink", "sub": "Absent 7+ days"},
])

l, r = st.columns(2)
with l:
    bar_chart(get_daily_revenue_chart(c.gym_id, days=days), "date", "amount", f"Daily revenue · {horizon}", money=True)
with r:
    line_chart(att, "date", "count", f"Daily check-ins · {horizon}")

l, r = st.columns(2)
with l:
    bar_chart(get_monthly_revenue_chart(c.gym_id), "month", "amount", "Monthly revenue · last 6 months", money=True, color=LIME)
with r:
    donut_chart(get_membership_distribution(c.gym_id), "plan", "count", "Active members by plan")

l, r = st.columns(2)
with l:
    bar_chart(get_peak_hours(c.gym_id, days=max(days, 30)), "hour", "count", "Peak hours (check-ins by hour)")
with r:
    bar_chart(get_expiry_outlook(c.gym_id), "week", "count", "Upcoming expiries · next 4 weeks", color=AMBER)

line_chart(get_member_growth_chart(c.gym_id), "date", "total", "Member growth · last 6 months", color="#8B5CF6", height=260)

if period_pay:
    with st.expander(f"Payments in the last {horizon}"):
        df = pd.DataFrame([{
            "Date": p.get("payment_date"), "Receipt": p.get("receipt_no"), "Member": p.get("member_name"),
            "Amount": float(p.get("amount") or 0), "Method": p.get("payment_method"),
        } for p in period_pay])
        st.dataframe(df, hide_index=True, width="stretch", column_config={"Amount": st.column_config.NumberColumn(format="₹%d")})
        st.download_button("Export CSV", df.to_csv(index=False).encode(), file_name=f"revenue_{days}d.csv", mime="text/csv", icon=":material/download:")
