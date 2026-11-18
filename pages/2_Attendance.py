"""SCREEN 3 & SCREEN 5 – QR ATTENDANCE & RECEPTION ATTENDANCE REGISTER

Provides QR-based check-in, duplicate prevention, and real-time attendance dashboard.
- For Members: Personal QR Code pass & check-in history.
- For Staff: Scanner, today's check-ins, manual check-in, date filters, and analytics.
"""

from __future__ import annotations
import os
import sys
from datetime import date, timedelta
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import init_session_state
from utils.permissions import require_auth
from utils.date_utils import get_ist_today, format_date_display, format_time_display
from services.attendance_service import (
    check_in,
    get_today_attendance,
    get_member_attendance,
    get_monthly_attendance_count,
    is_already_checked_in,
)
from services.member_service import get_members, get_member_by_qr, search_members
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.qr_components import render_member_qr, render_qr_scanner
from components.dashboard_cards import render_stat_cards_row
from components.notifications import show_success, show_error, show_warning, show_info


def load_css() -> None:
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


init_session_state()
load_css()
require_auth()
render_sidebar()

gym_id = st.session_state.get("gym_id", "00000000-0000-0000-0000-000000000001")
gym_name = st.session_state.get("gym_name", "FitZone Premium Gym")
user_role = (st.session_state.get("user_role") or "member").lower()

render_navbar("Attendance & QR Access", f"Check-in Operations • {gym_name}")

# ==========================================
# 1. MEMBER ROLE VIEW (SCREEN 3)
# ==========================================
if user_role == "member":
    user = st.session_state.get("user") or {}
    email = user.get("email", "")
    
    # Locate member record
    all_members = get_members(gym_id)
    current_member = next((m for m in all_members if m.get("email") == email or m.get("phone") == user.get("phone")), None)
    if not current_member and all_members:
        current_member = all_members[0]  # Fallback for demo

    if not current_member:
        st.error("No member profile linked to this account.")
        st.stop()

    mid = current_member["id"]
    mcode = current_member.get("member_code", "GMB-2026-001")
    mname = current_member.get("full_name", "Member")

    # Monthly count stat card
    monthly_count = get_monthly_attendance_count(gym_id, mid)
    checked_today = is_already_checked_in(gym_id, mid)

    col1, col2 = st.columns([1, 1.2])

    with col1:
        render_member_qr(member_code=mcode, member_name=mname, gym_name=gym_name)

    with col2:
        st.markdown(
            f"""
            <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 1.5rem; margin-bottom: 1rem;">
                <div style="font-size: 0.82rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em;">Today's Check-in Status</div>
                <div style="font-size: 1.4rem; font-weight: 800; color: {'#A3FF5C' if checked_today else '#EC4899'}; margin-top: 0.25rem;">
                    {'✅ Checked In Today' if checked_today else '⭕ Not Checked In Yet'}
                </div>
                <div style="font-size: 0.85rem; color: #64748B; margin-top: 0.2rem;">
                    {'You have completed today\'s session!' if checked_today else 'Show your QR code at the front desk when you arrive.'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 1.5rem;">
                <div style="font-size: 0.82rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em;">Monthly Consistency</div>
                <div style="font-family: 'Outfit', sans-serif; font-size: 2.5rem; font-weight: 800; color: #06D6C9; margin-top: 0.2rem;">
                    {monthly_count} <span style="font-size: 1rem; color: #94A3B8; font-weight: 500;">workouts this month</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 📋 My Recent Check-in History")
    history = get_member_attendance(gym_id, mid, limit=15)
    if history:
        records = []
        for h in history:
            records.append({
                "Date": format_date_display(h.get("check_in_date")),
                "Time": format_time_display(h.get("check_in_time")),
                "Method": h.get("method", "QR Code").replace("_", " ").title(),
            })
        st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True)
    else:
        st.info("No check-in entries recorded yet.")


# ==========================================
# 2. STAFF ROLE VIEW (SCREEN 5)
# ==========================================
else:
    today_date = get_ist_today()

    # Date filter
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        date_filter = st.radio(
            "Select Date Filter",
            options=["Today", "Yesterday", "Custom Date"],
            horizontal=True,
            label_visibility="collapsed",
        )
    with col_f2:
        if date_filter == "Custom Date":
            target_date = st.date_input("Target Date", value=today_date, max_value=today_date)
        elif date_filter == "Yesterday":
            target_date = today_date - timedelta(days=1)
        else:
            target_date = today_date

    # Fetch attendance
    records = get_today_attendance(gym_id, filter_date=target_date)

    # Stat cards row
    cards = [
        {"title": f"Check-ins ({format_date_display(target_date)})", "value": len(records), "icon": "📋", "color": "purple"},
        {"title": "Active Facility", "value": gym_name.split()[0], "icon": "🏢", "color": "cyan"},
        {"title": "Check-in Mode", "value": "QR + Manual", "icon": "⚡", "color": "lime"},
    ]
    render_stat_cards_row(cards)
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    col_scan, col_table = st.columns([1, 1.4])

    with col_scan:
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(139, 92, 246, 0.35); border-radius: 16px; padding: 1.25rem; margin-bottom: 1.5rem;">
            """,
            unsafe_allow_html=True,
        )
        scanned_input = render_qr_scanner(key_prefix="reception")
        st.markdown("</div>", unsafe_allow_html=True)

        if scanned_input:
            member = get_member_by_qr(gym_id, scanned_input)
            if not member:
                show_error(f"No member found matching '{scanned_input}'.", "Check Member ID or register them first.")
            else:
                mid = member["id"]
                mname = member.get("full_name", "Member")
                mcode = member.get("member_code", "-")

                st.markdown(
                    f"""
                    <div style="background: rgba(163, 255, 92, 0.08); border: 1px solid rgba(163, 255, 92, 0.3); border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                        <div style="font-size: 0.8rem; color: #A3FF5C; font-weight: 700;">IDENTIFIED MEMBER</div>
                        <div style="font-size: 1.2rem; font-weight: 800; color: #F8FAFC; margin-top: 2px;">{mname}</div>
                        <div style="font-size: 0.85rem; color: #94A3B8;">Code: <b>{mcode}</b> • Phone: <b>{member.get('phone')}</b></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if is_already_checked_in(gym_id, mid, target_date):
                    show_warning(f"Member '{mname}' is ALREADY checked in for this date! ⚠️")
                else:
                    if st.button(f"✅ Confirm Check-in for {mname}", use_container_width=True):
                        ok, msg, _ = check_in(gym_id, mid, method="qr_code")
                        if ok:
                            show_success(f"Check-in confirmed for {mname}!", msg)
                            st.rerun()
                        else:
                            show_warning(msg)

        # Quick manual check-in dropdown
        with st.expander("⚡ Quick Member Lookup & Manual Check-in"):
            all_m = get_members(gym_id)
            if all_m:
                member_options = {f"{m['full_name']} ({m.get('member_code', '-')})": m for m in all_m}
                selected_label = st.selectbox("Select Member", options=list(member_options.keys()))
                sel_m = member_options[selected_label]
                if st.button(f"Record Manual Attendance for {sel_m['full_name']}", use_container_width=True):
                    ok, msg, _ = check_in(gym_id, sel_m["id"], method="manual")
                    if ok:
                        show_success(msg)
                        st.rerun()
                    else:
                        show_warning(msg)

    with col_table:
        st.markdown(f"#### Check-in Register ({format_date_display(target_date)})")
        
        # Search filter
        search_q = st.text_input("🔍 Search check-ins by name or phone", placeholder="e.g. Amit")

        filtered = records
        if search_q:
            q = search_q.strip().lower()
            filtered = [r for r in records if q in r.get("member_name", "").lower() or q in r.get("member_phone", "")]

        if filtered:
            display_data = []
            for r in filtered:
                display_data.append({
                    "Time": format_time_display(r.get("check_in_time")),
                    "Member Name": r.get("member_name"),
                    "Member Code": r.get("member_code"),
                    "Phone": r.get("member_phone"),
                    "Method": r.get("method", "QR").replace("_", " ").title(),
                })
            st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)
        else:
            st.markdown(
                """
                <div style="background: rgba(23, 29, 48, 0.5); border: 1px dashed rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 2.5rem; text-align: center; color: #94A3B8;">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">📋</div>
                    <div style="font-size: 0.95rem; font-weight: 600;">No check-ins recorded for this date</div>
                    <div style="font-size: 0.8rem; color: #64748B;">Scan member QR codes or record manual entries above</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
