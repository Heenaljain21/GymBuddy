"""Interactive Plotly charts for GYM BUDDY, styled to match the dark theme."""

from __future__ import annotations
from datetime import date
from typing import Any, Dict

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PURPLE = "#8B5CF6"
CYAN = "#22D3C5"
LIME = "#A3E635"
AMBER = "#F59E0B"
PALETTE = [PURPLE, CYAN, LIME, "#60A5FA", "#F472B6", AMBER]
CONFIG = {"displayModeBar": False, "responsive": True}


def _layout(title: str, height: int = 300, **extra: Any) -> Dict[str, Any]:
    layout: Dict[str, Any] = {
        "title": {"text": title, "font": {"color": "#E8ECF4", "size": 14, "family": "Outfit, Inter, sans-serif"}, "x": 0.01, "y": 0.96},
        "paper_bgcolor": "rgba(21, 26, 46, 0.6)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#94A0B8", "family": "Inter, sans-serif", "size": 12},
        "margin": {"l": 48, "r": 16, "t": 48, "b": 36},
        "height": height,
        "xaxis": {"gridcolor": "rgba(148,160,184,0.08)", "zeroline": False, "showline": False},
        "yaxis": {"gridcolor": "rgba(148,160,184,0.08)", "zeroline": False, "showline": False},
        "hoverlabel": {"bgcolor": "#1B2138", "bordercolor": "#262E4A", "font": {"color": "#E8ECF4"}},
        "showlegend": False,
        "bargap": 0.35,
    }
    layout.update(extra)
    return layout


def _date_axis(layout: Dict[str, Any], df: pd.DataFrame, x: str) -> None:
    if not df.empty and isinstance(df[x].iloc[0], date):
        layout["xaxis"]["tickformat"] = "%d %b"


def _show(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config=CONFIG, theme=None)


def _count_axis(layout: Dict[str, Any], df: pd.DataFrame, y: str) -> None:
    """Counts are whole numbers: no 0.2 / 0.4 ticks when the numbers are small."""
    top = float(df[y].max()) if not df.empty else 0.0
    layout["yaxis"]["tickformat"] = ",d"
    layout["yaxis"]["rangemode"] = "tozero"
    if top <= 5:
        layout["yaxis"]["dtick"] = 1
        layout["yaxis"]["range"] = [0, max(top, 1) * 1.15]


def bar_chart(df: pd.DataFrame, x: str, y: str, title: str, money: bool = False, color: str = PURPLE, height: int = 300) -> None:
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Bar(
            x=df[x], y=df[y],
            marker={"color": color, "line": {"width": 0}, "cornerradius": 6},
            hovertemplate=("%{x}<br><b>₹%{y:,.0f}</b>" if money else "%{x}<br><b>%{y}</b>") + "<extra></extra>",
        ))
    layout = _layout(title, height)
    _date_axis(layout, df, x)
    if money:
        layout["yaxis"]["tickprefix"] = "₹"
        layout["yaxis"]["tickformat"] = ",.0f"
    else:
        _count_axis(layout, df, y)
    fig.update_layout(**layout)
    _show(fig)


def line_chart(df: pd.DataFrame, x: str, y: str, title: str, color: str = CYAN, height: int = 300, fill: bool = True) -> None:
    fig = go.Figure()
    if not df.empty:
        r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
        fig.add_trace(go.Scatter(
            x=df[x], y=df[y], mode="lines+markers",
            line={"color": color, "width": 3, "shape": "spline", "smoothing": 0.6},
            marker={"size": 6, "color": color, "line": {"color": "#0B0E1A", "width": 2}},
            fill="tozeroy" if fill else None, fillcolor=f"rgba({r},{g},{b},0.12)",
            hovertemplate="%{x|%d %b}<br><b>%{y}</b><extra></extra>",
        ))
    layout = _layout(title, height)
    _date_axis(layout, df, x)
    _count_axis(layout, df, y)
    fig.update_layout(**layout)
    _show(fig)


def donut_chart(df: pd.DataFrame, labels: str, values: str, title: str, height: int = 300) -> None:
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Pie(
            labels=df[labels], values=df[values], hole=0.62, sort=False,
            marker={"colors": PALETTE, "line": {"color": "#0B0E1A", "width": 2}},
            textinfo="value", textfont={"color": "#fff", "size": 13},
            hovertemplate="<b>%{label}</b><br>%{value} members (%{percent})<extra></extra>",
        ))
        fig.add_annotation(text=f"<b>{int(df[values].sum())}</b><br><span style='font-size:11px'>active</span>",
                           showarrow=False, font={"size": 20, "color": "#E8ECF4"})
    layout = _layout(title, height, showlegend=True)
    layout["legend"] = {"orientation": "h", "y": -0.05, "font": {"size": 11}}
    fig.update_layout(**layout)
    _show(fig)
