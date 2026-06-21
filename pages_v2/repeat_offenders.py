"""
pages_v2/repeat_offenders.py
=============================
Repeat Offender Intelligence Module — Screenshot 4.
Top offenders table, hotspot visitation map, enforcement card, activity timeline.
"""

import streamlit as st
import pandas as pd
from styles_v2.theme import COLORS, inject_v2_theme
from styles_v2.components import inject_component_css
from components_v2.sidebar import render_sidebar
from components_v2.topbar import render_topbar
from components_v2.data_table import render_offender_table
from components_v2.map_renderer import create_dark_map, add_hotspot_markers, render_map
from components_v2.chart_factory import activity_timeline_chart
from components_v2.action_card import render_enforcement_card
from components_v2.alert_badge import trend_arrow

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
    module_name="Intelligence Module",
    search_placeholder="Search Plate or VIN (e.g. KA-05...)",
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    from src.data_service import get_repeat_offenders, get_hotspots

    offenders_df = get_repeat_offenders(top_n=20)
    hotspots_df = get_hotspots()
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# 2-column layout
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1.8, 2.5], gap="medium")

# ========================== LEFT — Offender Table + Enforcement Card ==========================
with col_left:
    # Top Offenders table
    if not offenders_df.empty:
        # Header with filter icon
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between;
                        margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:0.9rem;">⚠️</span>
                    <span style="font-size:0.92rem; font-weight:700;
                                color:{COLORS['text_bright']};">Top Offenders (72h)</span>
                </div>
                <span style="color:{COLORS['text_muted']}; cursor:pointer;">🔍</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Build custom table matching screenshot
        header = f"""
        <table class="v2-table">
            <thead><tr>
                <th>Plate No.</th>
                <th style="text-align:right;">Violations</th>
                <th style="text-align:center;">Trend</th>
            </tr></thead>
            <tbody>
        """
        rows = ""
        for idx, row in offenders_df.head(6).iterrows():
            veh = row.get("vehicle_number", "")
            viols = int(row.get("total_violations", 0))
            score = row.get("offender_score", 0)

            # Determine trend based on score
            if score > 70:
                trend_html = trend_arrow("up")
            elif score > 40:
                trend_html = trend_arrow("flat")
            else:
                trend_html = trend_arrow("down")

            # Highlight top offender
            bg = f"background: rgba(239, 68, 68, 0.08);" if idx == offenders_df.index[0] else ""

            rows += f"""
                <tr style="{bg}">
                    <td style="color:{COLORS['accent_cyan']}; font-weight:600;">{veh}</td>
                    <td class="col-num" style="text-align:right; color:{COLORS['critical']}; font-weight:600;">
                        {viols}
                    </td>
                    <td style="text-align:center;">{trend_html}</td>
                </tr>
            """

        st.markdown(header + rows + "</tbody></table>", unsafe_allow_html=True)

        # Enforcement recommendation card for top offender
        top = offenders_df.iloc[0]
        render_enforcement_card(
            vehicle_number=top.get("vehicle_number", "N/A"),
            violation_count=int(top.get("total_violations", 0)),
            confidence=min(top.get("offender_score", 0) + 10, 99.5),
            primary_offense=top.get("top_violation_type", "No-Parking Zones"),
            description="",
        )
    else:
        st.info("No repeat offenders found.")

# ========================== RIGHT — Map + Activity Timeline ==========================
with col_right:
    if not offenders_df.empty:
        top = offenders_df.iloc[0]
        top_vehicle = top.get("vehicle_number", "N/A")

        # Hotspot Visitation map header
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%;
                            background:{COLORS['critical']};"></span>
                <span style="font-size:0.82rem; font-weight:600;
                            color:{COLORS['text_secondary']};">
                    Hotspot Visitation: {top_vehicle}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Parse offender's stations and show relevant hotspots
        offender_stations = str(top.get("police_stations", "")).split("|")
        offender_stations = [s.strip() for s in offender_stations if s.strip()]

        # Filter hotspots to relevant stations
        if offender_stations and not hotspots_df.empty:
            relevant = hotspots_df[
                hotspots_df["police_station"].isin(offender_stations)
            ].head(20)
        else:
            relevant = hotspots_df.head(15)

        m = create_dark_map(zoom=12)
        if not relevant.empty:
            add_hotspot_markers(
                m, relevant,
                popup_cols=["priority_band", "violation_count"],
            )
        render_map(m, height=350, key="offender_map")

        # Activity Timeline
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between;
                        margin:16px 0 8px;">
                <div style="display:flex; align-items:center; gap:6px;">
                    <span style="font-size:0.85rem;">📈</span>
                    <span style="font-size:0.85rem; font-weight:600;
                                color:{COLORS['text_primary']};">Activity Timeline</span>
                </div>
                <div class="v2-map-legend">
                    <div class="v2-legend-item">
                        <div class="v2-legend-dot" style="background:{COLORS['critical']};"></div>
                        <span>Critical</span>
                    </div>
                    <div class="v2-legend-item">
                        <div class="v2-legend-dot" style="background:{COLORS['accent_blue']};"></div>
                        <span>Standard</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Generate activity data from offender info
        total_viols = int(top.get("total_violations", 14))
        days = ["Mon", "Tue", "Wed", "Thu", "Today"]
        activity_data = []
        for i, day in enumerate(days):
            # Distribute violations across days
            base = total_viols // len(days)
            crit = max(0, base - 2) if i in [2, 4] else 0
            std = base - crit + (1 if i == 4 else 0)
            activity_data.append({"day": day, "critical": crit, "standard": max(std, 0)})

        fig = activity_timeline_chart(activity_data, title="", height=250)
        st.plotly_chart(fig, use_container_width=True, key="activity")
    else:
        st.info("No offender data available for map display.")
