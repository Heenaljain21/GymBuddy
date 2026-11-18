"""Top navigation bar component for GYM BUDDY.

Displays page title, active gym facility, current date in Indian standard format,
and personalized time-of-day greetings for staff and members.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import streamlit as st

try:
    from zoneinfo import ZoneInfo
    IST_TZ = ZoneInfo("Asia/Kolkata")
except Exception:
    IST_TZ = None


def _get_kolkata_now() -> datetime:
    """Return current timestamp localized to Asia/Kolkata."""
    if IST_TZ is not None:
        return datetime.now(IST_TZ)
    return datetime.now()


def _get_time_greeting(hour: int) -> str:
    """Return time-appropriate greeting text."""
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 17:
        return "Good Afternoon"
    else:
        return "Good Evening"


def render_navbar(
    page_title: str = "Dashboard",
    subtitle: Optional[str] = None,
) -> None:
    """Render the top navigation bar header.

    Args:
        page_title: Main heading for the active view.
        subtitle: Optional contextual sub-caption.
    """
    now = _get_kolkata_now()
    date_formatted = now.strftime("%A, %d %b %Y")
    time_formatted = now.strftime("%I:%M %p IST")
    greeting_prefix = _get_time_greeting(now.hour)

    gym_name = st.session_state.get("gym_name") or "Primary Facility"
    profile = st.session_state.get("profile") or {}
    user = st.session_state.get("user") or {}
    user_role = (st.session_state.get("user_role") or "Member").capitalize()

    full_name = (
        profile.get("full_name")
        or profile.get("name")
        or (user.get("email", "").split("@")[0].title() if user.get("email") else "Partner")
    )

    default_subtitle = subtitle or f"Active Facility: {gym_name} • Role: {user_role}"

    col_title, col_meta = st.columns([3, 2])

    with col_title:
        st.markdown(
            f"""
            <div style="padding: 0.25rem 0;">
                <h1 style="margin: 0; font-size: 1.85rem; font-weight: 800; letter-spacing: -0.025em; color: #F8FAFC;">
                    {page_title}
                </h1>
                <div style="font-size: 0.88rem; color: #94A3B8; margin-top: 0.2rem; display: flex; align-items: center; gap: 0.5rem;">
                    <span>🏢 {default_subtitle}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_meta:
        st.markdown(
            f"""
            <div style="display: flex; flex-direction: column; align-items: flex-end; justify-content: center; height: 100%; text-align: right;">
                <div style="font-size: 0.95rem; font-weight: 600; color: #F8FAFC;">
                    {greeting_prefix}, <span style="color: #06D6C9; font-weight: 700;">{full_name}</span> 👋
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.35rem;">
                    <span class="greeting-date">
                        📅 {date_formatted} • {time_formatted}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Decorative bottom neon separator
    st.markdown(
        """
        <div style="height: 1px; width: 100%; background: linear-gradient(90deg, rgba(139, 92, 246, 0.4) 0%, rgba(6, 214, 201, 0.4) 50%, transparent 100%); margin: 1rem 0 1.5rem 0;"></div>
        """,
        unsafe_allow_html=True,
    )
