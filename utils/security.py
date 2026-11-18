"""Security and Supabase client initialization for GYM BUDDY.

Handles Supabase client connection with environment secrets, session state lifecycle,
and offline fallback simulation for commercial demonstrations.
"""

from __future__ import annotations
import os
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

class SessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return None
    def __setattr__(self, key, value):
        self[key] = value
    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            pass

try:
    import streamlit as st
    if not hasattr(st, "session_state"):
        st.session_state = SessionState()
    if not hasattr(st, "secrets"):
        st.secrets = {}
except Exception:
    import types
    st = types.ModuleType("streamlit")
    st.session_state = SessionState()
    st.secrets = {}


def init_session_state() -> None:
    """Initialize all core session state variables with default values."""
    defaults = {
        "authenticated": False,
        "user": None,
        "user_role": "guest",
        "gym_id": "00000000-0000-0000-0000-000000000001",
        "gym_name": "FitZone Premium Gym",
        "profile": {},
        "access_token": None,
        "demo_mode": False,
        "supabase_client": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_supabase_credentials() -> tuple[Optional[str], Optional[str]]:
    """Retrieve Supabase URL and Key from Streamlit secrets or OS environment."""
    url = None
    key = None

    # Check Streamlit secrets first
    try:
        if hasattr(st, "secrets") and "supabase" in st.secrets:
            url = st.secrets["supabase"].get("url") or st.secrets["supabase"].get("SUPABASE_URL")
            key = st.secrets["supabase"].get("key") or st.secrets["supabase"].get("SUPABASE_KEY")
        elif hasattr(st, "secrets") and "SUPABASE_URL" in st.secrets:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets.get("SUPABASE_KEY") or st.secrets.get("SUPABASE_ANON_KEY")
    except Exception:
        pass

    # Fallback to os.environ / .env
    if not url:
        url = os.getenv("SUPABASE_URL")
    if not key:
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    return url, key


def get_supabase_client():
    """Return an active Supabase client or a local fallback client if credentials missing."""
    if hasattr(st, "session_state") and getattr(st.session_state, "supabase_client", None) is not None:
        return st.session_state.supabase_client

    url, key = get_supabase_credentials()

    if url and key and not url.startswith("https://your-project"):
        try:
            from supabase import create_client, Client
            client: Client = create_client(url, key)
            if hasattr(st, "session_state"):
                st.session_state.supabase_client = client
                st.session_state.demo_mode = False
            return client
        except Exception:
            pass

    # Local fallback mode for demo / offline reliability
    from .mock_db import get_local_db
    local_client = get_local_db()
    if hasattr(st, "session_state"):
        st.session_state.supabase_client = local_client
        st.session_state.demo_mode = True
    return local_client
