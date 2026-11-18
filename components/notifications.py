"""Notification and alert toast components for GYM BUDDY.

Provides sleek notification alerts matching the futuristic theme.
"""

from __future__ import annotations
from typing import Optional
import streamlit as st


def show_success(message: str, subtitle: Optional[str] = None) -> None:
    """Render a futuristic success toast or message box."""
    sub_html = f"<div style='font-size: 0.8rem; color: #94A3B8; margin-top: 2px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); border-left: 4px solid #10B981; border-radius: 10px; padding: 0.85rem 1.1rem; margin: 0.75rem 0; box-shadow: 0 4px 14px rgba(16, 185, 129, 0.15);">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.25rem;">✅</span>
                <div>
                    <div style="font-size: 0.92rem; font-weight: 700; color: #34D399;">{message}</div>
                    {sub_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_error(message: str, subtitle: Optional[str] = None) -> None:
    """Render a futuristic error toast or message box."""
    sub_html = f"<div style='font-size: 0.8rem; color: #94A3B8; margin-top: 2px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.4); border-left: 4px solid #EF4444; border-radius: 10px; padding: 0.85rem 1.1rem; margin: 0.75rem 0; box-shadow: 0 4px 14px rgba(239, 68, 68, 0.15);">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.25rem;">❌</span>
                <div>
                    <div style="font-size: 0.92rem; font-weight: 700; color: #F87171;">{message}</div>
                    {sub_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_warning(message: str, subtitle: Optional[str] = None) -> None:
    """Render a futuristic warning toast or message box."""
    sub_html = f"<div style='font-size: 0.8rem; color: #94A3B8; margin-top: 2px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div style="background: rgba(245, 158, 11, 0.12); border: 1px solid rgba(245, 158, 11, 0.4); border-left: 4px solid #F59E0B; border-radius: 10px; padding: 0.85rem 1.1rem; margin: 0.75rem 0; box-shadow: 0 4px 14px rgba(245, 158, 11, 0.15);">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.25rem;">⚠️</span>
                <div>
                    <div style="font-size: 0.92rem; font-weight: 700; color: #FBBF24;">{message}</div>
                    {sub_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_info(message: str, subtitle: Optional[str] = None) -> None:
    """Render a futuristic info toast or message box."""
    sub_html = f"<div style='font-size: 0.8rem; color: #94A3B8; margin-top: 2px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div style="background: rgba(6, 214, 201, 0.12); border: 1px solid rgba(6, 214, 201, 0.4); border-left: 4px solid #06D6C9; border-radius: 10px; padding: 0.85rem 1.1rem; margin: 0.75rem 0; box-shadow: 0 4px 14px rgba(6, 214, 201, 0.15);">
            <div style="display: flex; align-items: center; gap: 0.75rem;">
                <span style="font-size: 1.25rem;">ℹ️</span>
                <div>
                    <div style="font-size: 0.92rem; font-weight: 700; color: #06D6C9;">{message}</div>
                    {sub_html}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
