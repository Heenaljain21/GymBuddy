"""Data table and status badge components for GYM BUDDY.

Provides futuristic table layouts and neon status badges.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st


def render_status_badge(status: str) -> str:
    """Return HTML string for futuristic status badge."""
    s = (status or "").lower()
    
    status_map = {
        "active": {"bg": "rgba(163, 255, 92, 0.12)", "color": "#A3FF5C", "border": "rgba(163, 255, 92, 0.3)", "label": "Active"},
        "expiring": {"bg": "rgba(245, 158, 11, 0.15)", "color": "#F59E0B", "border": "rgba(245, 158, 11, 0.4)", "label": "Expiring Soon"},
        "expired": {"bg": "rgba(239, 68, 68, 0.15)", "color": "#EF4444", "border": "rgba(239, 68, 68, 0.4)", "label": "Expired"},
        "inactive": {"bg": "rgba(148, 163, 184, 0.12)", "color": "#94A3B8", "border": "rgba(148, 163, 184, 0.25)", "label": "Inactive"},
        "pending": {"bg": "rgba(236, 72, 153, 0.15)", "color": "#EC4899", "border": "rgba(236, 72, 153, 0.4)", "label": "Pending"},
        "completed": {"bg": "rgba(6, 214, 201, 0.15)", "color": "#06D6C9", "border": "rgba(6, 214, 201, 0.4)", "label": "Completed"},
        "paid": {"bg": "rgba(163, 255, 92, 0.15)", "color": "#A3FF5C", "border": "rgba(163, 255, 92, 0.4)", "label": "Paid"},
    }
    
    style = status_map.get(s, {"bg": "rgba(139, 92, 246, 0.15)", "color": "#8B5CF6", "border": "rgba(139, 92, 246, 0.3)", "label": status.capitalize()})
    
    return f"""<span style="background: {style['bg']}; color: {style['color']}; border: 1px solid {style['border']}; padding: 3px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; display: inline-flex; align-items: center; gap: 4px;"><span style="width: 6px; height: 6px; border-radius: 50%; background: {style['color']};"></span>{style['label']}</span>"""


def render_data_table(
    df: pd.DataFrame,
    columns_config: Optional[Dict[str, Any]] = None,
    use_container_width: bool = True,
    hide_index: bool = True,
) -> None:
    """Render a styled Streamlit dataframe."""
    if df.empty:
        st.markdown(
            """
            <div style="background: rgba(23, 29, 48, 0.5); border: 1px dashed rgba(148, 163, 184, 0.2); border-radius: 12px; padding: 2.5rem; text-align: center; color: #94A3B8;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📂</div>
                <div style="font-size: 0.95rem; font-weight: 600;">No records found</div>
                <div style="font-size: 0.8rem; color: #64748B;">Try adjusting your filters or date range</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.dataframe(
        df,
        use_container_width=use_container_width,
        hide_index=hide_index,
        column_config=columns_config,
    )
