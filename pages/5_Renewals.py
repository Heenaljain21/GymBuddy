"""SCREEN 7 – RENEWAL MANAGEMENT

Identifies memberships approaching expiry (7, 15, 30 days, expired),
provides 1-click WhatsApp renewal alerts, and executes plan renewals with automated payment logging.
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
from utils.helpers import format_currency, generate_whatsapp_link
from utils.date_utils import get_ist_today, format_date_display, days_remaining
from services.renewal_service import get_expiring_memberships, renew_membership, get_renewal_summary
from services.gym_service import get_membership_plans
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.dashboard_cards import render_stat_cards_row
from components.notifications import show_success, show_error, show_warning


def load_css() -> None:
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


init_session_state()
load_css()
require_role(["owner", "receptionist", "admin"])
render_sidebar()

gym_id = st.session_state.get("gym_id", "00000000-0000-0000-0000-000000000001")
gym_name = st.session_state.get("gym_name", "FitZone Premium Gym")

render_navbar("Renewal Management", "Expiring Memberships & Retention Tracking")

# Summary counts
summary = get_renewal_summary(gym_id)
cards = [
    {"title": "Expiring ≤ 7 Days", "value": summary["within_7_days"], "icon": "⚠️", "color": "amber"},
    {"title": "Expiring ≤ 15 Days", "value": summary["within_15_days"], "icon": "⏳", "color": "pink"},
    {"title": "Expiring ≤ 30 Days", "value": summary["within_30_days"], "icon": "📅", "color": "blue"},
    {"title": "Already Expired", "value": summary["expired"], "icon": "❌", "color": "amber"},
]
render_stat_cards_row(cards)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

categories = get_expiring_memberships(gym_id)
plans = get_membership_plans(gym_id, active_only=True)

tab_soon, tab_month, tab_expired, tab_all = st.tabs([
    f"⚠️ Expiring Soon ({len(categories['within_15_days'])})",
    f"📅 Expiring in 30 Days ({len(categories['within_30_days'])})",
    f"❌ Already Expired ({len(categories['expired'])})",
    f"👥 All Records ({len(categories['all'])})",
])


def render_renewal_list(items: list, tab_key: str):
    if not items:
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.4); border-radius: 12px; padding: 2rem; text-align: center; color: #64748B;">
                <div>✨ No memberships found in this category.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for idx, item in enumerate(items):
        mid = item["member_id"]
        mname = item["member_name"]
        mphone = item["phone"]
        rem = item["days_remaining"]
        pname = item["plan_name"]
        exp_date = item["expiry_date"]

        status_color = "#EF4444" if rem < 0 else ("#F59E0B" if rem <= 7 else "#3B82F6")
        status_text = f"EXPIRED ({abs(rem)} days ago)" if rem < 0 else (f"Expiring in {rem} days" if rem > 0 else "Expiring TODAY")

        # Prefilled WhatsApp message
        wa_text = f"Hello {mname}! Your gym membership at {gym_name} for '{pname}' is {status_text}. Renew now to continue your fitness journey without interruption! 💪"
        wa_link = generate_whatsapp_link(mphone, wa_text)

        st.markdown(
            f"""
            <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(148, 163, 184, 0.15); border-left: 4px solid {status_color}; border-radius: 14px; padding: 1.25rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 1.15rem; font-weight: 800; color: #F8FAFC;">{mname}</div>
                        <div style="font-size: 0.82rem; color: #06D6C9; margin-top: 2px;">ID: <b>{item.get('member_code')}</b> • 📞 {mphone}</div>
                        <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">Current Plan: <b>{pname}</b> • Expiry: <b>{format_date_display(exp_date)}</b></div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: rgba(255, 255, 255, 0.08); color: {status_color}; border: 1px solid {status_color}; padding: 4px 12px; border-radius: 20px; font-size: 0.78rem; font-weight: 700;">
                            {status_text}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            st.markdown(
                f"""
                <a href="{wa_link}" target="_blank" style="text-decoration: none;">
                    <div style="background: #25D366; color: white; text-align: center; padding: 7px; border-radius: 8px; font-weight: 700; font-size: 0.85rem;">
                        💬 Send WhatsApp Renewal Reminder
                    </div>
                </a>
                """,
                unsafe_allow_html=True,
            )
        with col_act2:
            with st.expander(f"🔄 Renew Membership for {mname}"):
                with st.form(f"renew_form_{tab_key}_{idx}"):
                    plan_options = {f"{p['name']} ({format_currency(p['price'])}, {p['duration_days']} days)": p for p in plans}
                    sel_p_label = st.selectbox("Select New Plan", options=list(plan_options.keys()))
                    sel_p = plan_options[sel_p_label]

                    r_amount = st.number_input("Renewal Fee (₹)", value=float(sel_p["price"]), min_value=0.0)
                    r_method = st.selectbox("Payment Method", options=["UPI", "Cash", "Bank Transfer"])
                    r_ref = st.text_input("Transaction Ref", placeholder="e.g. UPI/2026/1122")

                    if st.form_submit_button("⚡ Confirm Renewal & Collect Payment"):
                        with st.spinner("Processing renewal..."):
                            ok, err = renew_membership(
                                gym_id=gym_id,
                                member_id=mid,
                                new_plan_id=sel_p["id"],
                                amount_paid=r_amount,
                                payment_method=r_method,
                                transaction_ref=r_ref,
                            )
                            if ok:
                                show_success(f"Membership for {mname} renewed successfully under {sel_p['name']}!")
                                st.rerun()
                            else:
                                show_error(err or "Failed to renew.")


with tab_soon:
    render_renewal_list(categories["within_15_days"], "soon")

with tab_month:
    render_renewal_list(categories["within_30_days"], "month")

with tab_expired:
    render_renewal_list(categories["expired"], "expired")

with tab_all:
    render_renewal_list(categories["all"], "all")
