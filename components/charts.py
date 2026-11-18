"""Interactive Plotly charts for GYM BUDDY.

Designed with dark futuristic theme, neon accents, and responsive layouts.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


DARK_LAYOUT = {
    "paper_bgcolor": "rgba(23, 29, 48, 0.75)",
    "plot_bgcolor": "rgba(17, 21, 37, 0.4)",
    "font": {"color": "#94A3B8", "family": "Outfit, Inter, sans-serif"},
    "xaxis": {
        "gridcolor": "rgba(148, 163, 184, 0.1)",
        "zerolinecolor": "rgba(148, 163, 184, 0.15)",
        "tickfont": {"color": "#94A3B8"},
    },
    "yaxis": {
        "gridcolor": "rgba(148, 163, 184, 0.1)",
        "zerolinecolor": "rgba(148, 163, 184, 0.15)",
        "tickfont": {"color": "#94A3B8"},
    },
    "margin": {"l": 30, "r": 20, "t": 40, "b": 30},
}


def get_chart_theme() -> Dict[str, Any]:
    """Return dark chart layout dictionary."""
    return DARK_LAYOUT.copy()


def render_revenue_chart(
    df: pd.DataFrame,
    x_col: str = "date",
    y_col: str = "amount",
    title: str = "Daily Revenue (₹)",
) -> None:
    """Render revenue bar/area chart with cyan to purple neon gradients."""
    fig = go.Figure()
    if not df.empty and x_col in df.columns and y_col in df.columns:
        fig.add_trace(
            go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker=dict(
                    color=df[y_col],
                    colorscale=[[0, "#3B82F6"], [0.5, "#8B5CF6"], [1, "#06D6C9"]],
                    line=dict(color="#06D6C9", width=1),
                ),
                hovertemplate="<b>Date:</b> %{x}<br><b>Revenue:</b> ₹%{y:,.2f}<extra></extra>",
            )
        )
    layout = get_chart_theme()
    layout["title"] = {"text": f"<b>{title}</b>", "font": {"color": "#F8FAFC", "size": 15}}
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_attendance_chart(
    df: pd.DataFrame,
    x_col: str = "date",
    y_col: str = "count",
    title: str = "Attendance Trends",
) -> None:
    """Render attendance line/spline chart with neon green/cyan styling."""
    fig = go.Figure()
    if not df.empty and x_col in df.columns and y_col in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode="lines+markers",
                line=dict(color="#A3FF5C", width=3, shape="spline"),
                marker=dict(size=8, color="#06D6C9", line=dict(color="#090B14", width=2)),
                fill="tozeroy",
                fillcolor="rgba(163, 255, 92, 0.1)",
                hovertemplate="<b>Date:</b> %{x}<br><b>Check-ins:</b> %{y}<extra></extra>",
            )
        )
    layout = get_chart_theme()
    layout["title"] = {"text": f"<b>{title}</b>", "font": {"color": "#F8FAFC", "size": 15}}
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_membership_distribution(
    df: pd.DataFrame,
    labels_col: str = "plan",
    values_col: str = "count",
    title: str = "Membership Plan Distribution",
) -> None:
    """Render donut chart of membership plans."""
    fig = go.Figure()
    if not df.empty and labels_col in df.columns and values_col in df.columns:
        colors = ["#8B5CF6", "#06D6C9", "#A3FF5C", "#3B82F6", "#EC4899", "#F59E0B"]
        fig.add_trace(
            go.Pie(
                labels=df[labels_col],
                values=df[values_col],
                hole=0.6,
                marker=dict(colors=colors, line=dict(color="#090B14", width=2)),
                hovertemplate="<b>%{label}</b><br>Members: %{value} (%{percent})<extra></extra>",
                textinfo="label+percent",
                textposition="outside",
            )
        )
    layout = get_chart_theme()
    layout["title"] = {"text": f"<b>{title}</b>", "font": {"color": "#F8FAFC", "size": 15}}
    layout["showlegend"] = False
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_member_growth_chart(
    df: pd.DataFrame,
    x_col: str = "date",
    y_col: str = "total",
    title: str = "Cumulative Member Growth",
) -> None:
    """Render member growth area chart."""
    fig = go.Figure()
    if not df.empty and x_col in df.columns and y_col in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode="lines",
                line=dict(color="#8B5CF6", width=3, shape="spline"),
                fill="tozeroy",
                fillcolor="rgba(139, 92, 246, 0.15)",
                hovertemplate="<b>Date:</b> %{x}<br><b>Total Members:</b> %{y}<extra></extra>",
            )
        )
    layout = get_chart_theme()
    layout["title"] = {"text": f"<b>{title}</b>", "font": {"color": "#F8FAFC", "size": 15}}
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
