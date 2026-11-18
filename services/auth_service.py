"""Authentication service for GYM BUDDY.

Handles Supabase Auth, credentials verification, profile resolution,
and session state synchronization.
"""

from __future__ import annotations
from typing import Optional, Tuple

import streamlit as st

from utils.security import get_supabase_client, SESSION_KEYS


def _first(res) -> dict:
    return res.data[0] if (res and res.data) else {}


def sign_in(email: str, password: str) -> Tuple[bool, Optional[str]]:
    """Sign in user using Supabase Auth (or the demo database) and populate session state."""
    clean_email = (email or "").strip().lower()
    if not clean_email or not password:
        return False, "Please enter both email and password."

    client = get_supabase_client()
    try:
        res = client.auth.sign_in_with_password({"email": clean_email, "password": password})
    except Exception as e:
        if "invalid" in str(e).lower() or "credentials" in str(e).lower():
            return False, "Invalid email or password."
        return False, f"Authentication error: {e}"

    if not res or not getattr(res, "user", None):
        return False, "Invalid email or password."

    user_id = str(res.user.id)
    try:
        profile = _first(client.table("profiles").select("*").eq("id", user_id).execute())
        if not profile:
            profile = _first(client.table("profiles").select("*").eq("email", clean_email).execute())
    except Exception as e:
        return False, f"Could not load your profile: {e}"

    if not profile:
        return False, "Your account has no GYM BUDDY profile yet. Ask your gym admin to set it up."

    role = (profile.get("role") or "member").lower()
    gym_id = profile.get("gym_id")
    gym_name = "GYM BUDDY"
    if gym_id:
        gym = _first(client.table("gyms").select("name").eq("id", gym_id).execute())
        gym_name = gym.get("name") or gym_name

    member_id = None
    if role == "member" and gym_id:
        member = _first(client.table("members").select("id").eq("gym_id", gym_id).eq("user_id", user_id).execute())
        if not member:
            member = _first(client.table("members").select("id").eq("gym_id", gym_id).eq("email", clean_email).execute())
        member_id = member.get("id")

    st.session_state["authenticated"] = True
    st.session_state["user"] = {"id": user_id, "email": str(res.user.email)}
    st.session_state["user_role"] = role
    st.session_state["gym_id"] = gym_id
    st.session_state["gym_name"] = gym_name
    st.session_state["profile"] = profile
    st.session_state["member_id"] = member_id
    session = getattr(res, "session", None)
    st.session_state["access_token"] = getattr(session, "access_token", None)
    return True, None


def sign_out() -> None:
    """Log out current user and clear session state (keeps the demo database for this tab)."""
    try:
        get_supabase_client().auth.sign_out()
    except Exception:
        pass
    for key in SESSION_KEYS:
        st.session_state.pop(key, None)
    st.session_state["authenticated"] = False
    st.session_state["user_role"] = "guest"


def is_authenticated() -> bool:
    return bool(st.session_state.get("authenticated", False))


def current_user_id() -> Optional[str]:
    profile = st.session_state.get("profile") or {}
    user = st.session_state.get("user") or {}
    return profile.get("id") or user.get("id")
