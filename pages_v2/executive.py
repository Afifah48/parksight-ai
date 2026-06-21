"""
pages_v2/executive.py
=====================
Executive Dashboard — Screenshot 1.
3-column layout: Vital Signs | Ops Map + Tables | Tactical Feed
"""

import streamlit as st
from styles_v2.theme import COLORS, inject_v2_theme, BAND_COLORS
from styles_v2.components import inject_component_css
from components_v2.sidebar import render_sidebar
from components_v2.topbar import render_topbar
from components_v2.kpi_card import render_vital_sign
from components_v2.data_table import render_priority_table
from components_v2.map_renderer import create_dark_map, add_hotspot_markers, add_heatmap, render_map
from components_v2.chart_factory import grouped_bar_chart, bar_chart
from components_v2.tactical_feed import render_tactical_feed
from components_v2.alert_badge import priority_badge

# ---------------------------------------------------------------------------
# Theme + sidebar
# ---------------------------------------------------------------------------
inject_v2_theme()
st.markdown(inject_component_css(), unsafe_allow_html=True)
render_sidebar(active_page="Executive")

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
render_topbar(search_placeholder="Search operational data...")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    from src.data_service import (
        city_kpis, get_hotspots, get_priority_hotspots,
        get_station_summary,
    )
    from src.recommendation_engine import generate_recommendations

    kpis = city_kpis()
    hotspots_df = get_hotspots()
    top_hotspots = get_priority_hotspots(top_n=10)
    station_summary = get_station_summary()
    recommendations = generate_recommendations()
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# 3-column layout
# ---------------------------------------------------------------------------
col_left, col_center, col_right = st.columns([1.2, 2.8, 1.5], gap="medium")

# ========================== LEFT — Vital Signs ==========================
with col_left:
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between;
                    margin-bottom:14px;">
            <span style="font-size:0.95rem; font-weight:700; color:{COLORS['text_bright']};">
                Vital Signs
            </span>
            <span style="color:{COLORS['text_muted']}; font-size:0.85rem; cursor:pointer;">📊</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_vital_sign(
        label="Total Violations",
        value=f"{kpis['total_violations']:,}",
        trend_value="↗ +4.2% today",
        trend_direction="up",
    )

    # Readiness score
    readiness = 92
    render_vital_sign(
        label="Readiness Score",
        value=f"{readiness}/100",
        progress=readiness / 100,
        progress_color=COLORS["low"],
    )

    render_vital_sign(
        label="Critical Hotspots",
        value=str(kpis["critical_hotspots"]),
        subtitle="Active Intervention Required",
    )

    render_vital_sign(
        label="Emerging Hotspots",
        value=str(kpis["emerging_hotspots"]),
        subtitle="Predictive model flag",
    )

    render_vital_sign(
        label="Repeat Offenders",
        value=str(kpis["repeat_offenders"]),
        trend_value="↘ -2.1% this week",
        trend_direction="down",
    )

    render_vital_sign(
        label="Congestion Reduction",
        value="15%",
        subtitle="vs 30-day baseline",
    )

# ========================== CENTER — Ops Map + Tables ==========================
with col_center:
    # Map header
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between;
                    margin-bottom:8px;">
            <span style="font-size:0.88rem; font-weight:600; color:{COLORS['text_bright']};">
                Bengaluru Ops Live
            </span>
            <div style="display:flex; gap:8px;">
                <span style="color:{COLORS['text_muted']}; cursor:pointer;">⚙️</span>
                <span style="color:{COLORS['text_muted']}; cursor:pointer;">🔍</span>
                <span style="color:{COLORS['text_muted']}; cursor:pointer;">⊕</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dark ops map
    m = create_dark_map(zoom=12)
    add_hotspot_markers(
        m, hotspots_df,
        popup_cols=["priority_band", "pcis_score", "violation_count"],
    )
    add_heatmap(m, hotspots_df, weight_col="priority_score")
    render_map(m, height=420, key="exec_map")

    # Below map — 2 sub-columns
    sub_left, sub_right = st.columns([1.3, 1], gap="medium")

    with sub_left:
        # Top Priority Hotspots table
        table_cols = [
            {"key": "hotspot_name", "label": "Location", "fmt": "text"},
            {"key": "priority_band", "label": "Risk Lvl", "fmt": "badge", "align": "center"},
            {"key": "violation_count", "label": "Violations", "fmt": "number", "align": "right"},
        ]
        render_priority_table(
            top_hotspots, table_cols, max_rows=6,
            title="Top Priority Hotspots", show_chevron=True,
        )

    with sub_right:
        # Citywide Risk Trend — bar chart from station summary
        if not station_summary.empty:
            chart_data = station_summary.head(8).copy()
            chart_data["station_short"] = chart_data["police_station"].str.replace(
                "Traffic PS", ""
            ).str.strip().str[:12]
            fig = bar_chart(
                chart_data, x="station_short", y="max_priority",
                title="Citywide Risk Trend", height=280,
            )
            st.plotly_chart(fig, use_container_width=True, key="risk_trend")

# ========================== RIGHT — Tactical Feed ==========================
with col_right:
    render_tactical_feed(recommendations)
