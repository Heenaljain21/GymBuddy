"""Authentication service for GYM BUDDY.

Handles Supabase Auth, credentials verification, profile resolution,
and session state synchronization.
"""

from __future__ import annotations
from typing import Optional, Tuple

import streamlit as st

from utils.security import get_supabase_client, is_demo_mode, SESSION_KEYS, _secret
from utils.validators import validate_email

MIN_PASSWORD_LENGTH = 8


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
        if "not confirmed" in str(e).lower():
            return False, "Please confirm your email first: open the link we sent you, then sign in."
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


def sign_up(full_name: str, email: str, password: str, confirm: str) -> Tuple[bool, str]:
    """Create a member login. Supabase emails a confirmation link; once it is clicked
    the database links the login to the member record with the same email.

    Returns (ok, message). The message never reveals whether an email is registered.
    """
    name = " ".join((full_name or "").split())
    clean_email = (email or "").strip().lower()
    if len(name) < 2:
        return False, "Please enter your full name."
    if not clean_email or not validate_email(clean_email):
        return False, "Please enter a valid email address."
    if len(password or "") < MIN_PASSWORD_LENGTH:
        return False, f"Use a password of at least {MIN_PASSWORD_LENGTH} characters."
    if password != confirm:
        return False, "The two passwords don't match."
    if is_demo_mode():
        return False, "Account creation works once the app is connected to your gym's database. In demo mode, use the demo accounts below."

    options = {"data": {"full_name": name}}
    redirect = _secret("supabase", "site_url")
    if redirect:
        options["email_redirect_to"] = redirect
    try:
        res = get_supabase_client().auth.sign_up({"email": clean_email, "password": password, "options": options})
    except Exception as e:
        msg = str(e).lower()
        if "rate limit" in msg or "too many" in msg:
            return False, "Too many sign-ups right now. Please try again in an hour, or ask the front desk for help."
        if "already registered" in msg or "already exists" in msg:
            return False, "This email already has an account. Sign in instead, or use “Forgot password?”."
        if "password" in msg:
            return False, f"That password isn't accepted: {e}"
        return False, f"Could not create the account: {e}"

    if getattr(res, "session", None):
        # Email confirmation is switched off in Supabase: the account is live immediately.
        return True, "Account created. You can sign in now."
    return True, (f"Almost done! We've sent a confirmation link to {clean_email}. "
                  "Open it, then come back here and sign in. Check your spam folder if it doesn't arrive in a few minutes.")


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
