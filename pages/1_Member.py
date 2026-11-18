"""SCREEN 2 – ONLINE JOINING (Member Registration)

Allows staff (receptionist, owner, admin) to enroll new gym members,
select membership plans, compute dates, record initial payment,
and generate instant QR passes.
"""

from __future__ import annotations
import os
import sys
from datetime import date, timedelta
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import init_session_state
from utils.permissions import require_role
from utils.helpers import format_currency
from utils.date_utils import get_ist_today, format_date_display
from utils.validators import validate_member_form
from services.gym_service import get_membership_plans
from services.member_service import register_member
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.qr_components import render_member_qr
from components.notifications import show_success, show_error


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

render_navbar("Member Registration", "Enroll New Gym Member & Issue QR Pass")

# Fetch active membership plans
plans = get_membership_plans(gym_id, active_only=True)
if not plans:
    st.warning("⚠️ No active membership plans configured for this gym. Please configure plans first.")

# Registration State
if "registered_member" not in st.session_state:
    st.session_state.registered_member = None

if st.session_state.registered_member:
    m = st.session_state.registered_member
    show_success(f"Member '{m.get('full_name')}' enrolled successfully!", f"Unique Member ID: {m.get('member_code')}")
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.2])
    with col1:
        render_member_qr(
            member_code=m.get("member_code", ""),
            member_name=m.get("full_name", ""),
            gym_name=gym_name,
        )
    with col2:
        st.markdown(
            f"""
            <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 1.5rem;">
                <h3 style="color: #F8FAFC; margin-top: 0;">Member Profile Summary</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 0.92rem; color: #94A3B8;">
                    <tr style="border-bottom: 1px solid rgba(148,163,184,0.1);"><td style="padding: 8px 0;"><b>Name</b></td><td style="color: #F8FAFC; text-align: right;">{m.get('full_name')}</td></tr>
                    <tr style="border-bottom: 1px solid rgba(148,163,184,0.1);"><td style="padding: 8px 0;"><b>Member ID</b></td><td style="color: #06D6C9; text-align: right; font-weight: 700;">{m.get('member_code')}</td></tr>
                    <tr style="border-bottom: 1px solid rgba(148,163,184,0.1);"><td style="padding: 8px 0;"><b>Phone</b></td><td style="color: #F8FAFC; text-align: right;">{m.get('phone')}</td></tr>
                    <tr style="border-bottom: 1px solid rgba(148,163,184,0.1);"><td style="padding: 8px 0;"><b>Email</b></td><td style="color: #F8FAFC; text-align: right;">{m.get('email') or 'N/A'}</td></tr>
                    <tr style="border-bottom: 1px solid rgba(148,163,184,0.1);"><td style="padding: 8px 0;"><b>Gender / Age</b></td><td style="color: #F8FAFC; text-align: right;">{m.get('gender')} ({m.get('age')} yrs)</td></tr>
                    <tr style="border-bottom: 1px solid rgba(148,163,184,0.1);"><td style="padding: 8px 0;"><b>Emergency Contact</b></td><td style="color: #F8FAFC; text-align: right;">{m.get('emergency_contact') or 'N/A'}</td></tr>
                    <tr><td style="padding: 8px 0;"><b>Address</b></td><td style="color: #F8FAFC; text-align: right;">{m.get('address') or 'N/A'}</td></tr>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.button("➕ Register Another Member", use_container_width=True):
            st.session_state.registered_member = None
            st.rerun()

else:
    # Available Membership Plan Showcase
    st.markdown("#### 1. Select Membership Plan")
    plan_cols = st.columns(len(plans)) if plans else [st]
    selected_plan_idx = 0

    plan_names = [p["name"] for p in plans]
    selected_plan_name = st.radio(
        "Choose Plan",
        options=plan_names,
        horizontal=True,
        label_visibility="collapsed",
    )
    selected_plan = next((p for p in plans if p["name"] == selected_plan_name), plans[0] if plans else {})

    # Plan details banner
    p_price = float(selected_plan.get("price", 0.0))
    p_days = int(selected_plan.get("duration_days", 30))
    calc_start = get_ist_today()
    calc_end = calc_start + timedelta(days=p_days)

    st.markdown(
        f"""
        <div style="background: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.35); border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-weight: 700; color: #A78BFA; font-size: 1.05rem;">{selected_plan.get('name')}</span>
                <span style="font-size: 0.82rem; color: #94A3B8; margin-left: 0.75rem;">Duration: {p_days} Days ({selected_plan.get('description', '')})</span>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.25rem; font-weight: 800; color: #A3FF5C;">{format_currency(p_price)}</div>
                <div style="font-size: 0.76rem; color: #06D6C9;">Valid: {format_date_display(calc_start)} → {format_date_display(calc_end)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 2. Member & Payment Information")

    with st.form("member_registration_form"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            full_name = st.text_input("Full Name *", placeholder="e.g. Vikram Malhotra")
            phone = st.text_input("Mobile Phone (10-digits) *", placeholder="e.g. 9876543210")
            email = st.text_input("Email Address", placeholder="e.g. vikram@gmail.com")
            age = st.number_input("Age", min_value=12, max_value=90, value=25)
        with col_p2:
            gender = st.selectbox("Gender", options=["Male", "Female", "Other"])
            address = st.text_area("Address / Locality", placeholder="Flat/House, Street, City")
            emergency_contact = st.text_input("Emergency Contact Number", placeholder="e.g. 9876500000")

        st.markdown("<hr style='border: 0; border-top: 1px solid rgba(148,163,184,0.15); margin: 1.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("#### 3. Initial Fee Collection")

        col_pay1, col_pay2, col_pay3 = st.columns(3)
        with col_pay1:
            amount_input = st.number_input("Amount Collected (₹)", value=float(p_price), min_value=0.0, step=100.0)
        with col_pay2:
            pay_method = st.selectbox("Payment Method", options=["UPI", "Cash", "Bank Transfer"])
        with col_pay3:
            txn_ref = st.text_input("Transaction Reference / UTR", placeholder="e.g. UPI/2026/8912")

        submit = st.form_submit_button("⚡ Complete Registration & Issue QR Pass", use_container_width=True)

        if submit:
            payload = {
                "full_name": full_name,
                "phone": phone,
                "email": email,
                "age": age,
                "gender": gender,
                "address": address,
                "emergency_contact": emergency_contact,
                "plan_id": selected_plan.get("id"),
                "duration_days": p_days,
                "amount_paid": amount_input,
                "payment_method": pay_method,
                "transaction_ref": txn_ref,
                "start_date": calc_start,
            }

            is_valid, errors = validate_member_form(payload)
            if not is_valid:
                for err in errors:
                    st.error(f"• {err}")
            else:
                with st.spinner("Registering member in database..."):
                    ok, err_msg, new_member = register_member(gym_id, payload)
                    if ok and new_member:
                        st.session_state.registered_member = new_member
                        st.rerun()
                    else:
                        st.error(err_msg or "Failed to register member.")
