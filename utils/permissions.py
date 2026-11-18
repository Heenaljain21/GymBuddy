"""Role-based access control and page guard utilities for GYM BUDDY.

Ensures users only access views authorized for their role.
"""

from __future__ import annotations
from typing import List, Union
import streamlit as st


def require_auth() -> bool:
    """Ensure user is logged in. If not, redirect to login page."""
    if not st.session_state.get("authenticated", False):
        st.warning("⚠️ Access restricted. Please sign in to continue.")
        st.stop()
        return False
    return True


def require_role(allowed_roles: Union[str, List[str]]) -> bool:
    """Ensure logged in user has one of the allowed roles.
    
    Allowed roles: 'owner', 'receptionist', 'trainer', 'member', 'admin'.
    Admin automatically inherits all permissions.
    """
    require_auth()
    
    current_role = (st.session_state.get("user_role") or "member").lower()
    
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles.lower()]
    else:
        allowed_roles = [r.lower() for r in allowed_roles]
        
    # Platform Admin can view and do everything
    if current_role == "admin":
        return True
        
    if current_role not in allowed_roles:
        st.markdown(
            f"""
            <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 2rem; text-align: center; margin-top: 2rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔒</div>
                <h3 style="color: #F87171; margin-bottom: 0.5rem;">Access Denied</h3>
                <p style="color: #94A3B8; font-size: 0.95rem;">Your account role (<b>{current_role.upper()}</b>) is not authorized to view this page.</p>
                <p style="color: #64748B; font-size: 0.85rem;">Required role: {', '.join([r.upper() for r in allowed_roles])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()
        return False
        
    return True


def is_role(role: str) -> bool:
    """Check if current user matches given role."""
    current_role = (st.session_state.get("user_role") or "").lower()
    return current_role == role.lower() or current_role == "admin"
