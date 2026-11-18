"""SCREEN 10 – OWNER DASHBOARD & DAILY REPORT

Flagship executive analytics console.
Visualizes revenue collections, attendance throughput, membership distributions,
and commercial growth curves using dark-themed Plotly charts.
"""

from __future__ import annotations
import os
import sys
from datetime import date, timedelta
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import init_session_state
from utils.permissions import require_role
from utils.helpers import format_currency
from utils.date_utils import get_ist_today, get_ist_now, format_date_display
from services.report_service import (
    get_dashboard_stats,
    get_daily_revenue_chart,
    get_monthly_revenue_chart,
    get_attendance_trends,
    get_membership_distribution,
    get_member_growth_chart,
)
from services.payment_service import get_payments
from services.member_service import get_members
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.dashboard_cards import render_stat_cards_row
from components.charts import (
    render_revenue_chart,
    render_attendance_chart,
    render_membership_distribution,
    render_member_growth_chart,
)


def load_css() -> None:
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


init_session_state()
load_css()
require_role(["owner", "admin"])
render_sidebar()

gym_id = st.session_state.get("gym_id", "00000000-0000-0000-0000-000000000001")
gym_name = st.session_state.get("gym_name", "FitZone Premium Gym")

render_navbar("Executive Analytics & Daily Report", f"Commercial Performance • {gym_name}")

# Date range selection
col_f1, col_f2 = st.columns([3, 1])
with col_f1:
    range_filter = st.radio(
        "Reporting Horizon",
        options=["Last 30 Days", "Last 7 Days", "This Month", "Today"],
        horizontal=True,
    )
with col_f2:
    st.markdown(
        f"""
        <div style="text-align: right; padding-top: 10px;">
            <span style="background: rgba(6, 214, 201, 0.15); color: #06D6C9; border: 1px solid #06D6C9; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 700;">
                LIVE TELEMETRY
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 1. SIX CORE METRIC STAT CARDS
stats = get_dashboard_stats(gym_id)
cards_row_1 = [
    {"title": "Total Members", "value": stats["total_members"], "icon": "👥", "color": "purple", "subtext": "Registered Athletes"},
    {"title": "Active Passes", "value": stats["active_members"], "icon": "⚡", "color": "cyan", "subtext": "Valid memberships"},
    {"title": "Today's Check-ins", "value": stats["today_attendance"], "icon": "📋", "color": "blue", "subtext": "Facility footfall"},
]
cards_row_2 = [
    {"title": "Month Revenue", "value": format_currency(stats["monthly_revenue"]), "icon": "💰", "color": "lime", "subtext": "Current calendar month"},
    {"title": "Today's Collection", "value": format_currency(stats["today_revenue"]), "icon": "💵", "color": "pink", "subtext": "Daily counter cash & UPI"},
    {"title": "Inactive Members", "value": stats["inactive_members"], "icon": "⚠️", "color": "amber", "subtext": "Absent ≥ 7 days"},
]

render_stat_cards_row(cards_row_1)
st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
render_stat_cards_row(cards_row_2)
st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# 2. PLOTLY CHARTS GRID
days_param = 7 if range_filter == "Last 7 Days" else (1 if range_filter == "Today" else 30)

col_c1, col_c2 = st.columns(2)

with col_c1:
    # Daily Revenue Chart
    df_rev = get_daily_revenue_chart(gym_id, days=days_param)
    render_revenue_chart(df_rev, x_col="date", y_col="amount", title=f"Daily Revenue Velocity ({range_filter})")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Monthly Revenue Chart
    df_monthly = get_monthly_revenue_chart(gym_id)
    render_revenue_chart(df_monthly, x_col="month", y_col="amount", title="Monthly Revenue Aggregates (INR)")

with col_c2:
    # Attendance Trends
    df_att = get_attendance_trends(gym_id, days=days_param)
    render_attendance_chart(df_att, x_col="date", y_col="count", title=f"Gym Check-in Throughput ({range_filter})")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # Membership Distribution
    df_dist = get_membership_distribution(gym_id)
    render_membership_distribution(df_dist, labels_col="plan", values_col="count", title="Active Plan Distribution")

st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# Member Growth Area Chart
df_growth = get_member_growth_chart(gym_id)
render_member_growth_chart(df_growth, x_col="date", y_col="total", title="Cumulative Member Growth Trajectory")

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# 3. RECENT ACTIVITY AUDIT FEEDS
col_a1, col_a2 = st.columns(2)

with col_a1:
    st.markdown("#### 🆕 Recent Member Registrations")
    all_members = get_members(gym_id)
    recent_members = all_members[:5] if all_members else []
    if recent_members:
        rec_data = []
        for m in recent_members:
            rec_data.append({
                "Member": m.get("full_name"),
                "ID": m.get("member_code"),
                "Plan": m.get("plan_name", "Standard"),
                "Status": m.get("membership_status", "Active").upper(),
            })
        st.dataframe(pd.DataFrame(rec_data), use_container_width=True, hide_index=True)
    else:
        st.caption("No members registered yet.")

with col_a2:
    st.markdown("#### 💳 Recent Payment Transactions")
    recent_payments = get_payments(gym_id)[:5]
    if recent_payments:
        pay_data = []
        for p in recent_payments:
            pay_data.append({
                "Receipt": p.get("receipt_no"),
                "Member": p.get("member_name"),
                "Amount": format_currency(p.get("amount")),
                "Mode": p.get("payment_method"),
            })
        st.dataframe(pd.DataFrame(pay_data), use_container_width=True, hide_index=True)
    else:
        st.caption("No recent transactions recorded.")
