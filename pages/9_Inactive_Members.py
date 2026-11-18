"""SCREEN 11 – INACTIVE & MISSING MEMBERS RETENTION ENGINE

Commercial retention feature for identifying disengaged gym members,
categorizing absence periods (7-14, 15-30, 30+, never attended),
and orchestrating WhatsApp re-engagement campaigns.
"""

from __future__ import annotations
import os
import sys
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.security import init_session_state
from utils.permissions import require_role
from utils.helpers import generate_whatsapp_link
from utils.date_utils import format_date_display
from services.inactivity_service import get_inactive_members, log_followup
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.dashboard_cards import render_stat_cards_row
from components.notifications import show_success, show_error, show_info


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
profile = st.session_state.get("profile") or {}
user = st.session_state.get("user") or {}
staff_id = profile.get("id") or user.get("id", "22222222-2222-2222-2222-222222222222")

render_navbar("Inactive Member Recovery", f"Member Retention & WhatsApp Campaigns • {gym_name}")

# Inactivity Threshold Control
col_t1, col_t2 = st.columns([3, 1])
with col_t1:
    threshold = st.slider("Select Minimum Inactivity Days Threshold", min_value=7, max_value=60, value=14, step=1)
with col_t2:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.caption("Standard gym industry dropout alert begins at 14 days.")

categories = get_inactive_members(gym_id, threshold_days=threshold)

# Stat cards row
cards = [
    {"title": "7 – 14 Days Absent", "value": len(categories["7_to_14_days"]), "icon": "⚠️", "color": "amber", "subtext": "Early warning stage"},
    {"title": "15 – 30 Days Absent", "value": len(categories["15_to_30_days"]), "icon": "⏳", "color": "pink", "subtext": "High dropout risk"},
    {"title": "30+ Days Absent", "value": len(categories["over_30_days"]), "icon": "🚨", "color": "amber", "subtext": "Critical disengagement"},
    {"title": "Never Attended", "value": len(categories["never_attended"]), "icon": "⭕", "color": "purple", "subtext": "Enrolled but 0 visits"},
]
render_stat_cards_row(cards)
st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

tab_7_14, tab_15_30, tab_30_plus, tab_never = st.tabs([
    f"⚠️ 7 – 14 Days ({len(categories['7_to_14_days'])})",
    f"⏳ 15 – 30 Days ({len(categories['15_to_30_days'])})",
    f"🚨 30+ Days ({len(categories['over_30_days'])})",
    f"⭕ Never Attended ({len(categories['never_attended'])})",
])


def render_inactive_tab(items: list, tab_name: str):
    if not items:
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.4); border-radius: 12px; padding: 2rem; text-align: center; color: #64748B;">
                <div>🎉 Great news! No members currently in this inactive bracket.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    for idx, mem in enumerate(items):
        mid = mem["member_id"]
        mname = mem["member_name"]
        mphone = mem["phone"]
        days_off = mem["days_inactive"]
        last_visit = mem["last_visit"]
        status = mem.get("contact_status", "pending")
        last_note = mem.get("last_note", "")

        status_colors = {
            "pending": "#F59E0B",
            "contacted": "#3B82F6",
            "responded": "#06D6C9",
            "returned": "#A3FF5C",
            "lost": "#EF4444",
        }
        st_color = status_colors.get(status.lower(), "#94A3B8")

        # Dynamic motivational message
        if days_off >= 999:
            wa_text = f"Hello {mname}! We noticed you haven't started your fitness workouts at {gym_name} yet. Our coaching team is ready to give you a personalized orientation this week! Reply to book your slot. 💪"
        else:
            wa_text = f"Hey {mname}! We noticed you haven't visited {gym_name} in {days_off} days. Consistency is key to your fitness goals, and we'd love to see you back on the gym floor! How can we assist you? 🏋️"

        wa_link = generate_whatsapp_link(mphone, wa_text)

        st.markdown(
            f"""
            <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(148, 163, 184, 0.15); border-left: 4px solid {st_color}; border-radius: 14px; padding: 1.25rem; margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-size: 1.2rem; font-weight: 800; color: #F8FAFC;">{mname}</div>
                        <div style="font-size: 0.85rem; color: #06D6C9; margin-top: 2px;">ID: <b>{mem.get('member_code')}</b> • 📞 {mphone}</div>
                        <div style="font-size: 0.85rem; color: #94A3B8; margin-top: 4px;">
                            Last Seen: <b style="color: #F8FAFC;">{format_date_display(last_visit) if last_visit != 'Never' else 'Never'}</b> • Absent for: <b style="color: #EC4899;">{days_off if days_off < 999 else 'Never Attended'} days</b>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: rgba(255,255,255,0.08); color: {st_color}; border: 1px solid {st_color}; padding: 4px 12px; border-radius: 20px; font-size: 0.76rem; font-weight: 700; text-transform: uppercase;">
                            {status}
                        </span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_b1, col_b2 = st.columns([1, 1.2])
        with col_b1:
            st.markdown(
                f"""
                <a href="{wa_link}" target="_blank" style="text-decoration: none;">
                    <div style="background: #25D366; color: white; text-align: center; padding: 8px; border-radius: 8px; font-weight: 700; font-size: 0.85rem;">
                        💬 Launch WhatsApp Re-engagement
                    </div>
                </a>
                """,
                unsafe_allow_html=True,
            )
        with col_b2:
            with st.expander(f"📝 Update Outreach Log for {mname}"):
                with st.form(f"follow_form_{tab_name}_{idx}"):
                    new_status = st.selectbox(
                        "Outreach Status",
                        options=["pending", "contacted", "responded", "returned", "lost"],
                        index=["pending", "contacted", "responded", "returned", "lost"].index(status.lower()) if status.lower() in ["pending", "contacted", "responded", "returned", "lost"] else 0,
                    )
                    note_text = st.text_area("Follow-up Feedback / Note", value=last_note, placeholder="e.g. Member was unwell, will resume training on Monday")
                    if st.form_submit_button("Save Outreach Note"):
                        ok, err = log_followup(
                            gym_id=gym_id,
                            member_id=mid,
                            contacted_by=staff_id,
                            status=new_status,
                            notes=note_text,
                            channel="whatsapp",
                        )
                        if ok:
                            show_success(f"Followup note saved for {mname}!")
                            st.rerun()
                        else:
                            show_error(err or "Failed to log note.")


with tab_7_14:
    render_inactive_tab(categories["7_to_14_days"], "7_14")

with tab_15_30:
    render_inactive_tab(categories["15_to_30_days"], "15_30")

with tab_30_plus:
    render_inactive_tab(categories["over_30_days"], "30_plus")

with tab_never:
    render_inactive_tab(categories["never_attended"], "never")
