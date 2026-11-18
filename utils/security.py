"""Security and Supabase client initialization for GYM BUDDY.

Handles Supabase client connection with environment secrets, session state lifecycle,
and offline fallback simulation for demonstrations.
"""

from __future__ import annotations
import os
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import streamlit as st

SESSION_KEYS = ["authenticated", "user", "user_role", "gym_id", "gym_name", "profile", "access_token", "member_id"]


def init_session_state() -> None:
    """Initialize all core session state variables with default values."""
    defaults = {
        "authenticated": False,
        "user": None,
        "user_role": "guest",
        "gym_id": None,
        "gym_name": "GYM BUDDY",
        "profile": {},
        "access_token": None,
        "member_id": None,
        "demo_mode": False,
        "supabase_client": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _secret(*path: str) -> Optional[str]:
    try:
        node = st.secrets
        for p in path:
            node = node[p]
        return str(node) if node else None
    except Exception:
        return None


def get_supabase_credentials() -> tuple[Optional[str], Optional[str]]:
    """Retrieve Supabase URL and anon key from Streamlit secrets or the environment.

    Accepts the [supabase] table (url + key / anon_key) or flat SUPABASE_* keys.
    """
    url = _secret("supabase", "url") or _secret("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = (
        _secret("supabase", "anon_key")
        or _secret("supabase", "key")
        or _secret("SUPABASE_ANON_KEY")
        or _secret("SUPABASE_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_KEY")
    )
    return url, key


def _has_live_credentials(url: Optional[str], key: Optional[str]) -> bool:
    return bool(url and key and "your-project" not in url and "your-anon-key" not in key)


def get_supabase_client():
    """Return this session's Supabase client, or an isolated demo database if not configured."""
    client = st.session_state.get("supabase_client")
    if client is not None:
        return client

    url, key = get_supabase_credentials()
    if _has_live_credentials(url, key):
        try:
            from supabase import create_client
            client = create_client(url, key)
            st.session_state["supabase_client"] = client
            st.session_state["demo_mode"] = False
            return client
        except Exception as e:  # pragma: no cover - depends on network
            st.session_state["supabase_error"] = str(e)

    from .mock_db import get_local_db
    client = get_local_db()
    st.session_state["supabase_client"] = client
    st.session_state["demo_mode"] = True
    return client


def is_demo_mode() -> bool:
    get_supabase_client()
    return bool(st.session_state.get("demo_mode"))
