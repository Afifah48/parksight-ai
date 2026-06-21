"""
pages_v2/analytics.py
=====================
Analytics Deep-Dive — Priority Rankings + Score Decomposition + Correlations.
"""

import streamlit as st
import pandas as pd
from styles_v2.theme import COLORS, inject_v2_theme, BAND_COLORS
from styles_v2.components import inject_component_css
from components_v2.sidebar import render_sidebar
from components_v2.topbar import render_topbar
from components_v2.chart_factory import (
    stacked_bar_chart, donut_chart, scatter_chart, bar_chart,
)

# ---------------------------------------------------------------------------
# Theme + sidebar
# ---------------------------------------------------------------------------
inject_v2_theme()
st.markdown(inject_component_css(), unsafe_allow_html=True)
render_sidebar(active_page="Analytics")

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
render_topbar(module_name="Analytics")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    from src.data_service import get_hotspots, list_stations, list_bands

    stations = list_stations()
    bands = list_bands()
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"<div style='margin-top:16px; font-size:0.72rem; font-weight:600; "
        f"color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.08em;'>"
        f"Filters</div>",
        unsafe_allow_html=True,
    )
    selected_station = st.selectbox(
        "Police Station", ["All Stations"] + stations,
        key="an_station", label_visibility="collapsed",
    )
    selected_bands = st.multiselect(
        "Priority Band", bands, default=bands, key="an_bands",
    )
    sort_by = st.selectbox(
        "Sort By",
        ["Priority Score", "PCIS Score", "Drift Score"],
        key="an_sort",
    )

# Apply filters
station_param = None if selected_station == "All Stations" else selected_station
hotspots_df = get_hotspots(station=station_param)

if selected_bands and not hotspots_df.empty:
    hotspots_df = hotspots_df[hotspots_df["priority_band"].isin(selected_bands)]

# Sort
sort_map = {
    "Priority Score": "priority_score",
    "PCIS Score": "pcis_score",
    "Drift Score": "drift_score",
}
sort_col = sort_map.get(sort_by, "priority_score")
if sort_col in hotspots_df.columns:
    hotspots_df = hotspots_df.sort_values(sort_col, ascending=False)

# ---------------------------------------------------------------------------
# KPI Strip
# ---------------------------------------------------------------------------
if not hotspots_df.empty:
    total = len(hotspots_df)
    critical = len(hotspots_df[hotspots_df["priority_band"] == "Critical"])
    high = len(hotspots_df[hotspots_df["priority_band"] == "High"])
    avg_priority = hotspots_df["priority_score"].mean() if "priority_score" in hotspots_df.columns else 0
    avg_pcis = hotspots_df["pcis_score"].mean() if "pcis_score" in hotspots_df.columns else 0

    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.metric("Showing", total)
    with kpi_cols[1]:
        st.metric("Critical", critical)
    with kpi_cols[2]:
        st.metric("High", high)
    with kpi_cols[3]:
        st.metric("Avg Priority", f"{avg_priority:.1f}")
    with kpi_cols[4]:
        st.metric("Avg PCIS", f"{avg_pcis:.1f}")

st.markdown(f"<div style='height:8px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📋 Rankings", "📊 Score Decomposition", "🔗 Correlations"])

# ---- Tab 1: Full Rankings ----
with tab1:
    if not hotspots_df.empty:
        display_cols = [
            "rank_city", "hotspot_name", "police_station", "priority_band",
            "priority_score", "pcis_score", "drift_score", "violation_count",
        ]
        available_cols = [c for c in display_cols if c in hotspots_df.columns]
        display_df = hotspots_df[available_cols].head(50).copy()

        # Rename for display
        col_rename = {
            "rank_city": "Rank",
            "hotspot_name": "Hotspot",
            "police_station": "Station",
            "priority_band": "Band",
            "priority_score": "Priority",
            "pcis_score": "PCIS",
            "drift_score": "Drift",
            "violation_count": "Violations",
        }
        display_df = display_df.rename(columns=col_rename)

        st.dataframe(
            display_df,
            use_container_width=True,
            height=480,
            hide_index=True,
        )
        st.caption(f"Showing top {len(display_df)} of {len(hotspots_df)} hotspots")
    else:
        st.info("No hotspots match the current filters.")

# ---- Tab 2: Score Decomposition ----
with tab2:
    if not hotspots_df.empty:
        decomp_left, decomp_right = st.columns([3, 2], gap="medium")

        with decomp_left:
            # Stacked bar chart — top 15
            top15 = hotspots_df.head(15).copy()
            decomp_cols = ["pcis_score", "drift_score", "severity_norm", "repeat_offender_density_norm"]
            available_decomp = [c for c in decomp_cols if c in top15.columns]

            if available_decomp and "hotspot_name" in top15.columns:
                # Shorten names
                top15["name_short"] = top15["hotspot_name"].str[:20]
                fig = stacked_bar_chart(
                    top15, x="name_short", y_cols=available_decomp,
                    names=["PCIS", "Drift", "Severity", "RO Density"][:len(available_decomp)],
                    title="Score Decomposition — Top 15",
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True, key="decomp_stacked")

        with decomp_right:
            # Band distribution donut
            band_counts = hotspots_df["priority_band"].value_counts()
            fig = donut_chart(
                labels=band_counts.index.tolist(),
                values=band_counts.values.tolist(),
                title="Band Distribution",
                colors=[BAND_COLORS.get(b, COLORS["accent_blue"]) for b in band_counts.index],
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True, key="band_donut")

# ---- Tab 3: Correlations ----
with tab3:
    if not hotspots_df.empty:
        corr_left, corr_right = st.columns(2, gap="medium")

        with corr_left:
            if "pcis_score" in hotspots_df.columns and "drift_score" in hotspots_df.columns:
                fig = scatter_chart(
                    hotspots_df, x="pcis_score", y="drift_score",
                    color_col="priority_band",
                    color_map=BAND_COLORS,
                    title="PCIS vs Drift Score",
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True, key="pcis_drift_scatter")

        with corr_right:
            if "priority_score" in hotspots_df.columns and "violation_count" in hotspots_df.columns:
                fig = scatter_chart(
                    hotspots_df, x="violation_count", y="priority_score",
                    color_col="priority_band",
                    color_map=BAND_COLORS,
                    title="Priority Score vs Violation Count",
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True, key="priority_viol_scatter")
