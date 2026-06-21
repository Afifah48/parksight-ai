"""
components_v2/kpi_card.py
=========================
KPI card and vital sign renderers for ParkSight AI V2.
"""

import streamlit as st
from styles_v2.theme import COLORS


def render_vital_sign(label, value, subtitle="", trend_value=None, trend_direction="neutral",
                      progress=None, progress_color=None):
    """Render a single vital-sign card (used in the Executive Dashboard left panel).

    Parameters
    ----------
    label : str
        Uppercase label (e.g., "TOTAL VIOLATIONS").
    value : str
        Large display value (e.g., "12,450" or "92/100").
    subtitle : str
        Secondary text below value (e.g., "Active Intervention Required").
    trend_value : str, optional
        Trend indicator text (e.g., "+4.2% today").
    trend_direction : str
        One of "up", "down", "neutral" — controls trend color.
    progress : float, optional
        If set, render a progress bar (0.0 to 1.0).
    progress_color : str, optional
        Color override for the progress bar fill.
    """
    trend_class = {
        "up": "v2-trend-up",
        "down": "v2-trend-down",
        "neutral": "v2-trend-neutral",
    }.get(trend_direction, "v2-trend-neutral")

    trend_html = ""
    if trend_value:
        trend_html = f'<div class="v2-vital-trend {trend_class}">{trend_value}</div>'

    progress_html = ""
    if progress is not None:
        p_color = progress_color or COLORS["low"]
        pct = min(max(progress * 100, 0), 100)
        progress_html = f"""
            <div class="v2-progress">
                <div class="v2-progress-fill" style="width:{pct}%; background:{p_color};"></div>
            </div>
        """

    subtitle_html = ""
    if subtitle:
        subtitle_html = f'<div class="v2-vital-sub">{subtitle}</div>'

    st.markdown(
        f"""
        <div class="v2-vital">
            <div class="v2-vital-label">{label}</div>
            <div class="v2-vital-value">{value}</div>
            {subtitle_html}
            {trend_html}
            {progress_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_strip(kpis, columns=None):
    """Render a horizontal row of st.metric KPI cards.

    Parameters
    ----------
    kpis : list of dict
        Each dict has keys: label, value, delta (optional), delta_color (optional).
    columns : int, optional
        Number of columns. Defaults to len(kpis).
    """
    n = columns or len(kpis)
    cols = st.columns(n)
    for i, kpi in enumerate(kpis):
        with cols[i % n]:
            delta = kpi.get("delta")
            st.metric(
                label=kpi["label"],
                value=kpi["value"],
                delta=delta,
            )


def render_stat_pair(label1, value1, label2, value2):
    """Render two stat values side-by-side within a card context."""
    st.markdown(
        f"""
        <div style="display:flex; gap:20px; margin:8px 0;">
            <div>
                <div class="v2-vital-label">{label1}</div>
                <div style="font-size:1.3rem; font-weight:700; color:{COLORS['accent_cyan']};">{value1}</div>
            </div>
            <div>
                <div class="v2-vital-label">{label2}</div>
                <div style="font-size:1.3rem; font-weight:700; color:{COLORS['text_bright']};">{value2}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
