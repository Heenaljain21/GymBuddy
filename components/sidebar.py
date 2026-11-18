"""Sidebar navigation component for GYM BUDDY.

Provides role-based navigation menus, branding display, gym switcher context,
user profile summary, and logout handling.
"""

from __future__ import annotations

import os
from typing import Optional
import streamlit as st
from streamlit_option_menu import option_menu


def _get_role_menu_config(role: str) -> tuple[list[str], list[str]]:
    """Return navigation labels and bootstrap icons for the given role."""
    role_normalized = (role or "").strip().lower()

    if role_normalized == "admin":
        menu_items = ["Dashboard", "Manage Gyms", "Manage Users"]
        icons = ["speedometer2", "building", "people"]
    elif role_normalized == "owner":
        menu_items = ["Dashboard", "Members", "Staff", "Reports", "Inactive Members"]
        icons = ["speedometer2", "people", "person-badge", "bar-chart-line", "clock-history"]
    elif role_normalized == "receptionist":
        menu_items = ["Attendance", "Fees", "Renewals", "Members"]
        icons = ["calendar-check", "cash-stack", "arrow-repeat", "people"]
    elif role_normalized == "trainer":
        menu_items = ["My Members", "Workout Plans", "Diet Plans"]
        icons = ["people", "activity", "egg-fried"]
    elif role_normalized == "member":
        menu_items = ["My Profile", "QR Attendance", "Workout Plan", "Diet Plan"]
        icons = ["person-circle", "qr-code-scan", "lightning-charge", "heart-pulse"]
    else:
        menu_items = ["Login"]
        icons = ["box-arrow-in-right"]

    return menu_items, icons


def render_sidebar() -> str:
    """Render the GYM BUDDY premium dark sidebar.

    Displays logo, gym context, role badge, role-appropriate navigation
    using streamlit_option_menu, user profile details, and logout action.

    Returns:
        The selected navigation label (str).
    """
    with st.sidebar:
        # 1. Logo & App Branding
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(os.path.dirname(current_dir), "assets", "logo.png")

        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 0.85rem; padding: 0.5rem 0 1.25rem 0;">
                <div style="width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 14px rgba(139, 92, 246, 0.45); font-size: 1.4rem;">
                    🏋️
                </div>
                <div>
                    <div style="font-family: 'Outfit', sans-serif; font-size: 1.35rem; font-weight: 900; letter-spacing: 0.05em; background: linear-gradient(135deg, #FFFFFF 0%, #A78BFA 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; line-height: 1.1;">
                        GYM BUDDY
                    </div>
                    <div style="font-size: 0.7rem; font-weight: 700; color: #06D6C9; letter-spacing: 0.16em; text-transform: uppercase;">
                        Commercial SaaS
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if os.path.exists(logo_path):
            try:
                st.image(logo_path, width=190)
            except Exception:
                pass

        # 2. Gym Name & Role Badge
        gym_name = st.session_state.get("gym_name") or "Primary Facility"
        user_role = (st.session_state.get("user_role") or "guest").lower()
        role_class = f"role-badge-{user_role}"

        st.markdown(
            f"""
            <div style="background: rgba(23, 29, 48, 0.65); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 1.25rem;">
                <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.25rem;">Active Facility</div>
                <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 0.98rem; color: #F8FAFC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 0.5rem;">
                    🏢 {gym_name}
                </div>
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span style="font-size: 0.75rem; color: #64748B;">Role</span>
                    <span class="role-badge {role_class}">{user_role.upper()}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 3. Role-Based Navigation Menu
        menu_items, icons = _get_role_menu_config(user_role)

        menu_styles = {
            "container": {
                "padding": "0!important",
                "background-color": "transparent",
            },
            "icon": {
                "color": "#94A3B8",
                "font-size": "15px",
            },
            "nav-link": {
                "font-size": "0.92rem",
                "text-align": "left",
                "margin": "4px 0",
                "color": "#94A3B8",
                "border-radius": "10px",
                "font-weight": "500",
                "font-family": "Outfit, Inter, sans-serif",
                "padding": "10px 14px",
                "transition": "all 0.2s ease",
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%)",
                "color": "#FFFFFF",
                "font-weight": "700",
                "box-shadow": "0 4px 14px rgba(139, 92, 246, 0.4)",
            },
        }

        # Check existing selection state if present
        current_selection = option_menu(
            menu_title=None,
            options=menu_items,
            icons=icons,
            menu_icon="cast",
            default_index=0,
            styles=menu_styles,
            key=f"sidebar_nav_{user_role}",
        )

        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

        # 4. User Profile Section & Logout
        profile = st.session_state.get("profile") or {}
        user = st.session_state.get("user") or {}

        full_name = (
            profile.get("full_name")
            or profile.get("name")
            or user.get("email", "Member").split("@")[0].title()
        )
        email = user.get("email") or profile.get("email") or "account@gymbuddy.io"
        initial = (full_name[:1] if full_name else "U").upper()

        st.markdown(
            f"""
            <div style="background: rgba(17, 21, 37, 0.85); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 12px; padding: 0.85rem; margin-top: auto; margin-bottom: 0.75rem;">
                <div style="display: flex; align-items: center; gap: 0.75rem;">
                    <div style="width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.95rem; color: #FFFFFF; flex-shrink: 0; box-shadow: 0 2px 8px rgba(139, 92, 246, 0.4);">
                        {initial}
                    </div>
                    <div style="min-width: 0; flex: 1;">
                        <div style="font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 0.88rem; color: #F8FAFC; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {full_name}
                        </div>
                        <div style="font-size: 0.74rem; color: #94A3B8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {email}
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.sidebar.button("🚪 Sign Out", key="gym_buddy_logout_btn", use_container_width=True):
            for k in [
                "authenticated",
                "user",
                "user_role",
                "gym_id",
                "gym_name",
                "profile",
                "access_token",
            ]:
                st.session_state.pop(k, None)
            st.session_state.authenticated = False
            st.rerun()

        return current_selection
