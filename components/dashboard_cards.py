"""Dashboard stat card components for GYM BUDDY.

Provides futuristic styled metric cards with gradients, neon borders, and icons.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any
import streamlit as st


def render_stat_card(
    title: str,
    value: str | int | float,
    change: Optional[str] = None,
    icon: str = "📊",
    color: str = "purple",  # purple, cyan, lime, blue, pink, amber
    subtext: Optional[str] = None,
) -> None:
    """Render a single futuristic dark glassmorphic stat card."""
    color_accents = {
        "purple": {"glow": "rgba(139, 92, 246, 0.4)", "grad": "linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%)", "border": "#8B5CF6"},
        "cyan": {"glow": "rgba(6, 214, 201, 0.4)", "grad": "linear-gradient(135deg, #06D6C9 0%, #3B82F6 100%)", "border": "#06D6C9"},
        "lime": {"glow": "rgba(163, 255, 92, 0.4)", "grad": "linear-gradient(135deg, #A3FF5C 0%, #06D6C9 100%)", "border": "#A3FF5C"},
        "blue": {"glow": "rgba(59, 130, 246, 0.4)", "grad": "linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)", "border": "#3B82F6"},
        "pink": {"glow": "rgba(236, 72, 153, 0.4)", "grad": "linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%)", "border": "#EC4899"},
        "amber": {"glow": "rgba(245, 158, 11, 0.4)", "grad": "linear-gradient(135deg, #F59E0B 0%, #EF4444 100%)", "border": "#F59E0B"},
    }
    
    accent = color_accents.get(color.lower(), color_accents["purple"])
    
    change_html = ""
    if change:
        is_pos = "+" in change or "up" in change.lower() or "↑" in change
        chg_color = "#A3FF5C" if is_pos else ("#EF4444" if "-" in change else "#94A3B8")
        change_html = f"""<span style="font-size: 0.8rem; font-weight: 600; color: {chg_color}; margin-left: 0.5rem; background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 6px;">{change}</span>"""

    subtext_html = ""
    if subtext:
        subtext_html = f"""<div style="font-size: 0.74rem; color: #64748B; margin-top: 0.4rem;">{subtext}</div>"""

    card_html = f"""
    <div style="background: rgba(23, 29, 48, 0.85); border: 1px solid rgba(148, 163, 184, 0.15); border-radius: 16px; padding: 1.25rem; backdrop-filter: blur(12px); box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25); position: relative; overflow: hidden; transition: transform 0.2s ease, border-color 0.2s ease;">
        <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: {accent['grad']};"></div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
            <span style="font-size: 0.82rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #94A3B8;">{title}</span>
            <div style="width: 38px; height: 38px; border-radius: 10px; background: {accent['grad']}; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; box-shadow: 0 2px 10px {accent['glow']};">
                {icon}
            </div>
        </div>
        <div style="display: flex; align-items: baseline;">
            <span style="font-family: 'Outfit', sans-serif; font-size: 1.85rem; font-weight: 800; color: #F8FAFC; letter-spacing: -0.02em;">{value}</span>
            {change_html}
        </div>
        {subtext_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def render_stat_cards_row(cards: List[Dict[str, Any]]) -> None:
    """Render a row of metric stat cards.
    
    cards: list of dicts with keys: title, value, change, icon, color, subtext
    """
    if not cards:
        return
    cols = st.columns(len(cards))
    for idx, card in enumerate(cards):
        with cols[idx]:
            render_stat_card(
                title=card.get("title", ""),
                value=card.get("value", 0),
                change=card.get("change"),
                icon=card.get("icon", "📊"),
                color=card.get("color", "purple"),
                subtext=card.get("subtext"),
            )
