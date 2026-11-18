"""GYM BUDDY - Production-Ready Gym Management SaaS.

Tagline: Your Gym. Your Goals. One Smart Buddy.
Main application entry point, login portal, platform admin console, and role router.
"""

from __future__ import annotations
import os
import sys
from typing import Optional
import streamlit as st

# Configure path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Streamlit Page Config - Must be called first
st.set_page_config(
    page_title="GYM BUDDY - Gym Management SaaS",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.security import init_session_state, get_supabase_client
from utils.permissions import require_auth
from services.auth_service import sign_in, sign_out, is_authenticated
from services.gym_service import get_all_gyms, create_gym
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.notifications import show_success, show_error, show_info
from components.dashboard_cards import render_stat_card, render_stat_cards_row


def load_css() -> None:
    """Inject futuristic dark theme CSS."""
    css_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


init_session_state()
load_css()


def render_login_screen() -> None:
    """Render futuristic dark login portal (Screen 1)."""
    st.markdown("<div style='height: 3vh;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        # Futuristic card wrapper
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.9); border: 1px solid rgba(139, 92, 246, 0.35); border-radius: 24px; padding: 2.5rem 2rem; backdrop-filter: blur(16px); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45), 0 0 30px rgba(139, 92, 246, 0.15); text-align: center;">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; border-radius: 18px; background: linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%); font-size: 2rem; margin-bottom: 1rem; box-shadow: 0 6px 20px rgba(139, 92, 246, 0.5);">
                    💪
                </div>
                <h1 style="font-family: 'Outfit', sans-serif; font-size: 2.3rem; font-weight: 900; letter-spacing: -0.02em; background: linear-gradient(135deg, #FFFFFF 0%, #A78BFA 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 0.25rem 0;">
                    GYM BUDDY
                </h1>
                <div style="font-size: 0.85rem; font-weight: 600; color: #06D6C9; letter-spacing: 0.15em; text-transform: uppercase; margin-bottom: 1.5rem;">
                    Your Gym. Your Goals. One Smart Buddy.
                </div>
                <h3 style="font-size: 1.35rem; font-weight: 700; color: #F8FAFC; margin-bottom: 0.2rem;">
                    Welcome Back.
                </h3>
                <p style="font-size: 0.88rem; color: #94A3B8; margin-top: 0; margin-bottom: 1.5rem;">
                    Your fitness management starts here.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Quick Demo Role Fillers for instant testing
        st.markdown(
            """
            <div style="background: rgba(17, 21, 37, 0.6); border: 1px dashed rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
                <div style="font-size: 0.76rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; text-align: center;">
                    ⚡ 1-Click Demo Accounts
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        d_col1, d_col2, d_col3, d_col4, d_col5 = st.columns(5)
        demo_clicked = None
        with d_col1:
            if st.button("👑 Admin", use_container_width=True):
                demo_clicked = ("admin@gymbuddy.io", "admin123")
        with d_col2:
            if st.button("🏢 Owner", use_container_width=True):
                demo_clicked = ("owner@fitzone.in", "owner123")
        with d_col3:
            if st.button("📋 Desk", use_container_width=True):
                demo_clicked = ("reception@fitzone.in", "reception123")
        with d_col4:
            if st.button("🏋️ Trainer", use_container_width=True):
                demo_clicked = ("vikram@fitzone.in", "trainer123")
        with d_col5:
            if st.button("👤 Member", use_container_width=True):
                demo_clicked = ("amit@gmail.com", "member123")

        with st.form("login_form", clear_on_submit=False):
            default_email = demo_clicked[0] if demo_clicked else ""
            default_pwd = demo_clicked[1] if demo_clicked else ""

            email = st.text_input("Work Email Address", value=default_email, placeholder="e.g. owner@fitzone.in")
            password = st.text_input("Password", value=default_pwd, type="password", placeholder="••••••••")
            submit = st.form_submit_button("🚀 Sign In to GYM BUDDY", use_container_width=True)

            if submit or demo_clicked:
                with st.spinner("Authenticating credentials..."):
                    ok, err = sign_in(email, password)
                    if ok:
                        st.success("Authenticated successfully! Redirecting...")
                        st.rerun()
                    else:
                        st.error(err or "Invalid credentials. Please try again.")

        with st.expander("Forgot your password?"):
            st.info("Please contact your gym administrator or platform support at support@gymbuddy.io to reset credentials.")


def render_admin_console() -> None:
    """Render Platform Admin feature for managing multi-gym architecture."""
    render_navbar("Platform Administration Console", "Multi-Tenant Cloud Operations")

    st.markdown(
        """
        <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 1.5rem;">
            <div style="font-size: 0.95rem; font-weight: 700; color: #A78BFA; margin-bottom: 0.2rem;">
                👑 Platform Super-Admin Privileges Active
            </div>
            <div style="font-size: 0.82rem; color: #94A3B8;">
                You have global access across all gym tenants, staff allocations, and commercial subscriptions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3 = st.tabs(["🏢 Gym Facilities", "➕ Provision New Gym", "👥 Global Users"])

    with tab1:
        gyms = get_all_gyms()
        if gyms:
            for g in gyms:
                with st.container():
                    st.markdown(
                        f"""
                        <div style="background: rgba(23, 29, 48, 0.8); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 14px; padding: 1.25rem; margin-bottom: 1rem;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <div style="font-size: 1.25rem; font-weight: 800; color: #F8FAFC;">{g.get('name')}</div>
                                    <div style="font-size: 0.85rem; color: #06D6C9; margin-top: 2px;">📍 {g.get('city')}, {g.get('state')} • {g.get('phone')}</div>
                                    <div style="font-size: 0.8rem; color: #94A3B8; margin-top: 4px;">{g.get('address')}</div>
                                </div>
                                <div>
                                    <span style="background: rgba(163, 255, 92, 0.15); color: #A3FF5C; border: 1px solid #A3FF5C; padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700;">ACTIVE TENANT</span>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No gyms registered yet.")

    with tab2:
        st.subheader("Register New Gym Tenant")
        with st.form("new_gym_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                g_name = st.text_input("Gym Facility Name *", placeholder="e.g. Iron Fitness Hub")
                g_slug = st.text_input("Unique Slug *", placeholder="e.g. iron-fitness-hub")
                g_phone = st.text_input("Primary Contact Phone *", placeholder="e.g. 9876543210")
                g_email = st.text_input("Business Email", placeholder="e.g. contact@ironfitness.in")
            with col_b:
                g_city = st.text_input("City *", placeholder="e.g. Mumbai")
                g_state = st.text_input("State *", placeholder="e.g. Maharashtra")
                g_addr = st.text_area("Full Address", placeholder="Street, Locality, Pincode")
                g_tagline = st.text_input("Tagline", placeholder="e.g. Build Real Strength")

            if st.form_submit_button("🚀 Provision Facility", use_container_width=True):
                if not g_name or not g_slug or not g_phone or not g_city:
                    st.error("Please fill in all required fields.")
                else:
                    payload = {
                        "name": g_name,
                        "slug": g_slug,
                        "phone": g_phone,
                        "email": g_email,
                        "city": g_city,
                        "state": g_state,
                        "address": g_addr,
                        "tagline": g_tagline,
                        "currency": "INR",
                        "is_active": True,
                    }
                    ok, err, new_g = create_gym(payload)
                    if ok:
                        st.success(f"Facility '{g_name}' provisioned successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to create gym: {err}")

    with tab3:
        st.subheader("Global User Directory")
        client = get_supabase_client()
        profiles = client.table("profiles").select("*").execute().data or []
        import pandas as pd
        if profiles:
            df = pd.DataFrame(profiles)[["full_name", "email", "role", "phone"]]
            st.dataframe(df, use_container_width=True, hide_index=True)


def render_authenticated_home() -> None:
    """Render home experience according to logged-in user role."""
    render_sidebar()
    role = (st.session_state.get("user_role") or "member").lower()

    if role == "admin":
        render_admin_console()
        return

    # For other roles, display high-level dashboard and navigation guide
    gym_name = st.session_state.get("gym_name", "FitZone Premium Gym")
    render_navbar("Facility Overview", f"Welcome to {gym_name}")

    if role == "owner":
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.7); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <h2 style="margin: 0 0 0.5rem 0; color: #F8FAFC;">Owner Command Center</h2>
                <p style="color: #94A3B8; margin: 0;">Navigate to <b>Daily Report</b> for in-depth analytics, revenue charts, and membership statistics, or inspect <b>Inactive Members</b> to run WhatsApp retention campaigns.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                """
                <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 14px; padding: 1.25rem; text-align: center;">
                    <div style="font-size: 2rem;">📊</div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-top: 0.5rem;">Daily Report & KPIs</div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 0.25rem;">Plotly revenue, attendance trends, and collections</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Open Daily Report", key="go_report", use_container_width=True):
                st.switch_page("pages/8_Daily_Report.py")
        with col2:
            st.markdown(
                """
                <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(6, 214, 201, 0.3); border-radius: 14px; padding: 1.25rem; text-align: center;">
                    <div style="font-size: 2rem;">⚠️</div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-top: 0.5rem;">Inactive Member Recovery</div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 0.25rem;">Identify absent members & trigger WhatsApp alerts</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Open Inactive Members", key="go_inactive", use_container_width=True):
                st.switch_page("pages/9_Inactive_Members.py")
        with col3:
            st.markdown(
                """
                <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(163, 255, 92, 0.3); border-radius: 14px; padding: 1.25rem; text-align: center;">
                    <div style="font-size: 2rem;">👥</div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: #F8FAFC; margin-top: 0.5rem;">Member Registration</div>
                    <div style="font-size: 0.82rem; color: #94A3B8; margin-top: 0.25rem;">Enroll new members & generate QR passes</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Open Registration", key="go_register", use_container_width=True):
                st.switch_page("pages/1_Member.py")

    elif role == "receptionist":
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.7); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <h2 style="margin: 0 0 0.5rem 0; color: #F8FAFC;">Front Desk Operations</h2>
                <p style="color: #94A3B8; margin: 0;">Perform daily QR check-ins, record membership fees, and manage upcoming plan renewals.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📸 Check-in Scanner & Attendance", use_container_width=True):
                st.switch_page("pages/2_Attendance.py")
        with col2:
            if st.button("💳 Fee Collection & Receipts", use_container_width=True):
                st.switch_page("pages/4_Fees.py")
        with col3:
            if st.button("🔄 Membership Renewals", use_container_width=True):
                st.switch_page("pages/5_Renewals.py")

    elif role == "trainer":
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.7); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <h2 style="margin: 0 0 0.5rem 0; color: #F8FAFC;">Trainer Dashboard</h2>
                <p style="color: #94A3B8; margin: 0;">Manage your assigned athletes, formulate custom exercise regimes, and design nutritional meal plans.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏋️ My Assigned Members", use_container_width=True):
                st.switch_page("pages/6_My_Members.py")
        with col2:
            if st.button("🥗 Nutritional Diet Plans", use_container_width=True):
                st.switch_page("pages/7_Diet_Plan.py")

    else:  # member
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.7); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <h2 style="margin: 0 0 0.5rem 0; color: #F8FAFC;">Welcome to Your Gym Buddy</h2>
                <p style="color: #94A3B8; margin: 0;">Track your check-ins, view your trainer-assigned workouts, and stay on top of your daily nutrition.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📱 My QR Attendance Pass", use_container_width=True):
                st.switch_page("pages/2_Attendance.py")
        with col2:
            if st.button("⚡ My Workout Schedule", use_container_width=True):
                st.switch_page("pages/3_Workout.py")
        with col3:
            if st.button("🥗 My Diet Plan", use_container_width=True):
                st.switch_page("pages/7_Diet_Plan.py")


if not is_authenticated():
    render_login_screen()
else:
    render_authenticated_home()
