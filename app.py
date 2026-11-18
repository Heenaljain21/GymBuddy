"""GYM BUDDY - Gym Management SaaS.

Tagline: Your Gym. Your Goals. One Smart Buddy.

Entry point: page config, theme, authentication gate and role-based navigation.
Each screen lives in views/ and is registered with st.navigation, so the sidebar
only ever shows the pages the signed-in role may open.
"""

from __future__ import annotations
import os
import sys

import streamlit as st

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

st.set_page_config(
    page_title="GYM BUDDY · Gym Management",
    page_icon=os.path.join(ROOT, "assets", "logo_sm.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.security import init_session_state, is_demo_mode
from services.auth_service import sign_in, sign_out, is_authenticated
from components.ui import load_css, html_block, esc, asset_data_uri, show_flashes, initials

init_session_state()
html_block(f"<style>{load_css()}</style>")

DEMO_ACCOUNTS = [
    ("Owner", "owner@fitzone.in", "owner123", ":material/insights:"),
    ("Desk", "reception@fitzone.in", "reception123", ":material/badge:"),
    ("Trainer", "vikram@fitzone.in", "trainer123", ":material/fitness_center:"),
    ("Member", "amit@gmail.com", "member123", ":material/person:"),
    ("Admin", "admin@gymbuddy.io", "admin123", ":material/admin_panel_settings:"),
]


def login_page() -> None:
    demo = is_demo_mode()
    left, _, right = st.columns([1.15, 0.1, 1])

    with left:
        html_block(
            f"""
            <div style="padding-top: 3vh">
              <div class="gb-login-brand">
                <img src="{asset_data_uri('logo_sm.png')}" alt="GYM BUDDY logo">
                <div><div class="gb-brand-name">GYM BUDDY</div>
                <div class="gb-eyebrow" style="margin-top:.3rem">Your gym. Your goals. One smart buddy.</div></div>
              </div>
              <h1 class="gb-login-title">Run your whole gym<br>from <span>one screen.</span></h1>
              <div class="gb-feature"><div class="gb-feature-icon">📲</div><div><b>QR check-ins in seconds</b>Members show a pass, the desk scans it, duplicates are blocked automatically.</div></div>
              <div class="gb-feature"><div class="gb-feature-icon">💳</div><div><b>Fees, receipts &amp; renewals</b>Record UPI / cash payments, issue PDF receipts and chase renewals on WhatsApp.</div></div>
              <div class="gb-feature"><div class="gb-feature-icon">🏋️</div><div><b>Coaching built in</b>Trainers assign weekly workouts and 4-meal diet plans members follow on their phone.</div></div>
              <div class="gb-feature"><div class="gb-feature-icon">📈</div><div><b>Know your numbers</b>Revenue, footfall, peak hours and members at risk of dropping out.</div></div>
            </div>
            """
        )

    with right:
        st.write("")
        with st.container(border=True):
            st.subheader("Sign in")
            st.caption("Staff and members use the same login.")
            with st.form("login_form", border=False):
                email = st.text_input("Email", placeholder="you@yourgym.in", autocomplete="email")
                password = st.text_input("Password", type="password", placeholder="••••••••", autocomplete="current-password")
                submitted = st.form_submit_button("Sign in", type="primary", width="stretch", icon=":material/login:")
            if submitted:
                with st.spinner("Signing you in…"):
                    ok, err = sign_in(email, password)
                if ok:
                    st.rerun()
                st.error(err or "Invalid email or password.", icon=":material/error:")

            with st.expander("Forgot password?"):
                st.write("Ask your gym owner to reset it, or email **support@gymbuddy.io**.")

        if demo:
            with st.container(border=True):
                st.markdown("**Try a demo account** · one click, no setup")
                cols = st.columns(3)
                for i, (label, demo_email, demo_pwd, icon) in enumerate(DEMO_ACCOUNTS):
                    if cols[i % 3].button(label, icon=icon, width="stretch", key=f"demo_{label}"):
                        ok, err = sign_in(demo_email, demo_pwd)
                        if ok:
                            st.rerun()
                        st.error(err)
                st.caption("Demo data lives only in this browser tab and resets when you close it.")


def render_user_card() -> None:
    profile = st.session_state.get("profile") or {}
    user = st.session_state.get("user") or {}
    name = profile.get("full_name") or (user.get("email") or "User").split("@")[0].title()
    role = (st.session_state.get("user_role") or "").title()
    with st.sidebar:
        html_block(
            f"""
            <div class="gb-user">
              <div class="gb-avatar" style="width:38px;height:38px;border-radius:10px">{initials(name)}</div>
              <div style="min-width:0">
                <div class="gb-user-name">{esc(name)}</div>
                <div class="gb-user-sub">{esc(role)} · {esc(st.session_state.get('gym_name'))}</div>
              </div>
            </div>
            """
        )
        st.write("")
        if st.button("Sign out", icon=":material/logout:", width="stretch", key="logout"):
            sign_out()
            st.rerun()
        if is_demo_mode():
            html_block('<div class="gb-demo-note">Demo mode · changes are kept only for this browser session.</div>')


def build_navigation():
    role = (st.session_state.get("user_role") or "member").lower()
    is_member = role == "member"

    def page(path: str, title: str, icon: str, url: str, default: bool = False):
        return st.Page(os.path.join(ROOT, "views", path), title=title, icon=icon, url_path=url, default=default)

    home = page("home.py", "My dashboard" if is_member else "Dashboard", ":material/space_dashboard:", "home", default=True)
    members = page("members.py", "Members", ":material/groups:", "members")
    register = page("register.py", "New member", ":material/person_add:", "register")
    attendance = page("attendance.py", "My QR pass" if is_member else "Check-in desk",
                      ":material/qr_code_2:" if is_member else ":material/qr_code_scanner:", "attendance")
    fees = page("fees.py", "Fees & receipts", ":material/payments:", "fees")
    renewals = page("renewals.py", "Renewals", ":material/autorenew:", "renewals")
    roster = page("my_members.py", "My athletes" if role == "trainer" else "Coaching roster", ":material/sports:", "roster")
    workout = page("workout.py", "My workouts" if is_member else "Workout plans", ":material/fitness_center:", "workouts")
    diet = page("diet.py", "My diet" if is_member else "Diet plans", ":material/restaurant:", "diet")
    reports = page("reports.py", "Reports", ":material/monitoring:", "reports")
    inactive = page("inactive.py", "Win-back", ":material/person_alert:", "inactive")
    admin = page("admin.py", "Platform console", ":material/admin_panel_settings:", "admin")

    if role == "admin":
        return {
            "Platform": [home, admin],
            "Front desk": [attendance, register, fees, renewals],
            "Members": [members, inactive, roster],
            "Coaching": [workout, diet],
            "Insights": [reports],
        }
    if role == "owner":
        return {
            "Overview": [home, reports],
            "Front desk": [attendance, register, fees, renewals],
            "Members": [members, inactive, roster],
            "Coaching": [workout, diet],
        }
    if role == "receptionist":
        return {
            "Overview": [home],
            "Front desk": [attendance, register, fees, renewals],
            "Members": [members, inactive],
        }
    if role == "trainer":
        return {"Overview": [home], "Coaching": [roster, workout, diet]}
    return [home, attendance, workout, diet]


if not is_authenticated():
    nav = st.navigation([st.Page(login_page, title="Sign in", icon=":material/login:", url_path="login")], position="hidden")
else:
    st.logo(os.path.join(ROOT, "assets", "logo_sm.png"), size="large")
    nav = st.navigation(build_navigation())
    render_user_card()

show_flashes()
nav.run()
