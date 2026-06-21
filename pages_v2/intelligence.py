"""
pages_v2/intelligence.py
=========================
Hotspot Intelligence — Screenshot 2.
Full-screen map with analytics panel and junction detail cards.
"""

import streamlit as st
import pandas as pd
from styles_v2.theme import COLORS, inject_v2_theme, BAND_COLORS
from styles_v2.components import inject_component_css
from components_v2.sidebar import render_sidebar
from components_v2.topbar import render_topbar
from components_v2.data_table import render_priority_table
from components_v2.map_renderer import create_dark_map, add_hotspot_markers, add_heatmap, render_map
from components_v2.chart_factory import bar_chart
from components_v2.action_card import render_hotspot_detail_card
from components_v2.alert_badge import status_dot

# ---------------------------------------------------------------------------
# Theme + sidebar
# ---------------------------------------------------------------------------
inject_v2_theme()
st.markdown(inject_component_css(), unsafe_allow_html=True)
render_sidebar(active_page="Intelligence")

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
render_topbar(
    module_name="Hotspot Intelligence",
    search_placeholder="Search junctions, zones...",
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    from src.data_service import get_hotspots, get_priority_hotspots, list_stations

    hotspots_df = get_hotspots()
    critical_hotspots = get_priority_hotspots(top_n=10)
    stations = list_stations()
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# 2-column layout — Map dominant
# ---------------------------------------------------------------------------
col_map, col_panel = st.columns([3, 1.5], gap="medium")

# ========================== LEFT — Map ==========================
with col_map:
    m = create_dark_map(zoom=12)
    add_hotspot_markers(
        m, hotspots_df,
        popup_cols=["priority_band", "pcis_score", "violation_count", "drift_status"],
    )
    add_heatmap(m, hotspots_df, weight_col="pcis_score")
    render_map(m, height=600, key="intel_map")

    # PCIS gradient legend below map
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:12px; padding:8px 12px;
                    background:{COLORS['surface']}; border-radius:8px; margin-top:6px;">
            <span style="font-size:0.72rem; font-weight:600; color:{COLORS['text_secondary']};
                        text-transform:uppercase; letter-spacing:0.06em;">
                Congestion Impact (PCIS)
            </span>
            <div style="flex:1; height:6px; border-radius:3px;
                        background: linear-gradient(90deg, {COLORS['low']}, {COLORS['medium']},
                        {COLORS['high']}, {COLORS['critical']});">
            </div>
            <div style="display:flex; justify-content:space-between; width:120px;">
                <span style="font-size:0.66rem; color:{COLORS['text_muted']};">Low</span>
                <span style="font-size:0.66rem; color:{COLORS['text_muted']};">Severe</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ========================== RIGHT — Analytics Panel ==========================
with col_panel:
    st.markdown(
        f"""
        <div style="font-size:0.95rem; font-weight:700; color:{COLORS['text_bright']};
                    margin-bottom:16px;">
            Hotspot Analytics
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Critical Junctions table
    table_cols = [
        {"key": "hotspot_name", "label": "Junction", "fmt": "text"},
        {"key": "violation_count", "label": "Violations", "fmt": "number", "align": "right"},
        {"key": "pcis_score", "label": "PCIS", "fmt": "score", "align": "right"},
        {"key": "priority_band", "label": "Status", "fmt": "dot", "align": "center"},
    ]
    render_priority_table(
        critical_hotspots, table_cols, max_rows=5,
        title="⚡ Critical Junctions", show_chevron=True,
    )

    # PCIS Distribution bar chart
    st.markdown(
        f"""
        <div style="margin-top:18px; margin-bottom:8px;">
            <span style="font-size:0.82rem; font-weight:700; color:{COLORS['text_secondary']};">
                📊 PCIS Distribution
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not hotspots_df.empty and "pcis_score" in hotspots_df.columns:
        # Create band distribution for chart
        band_counts = hotspots_df["priority_band"].value_counts()
        chart_df = pd.DataFrame({
            "band": band_counts.index,
            "count": band_counts.values,
        })
        fig = bar_chart(
            chart_df, x="band", y="count",
            title="", height=200,
        )
        # Color bars by band
        colors = [BAND_COLORS.get(b, COLORS["accent_blue"]) for b in chart_df["band"]]
        fig.update_traces(marker_color=colors)
        st.plotly_chart(fig, use_container_width=True, key="pcis_dist")

    # Junction detail card — top hotspot
    if not critical_hotspots.empty:
        top = critical_hotspots.iloc[0]
        name = top.get("hotspot_name", "Unknown")
        pcis = top.get("pcis_score", 0)
        violations = top.get("violation_count", 0)
        drift = top.get("drift_status", "Stable")

        # Calculate trend text
        recent = top.get("mean_weekly_recent", 0)
        prior = top.get("mean_weekly_prior", 0)
        if prior and prior > 0:
            pct_change = ((recent - prior) / prior) * 100
            trend_text = f"+{pct_change:.0f}%" if pct_change > 0 else f"{pct_change:.0f}%"
        else:
            trend_text = "N/A"

        # Normalize PCIS to ~10 scale for impact score display
        impact = pcis / 10.0 if pcis else 0

        render_hotspot_detail_card(
            name=name,
            hotspot_id=f"JNC-{hash(name) % 9999:04d}-X",
            impact_score=impact,
            trend_24h=trend_text,
            description=(
                f"Primary congestion driver identified. "
                f"Total violations: {int(violations):,}. "
                f"Drift status: {drift}."
            ),
        )
