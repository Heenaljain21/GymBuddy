"""Authentication service for GYM BUDDY.

Handles Supabase Auth, credentials verification, profile resolution,
and session state synchronization.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, Tuple

try:
    import streamlit as st
except Exception:
    import types
    st = types.ModuleType("streamlit")
    st.session_state = {}

from utils.security import get_supabase_client


def sign_in(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """Sign in user using Supabase Auth or mock client, and populate session state."""
    client = get_supabase_client()
    clean_email = (email or "").strip().lower()

    if not clean_email or not password:
        return False, "Please enter both email and password."

    try:
        res = client.auth.sign_in_with_password({"email": clean_email, "password": password})
        if not res or not hasattr(res, "user") or not res.user:
            return False, "Invalid email or password."

        user_id = str(res.user.id)
        email_val = str(res.user.email)
        token = res.session.access_token if hasattr(res, "session") and res.session else "token"

        # Resolve profile from profiles table
        profile_res = client.table("profiles").select("*").eq("email", clean_email).execute()
        profile_data = profile_res.data[0] if (profile_res.data and len(profile_res.data) > 0) else {}

        role = profile_data.get("role", "member")
        gym_id = profile_data.get("gym_id", "00000000-0000-0000-0000-000000000001")

        # Resolve gym name
        gym_name = "FitZone Premium Gym"
        if gym_id:
            gym_res = client.table("gyms").select("name").eq("id", gym_id).execute()
            if gym_res.data and len(gym_res.data) > 0:
                gym_name = gym_res.data[0].get("name", gym_name)

        # Set session state
        st.session_state["authenticated"] = True
        st.session_state["user"] = {"id": user_id, "email": email_val}
        st.session_state["user_role"] = role
        st.session_state["gym_id"] = gym_id
        st.session_state["gym_name"] = gym_name
        st.session_state["profile"] = profile_data
        st.session_state["access_token"] = token

        return True, None
    except Exception as e:
        err_msg = str(e)
        if "Invalid login credentials" in err_msg:
            return False, "Invalid email or password."
        return False, f"Authentication error: {err_msg}"


def sign_out() -> None:
    """Log out current user and clear session state."""
    try:
        client = get_supabase_client()
        client.auth.sign_out()
    except Exception:
        pass

    for key in ["authenticated", "user", "user_role", "gym_id", "gym_name", "profile", "access_token"]:
        if hasattr(st, "session_state"):
            if isinstance(st.session_state, dict):
                st.session_state.pop(key, None)
            else:
                st.session_state.pop(key, None)
    if hasattr(st, "session_state"):
        st.session_state["authenticated"] = False


def is_authenticated() -> bool:
    """Check if current session is authenticated."""
    if hasattr(st, "session_state"):
        if isinstance(st.session_state, dict):
            return bool(st.session_state.get("authenticated", False))
        return bool(st.session_state.get("authenticated", False))
    return False
