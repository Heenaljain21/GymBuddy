"""Reusable presentation helpers for GYM BUDDY views.

Every helper HTML-escapes user-provided text, so member names, notes, etc.
can never break the layout or inject markup.
"""

from __future__ import annotations
import base64
import functools
import html
import os
from typing import Any, Dict, Iterable, List, Optional

import streamlit as st

from utils.date_utils import get_ist_now, format_date_display, days_remaining
from utils.helpers import generate_whatsapp_link

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

STATUS_LABELS = {
    "active": "Active",
    "expiring": "Expiring soon",
    "expired": "Expired",
    "inactive": "Inactive",
    "no_plan": "No plan",
    "pending": "Pending",
    "contacted": "Contacted",
    "responded": "Responded",
    "returned": "Returned",
    "lost": "Lost",
}


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


@functools.lru_cache(maxsize=1)
def load_css() -> str:
    with open(os.path.join(ASSETS_DIR, "styles.css"), "r", encoding="utf-8") as f:
        return f.read()


@functools.lru_cache(maxsize=4)
def asset_data_uri(name: str) -> str:
    with open(os.path.join(ASSETS_DIR, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def html_block(markup: str) -> None:
    # Flatten the snippet: in Markdown, a blank line followed by indented HTML
    # turns into a code block, which would print raw tags on screen.
    flat = "\n".join(line.strip() for line in markup.splitlines() if line.strip())
    st.markdown(flat, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Flash messages (survive st.rerun)
# ---------------------------------------------------------------------------

def flash(message: str, icon: str = "✅") -> None:
    """Queue a toast to show on the next run (use right before st.rerun())."""
    st.session_state.setdefault("_flash", []).append((message, icon))


def show_flashes() -> None:
    for message, icon in st.session_state.pop("_flash", []):
        st.toast(message, icon=icon)


# ---------------------------------------------------------------------------
# Layout primitives
# ---------------------------------------------------------------------------

def greeting() -> str:
    hour = get_ist_now().hour
    if 5 <= hour < 12:
        return "Good morning"
    if 12 <= hour < 17:
        return "Good afternoon"
    return "Good evening"


def page_header(title: str, subtitle: str = "", eyebrow: str = "") -> None:
    now = get_ist_now()
    html_block(
        f"""
        <div class="gb-header">
          <div>
            {f'<div class="gb-eyebrow">{esc(eyebrow)}</div>' if eyebrow else ''}
            <h1>{esc(title)}</h1>
            {f'<div class="gb-sub">{esc(subtitle)}</div>' if subtitle else ''}
          </div>
          <div class="gb-meta"><b>{now.strftime('%A, %d %b %Y')}</b><br>{now.strftime('%I:%M %p')} IST</div>
        </div>
        """
    )


def stat_cards(cards: Iterable[Dict[str, Any]]) -> None:
    """Responsive KPI grid. Each card: label, value, icon, accent, sub."""
    parts = []
    for c in cards:
        parts.append(
            f"""<div class="gb-stat gb-accent-{esc(c.get('accent', 'purple'))}">
                  <div class="gb-stat-top"><span class="gb-stat-label">{esc(c.get('label'))}</span>
                  <span class="gb-stat-icon">{c.get('icon', '📊')}</span></div>
                  <div class="gb-stat-value">{esc(c.get('value'))}</div>
                  {f'<div class="gb-stat-sub">{esc(c["sub"])}</div>' if c.get('sub') else ''}
                </div>"""
        )
    html_block(f'<div class="gb-stats">{"".join(parts)}</div>')


def badge(status: str, label: Optional[str] = None) -> str:
    key = (status or "").lower()
    return f'<span class="gb-badge {esc(key)}">{esc(label or STATUS_LABELS.get(key, status))}</span>'


def chip(text: str) -> str:
    return f'<span class="gb-chip">{esc(text)}</span>'


def initials(name: str) -> str:
    parts = [p for p in (name or "?").split() if p]
    return esc("".join(p[0] for p in parts[:2]).upper() or "?")


def person_row(name: str, meta_html: str, badges_html: str = "") -> None:
    """Avatar + name + meta line. `meta_html` must already be escaped."""
    html_block(
        f"""
        <div class="gb-person">
          <div class="gb-avatar">{initials(name)}</div>
          <div style="min-width:0">
            <div class="gb-row-title">{esc(name)} {badges_html}</div>
            <div class="gb-row-meta">{meta_html}</div>
          </div>
        </div>
        """
    )


def empty_state(title: str, subtitle: str = "", icon: str = "✨") -> None:
    html_block(
        f"""
        <div class="gb-empty">
          <div class="gb-empty-icon">{icon}</div>
          <div class="gb-empty-title">{esc(title)}</div>
          {f'<div class="gb-empty-sub">{esc(subtitle)}</div>' if subtitle else ''}
        </div>
        """
    )


def whatsapp_button(phone: str, message: str, label: str = "WhatsApp") -> None:
    link = generate_whatsapp_link(phone, message)
    if link == "#":
        st.button(f"💬 {label}", disabled=True, width="stretch", key=f"wa_disabled_{phone}_{label}")
        return
    html_block(f'<a class="gb-wa" href="{esc(link)}" target="_blank" rel="noopener">💬 {esc(label)}</a>')


def kv_table(rows: List[tuple]) -> None:
    body = "".join(f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in rows)
    html_block(f'<table class="gb-kv">{body}</table>')


def result_banner(kind: str, title: str, subtitle: str = "") -> None:
    icon = {"ok": "✅", "warn": "⚠️", "err": "⛔"}.get(kind, "ℹ️")
    html_block(
        f"""
        <div class="gb-result {esc(kind)}">
          <div class="gb-result-icon">{icon}</div>
          <div><div class="gb-result-title">{esc(title)}</div>
          <div class="gb-result-sub">{esc(subtitle)}</div></div>
        </div>
        """
    )


def expiry_text(expiry: Optional[str]) -> str:
    if not expiry:
        return "No active plan"
    rem = days_remaining(expiry)
    if rem < 0:
        return f"Expired {abs(rem)} day{'s' if abs(rem) != 1 else ''} ago"
    if rem == 0:
        return "Expires today"
    return f"{rem} day{'s' if rem != 1 else ''} left · ends {format_date_display(expiry)}"


class Ctx:
    """Who is signed in and which gym they operate in."""

    def __init__(self) -> None:
        ss = st.session_state
        profile = ss.get("profile") or {}
        user = ss.get("user") or {}
        self.gym_id: str = ss.get("gym_id") or ""
        self.gym_name: str = ss.get("gym_name") or "GYM BUDDY"
        self.role: str = (ss.get("user_role") or "member").lower()
        self.user_id: str = profile.get("id") or user.get("id") or ""
        self.name: str = profile.get("full_name") or (user.get("email") or "there").split("@")[0].title()
        self.first_name: str = self.name.split()[0] if self.name else "there"
        self.member_id: Optional[str] = ss.get("member_id")

    @property
    def is_staff(self) -> bool:
        return self.role in ("admin", "owner", "receptionist")

    @property
    def can_coach(self) -> bool:
        return self.role in ("admin", "owner", "trainer")


def ctx() -> Ctx:
    return Ctx()


def require_role(*roles: str) -> None:
    """Stop rendering if the signed-in user lacks one of `roles` (admin always passes)."""
    role = (st.session_state.get("user_role") or "").lower()
    if role == "admin" or role in roles:
        return
    empty_state("You don't have access to this page", "Ask your gym owner if you need it.", "🔒")
    st.stop()


def unlinked_member_notice() -> None:
    """Shown to a member login that isn't attached to a membership yet."""
    email = (st.session_state.get("user") or {}).get("email") or "your email"
    empty_state(
        "Your account isn't linked to a membership yet",
        f"Ask the front desk to register you (or update your record) with the email {email}. "
        "It links automatically. Then sign out and sign in again.",
        "🔗",
    )
