"""SCREEN 8 – MY MEMBERS (Trainer Roster & Athlete Tracking)

Displays members assigned to the logged-in trainer, last visit dates,
workout and diet linkage, and coach-athlete WhatsApp communications.
Owners can allocate members to trainers.
"""

from __future__ import annotations
import os
import sys
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import init_session_state, get_supabase_client
from utils.permissions import require_role
from utils.helpers import generate_whatsapp_link
from utils.date_utils import format_date_display, days_since
from services.member_service import get_members
from services.attendance_service import get_member_attendance
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.dashboard_cards import render_stat_cards_row
from components.notifications import show_success, show_info


def load_css() -> None:
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


init_session_state()
load_css()
require_role(["trainer", "owner", "admin"])
render_sidebar()

gym_id = st.session_state.get("gym_id", "00000000-0000-0000-0000-000000000001")
gym_name = st.session_state.get("gym_name", "FitZone Premium Gym")
user_role = (st.session_state.get("user_role") or "trainer").lower()
profile = st.session_state.get("profile") or {}
user = st.session_state.get("user") or {}
trainer_id = profile.get("id") or user.get("id", "33333333-3333-3333-3333-333333333333")

render_navbar("My Athletes & Members", f"Coaching Roster • {gym_name}")

client = get_supabase_client()

# Fetch trainer assignments
assignments_res = client.table("trainer_assignments").select("*").eq("gym_id", gym_id).execute()
assignments = assignments_res.data or []
assigned_member_ids = {a["member_id"] for a in assignments if user_role == "owner" or a.get("trainer_id") == trainer_id}

all_m = get_members(gym_id)
my_members = [m for m in all_m if m["id"] in assigned_member_ids] if user_role == "trainer" else all_m

# Stat cards
active_count = sum(1 for m in my_members if m.get("membership_status") == "active")
cards = [
    {"title": "Total Assigned" if user_role == "trainer" else "Total Members", "value": len(my_members), "icon": "👥", "color": "purple"},
    {"title": "Active Members", "value": active_count, "icon": "⚡", "color": "lime"},
    {"title": "Facility Name", "value": gym_name.split()[0], "icon": "🏢", "color": "cyan"},
]
render_stat_cards_row(cards)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

# Search & Filters
col_s1, col_s2 = st.columns([2, 1])
with col_s1:
    search_query = st.text_input("🔍 Search athletes by name or phone", placeholder="e.g. Amit")
with col_s2:
    status_filter = st.selectbox("Status Filter", options=["All", "Active", "Expired", "Inactive"])

filtered_members = my_members
if search_query:
    q = search_query.strip().lower()
    filtered_members = [m for m in filtered_members if q in m.get("full_name", "").lower() or q in m.get("phone", "")]
if status_filter != "All":
    filtered_members = [m for m in filtered_members if m.get("membership_status", "").lower() == status_filter.lower()]

if not filtered_members:
    st.info("No athletes found matching the filters.")
else:
    for m in filtered_members:
        mid = m["id"]
        mname = m.get("full_name", "Member")
        mcode = m.get("member_code", "-")
        mphone = m.get("phone", "")
        plan_name = m.get("plan_name", "Standard")
        m_status = m.get("membership_status", "active")
        exp_date = m.get("expiry_date")

        # Get attendance to check last visit
        att = get_member_attendance(gym_id, mid, limit=1)
        last_visit = att[0].get("check_in_date") if att else None
        days_past = days_since(last_visit) if last_visit else 999

        badge_color = "#A3FF5C" if m_status == "active" else "#EF4444"

        st.markdown(
            f"""
            <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 14px; padding: 1.25rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 1.2rem; font-weight: 800; color: #F8FAFC;">{mname}</span>
                            <span style="background: rgba(139, 92, 246, 0.2); color: #A78BFA; border: 1px solid #8B5CF6; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">{mcode}</span>
                            <span style="background: rgba(255,255,255,0.08); color: {badge_color}; border: 1px solid {badge_color}; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 6px;">{m_status.upper()}</span>
                        </div>
                        <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">
                            Plan: <b>{plan_name}</b> • Expires: <b>{format_date_display(exp_date)}</b> • Last Gym Visit: <b style="color: {'#A3FF5C' if days_past <= 2 else '#F59E0B'}">{format_date_display(last_visit) if last_visit else 'Never'}</b> ({days_past} days ago)
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_a1, col_a2, col_a3, col_a4 = st.columns([1, 1, 1, 1])
        with col_a1:
            wa_text = f"Hey {mname}! Coach {profile.get('full_name', 'Vikram')} here from {gym_name}. How is your training and nutrition going this week? 💪"
            wa_link = generate_whatsapp_link(mphone, wa_text)
            st.markdown(
                f"""
                <a href="{wa_link}" target="_blank" style="text-decoration: none;">
                    <div style="background: #25D366; color: white; text-align: center; padding: 6px; border-radius: 8px; font-weight: 700; font-size: 0.82rem;">
                        💬 WhatsApp Athlete
                    </div>
                </a>
                """,
                unsafe_allow_html=True,
            )
        with col_a2:
            if st.button("🏋️ Workout Routine", key=f"btn_wp_{mid}", use_container_width=True):
                st.switch_page("pages/3_Workout.py")
        with col_a3:
            if st.button("🥗 Diet Plan", key=f"btn_dp_{mid}", use_container_width=True):
                st.switch_page("pages/7_Diet_Plan.py")
        with col_a4:
            with st.expander("📋 Details"):
                st.caption(f"Phone: {mphone}")
                st.caption(f"Emergency Contact: {m.get('emergency_contact', '-')}")
                st.caption(f"Address: {m.get('address', '-')}")
                history = get_member_attendance(gym_id, mid, limit=5)
                if history:
                    st.caption("Recent Check-ins:")
                    for h in history:
                        st.caption(f"• {format_date_display(h.get('check_in_date'))} at {h.get('check_in_time')}")
                else:
                    st.caption("No attendance recorded yet.")
