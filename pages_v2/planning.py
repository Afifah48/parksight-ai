"""
pages_v2/planning.py
====================
Patrol Planner — Screenshot 5.
Deployment stats, route map, allocation matrix.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from styles_v2.theme import COLORS, inject_v2_theme, BAND_COLORS
from styles_v2.components import inject_component_css
from components_v2.sidebar import render_sidebar
from components_v2.topbar import render_topbar
from components_v2.kpi_card import render_stat_pair
from components_v2.map_renderer import create_dark_map, add_patrol_route, render_map
from components_v2.alert_badge import priority_badge
from components_v2.allocation_matrix import render_allocation_matrix

# ---------------------------------------------------------------------------
# Theme + sidebar
# ---------------------------------------------------------------------------
inject_v2_theme()
st.markdown(inject_component_css(), unsafe_allow_html=True)
render_sidebar(active_page="Planning")

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
render_topbar(module_name="Patrol Planner")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    from src.data_service import get_patrol_routes, list_stations

    stations = list_stations()
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar — Station & Route selector
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"<div style='margin-top:16px; font-size:0.72rem; font-weight:600; "
        f"color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.08em;'>"
        f"Patrol Configuration</div>",
        unsafe_allow_html=True,
    )
    selected_station = st.selectbox(
        "Police Station", stations, key="pp_station",
        label_visibility="collapsed",
    )

routes_df = get_patrol_routes(station=selected_station)
route_ids = routes_df["route_id"].unique().tolist() if not routes_df.empty else []

with st.sidebar:
    selected_route = st.selectbox(
        "Patrol Route", route_ids, key="pp_route",
        label_visibility="collapsed",
    ) if route_ids else None

# Filter to selected route
if selected_route and not routes_df.empty:
    route_data = routes_df[routes_df["route_id"] == selected_route].copy()
else:
    route_data = routes_df.head(10).copy() if not routes_df.empty else pd.DataFrame()

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
hdr_left, hdr_right = st.columns([3, 1.5])

with hdr_left:
    now = datetime.now()
    st.markdown(
        f"""
        <div>
            <h1 style="font-size:1.6rem; font-weight:700; color:{COLORS['text_bright']};
                       margin:0 0 4px 0;">
                Shift Alpha Deployment
            </h1>
            <p style="font-size:0.82rem; color:{COLORS['text_secondary']}; margin:0;">
                ⏱ 08:00 - 16:00 IST | {now.strftime('%d %b %Y')}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with hdr_right:
    btn_cols = st.columns(2)
    with btn_cols[0]:
        st.markdown(
            f"<div class='v2-btn v2-btn-ghost' style='text-align:center;'>Export Plan</div>",
            unsafe_allow_html=True,
        )
    with btn_cols[1]:
        st.markdown(
            f"<div class='v2-btn v2-btn-primary' style='text-align:center;'>Execute Deployment</div>",
            unsafe_allow_html=True,
        )

st.markdown(f"<hr style='border:none; border-top:1px solid {COLORS['border']}; margin:12px 0 18px;'>",
            unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 2-column layout
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([1.5, 3], gap="medium")

# ========================== LEFT — Stats, Parameters, Routes ==========================
with col_left:
    # DEPLOYMENT STATS
    st.markdown(
        f"""
        <div class="v2-section-header">
            <span class="icon">🚔</span>
            <span>Deployment Stats</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_stops = len(route_data)
    total_distance = route_data["distance_from_prev_km"].sum() if "distance_from_prev_km" in route_data.columns else 0
    critical_stops = len(route_data[route_data["priority_band"] == "Critical"]) if "priority_band" in route_data.columns else 0
    high_stops = len(route_data[route_data["priority_band"] == "High"]) if "priority_band" in route_data.columns else 0

    render_stat_pair("Active Officers", f"{len(route_ids)}/{len(route_ids) + 8}",
                     "Zone Coverage", "84%")
    render_stat_pair("High Priority", f"{critical_stops + high_stops} Routes",
                     "Est. Response", "< 4m")

    st.markdown(f"<div style='height:14px;'></div>", unsafe_allow_html=True)

    # PARAMETERS
    st.markdown(
        f"""
        <div class="v2-section-header">
            <span class="icon">⚙️</span>
            <span>Parameters</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div style='font-size:0.72rem; color:{COLORS['text_muted']}; font-style:italic; margin-bottom:4px;'>"
        f"Optimization Goal</div>",
        unsafe_allow_html=True,
    )
    st.selectbox(
        "Optimization Goal",
        ["Max Coverage", "Min Response Time", "Priority Focus"],
        key="opt_goal", label_visibility="collapsed",
    )

    cw = st.slider(
        "Congestion Weight",
        0.0, 1.0, 0.8, 0.1, key="cong_weight",
        help="Higher weight prioritizes congestion-impacting hotspots",
    )
    st.markdown(
        f"<div style='text-align:right; font-size:0.7rem; color:{COLORS['text_secondary']}; margin-top:-8px;'>"
        f"High ({cw})</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="v2-btn v2-btn-primary" style="text-align:center; width:100%; margin-top:8px;">
            ✨ Auto-Optimize Allocations
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"<div style='height:14px;'></div>", unsafe_allow_html=True)

    # ACTIVE ROUTES
    st.markdown(
        f"""
        <div class="v2-section-header">
            <span class="icon">🗺️</span>
            <span>Active Routes</span>
            <span style="color:{COLORS['text_muted']}; cursor:pointer; margin-left:auto;">🔍</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    mock_officers = ["Off. K. Sharma", "Off. M. Reddy", "Off. P. Singh",
                     "Off. R. Kumar", "Off. S. Nair"]

    for i, rid in enumerate(route_ids[:4]):
        r_data = routes_df[routes_df["route_id"] == rid]
        max_priority = r_data["priority_score"].max() if "priority_score" in r_data.columns else 0
        n_stops = len(r_data)
        is_high = max_priority > 60
        badge = priority_badge("High" if is_high else "Normal")
        officer = mock_officers[i % len(mock_officers)]
        eta = f"{4 + i * 3}m"

        # Abbreviate station
        station_short = selected_station.replace("Traffic PS", "").strip()

        st.markdown(
            f"""
            <div class="v2-panel" style="padding:12px 14px;">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <div>
                        <div style="font-size:0.82rem; font-weight:600;
                                    color:{COLORS['text_primary']};">
                            Sector — {station_short[:15]}
                        </div>
                        <div style="font-size:0.7rem; color:{COLORS['text_muted']}; margin-top:2px;">
                            {rid}
                        </div>
                    </div>
                    {badge}
                </div>
                <div style="display:flex; align-items:center; gap:6px; margin-top:8px;
                            font-size:0.72rem; color:{COLORS['text_secondary']};">
                    <span>👤</span> {officer}
                    <span style="margin-left:auto;">ETA: {eta}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ========================== RIGHT — Map + Allocation Matrix ==========================
with col_right:
    # Route map
    m = create_dark_map(zoom=12)
    if not route_data.empty:
        add_patrol_route(m, route_data)
    render_map(m, height=420, key="patrol_map")

    # Map legend
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:space-between;
                    padding:6px 0; margin-top:4px;">
            <span style="font-size:0.7rem; color:{COLORS['text_muted']};">
                Map Data: BTP Urban Sensors
            </span>
            <div class="v2-map-legend">
                <div class="v2-legend-item">
                    <div class="v2-legend-dot" style="background:{COLORS['accent_blue']};"></div>
                    <span>Standard Route</span>
                </div>
                <div class="v2-legend-item">
                    <div class="v2-legend-dot" style="background:{COLORS['critical']};"></div>
                    <span>Priority Action</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"<div style='height:14px;'></div>", unsafe_allow_html=True)

    # Allocation Matrix
    if not routes_df.empty:
        render_allocation_matrix(routes_df)
