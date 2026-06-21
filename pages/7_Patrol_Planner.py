"""
pages/7_Patrol_Planner.py
=========================
Patrol Planner — route visualisation and stop-sequence planning for supervisors.

Features:
  - Station selector → Route selector (only routes for that station)
  - Folium map: polyline connecting stops in order, numbered circle markers
  - Stop sequence table with priority score, band, distance from previous stop
  - Route summary: total stops, total distance, critical/high count
  - Priority band colour coding throughout
"""

import sys
from pathlib import Path

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

_PAGE_DIR     = Path(__file__).resolve().parent
_PROJECT_ROOT = _PAGE_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data_service import get_patrol_routes, list_stations

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Patrol Planner | AI Parking Intelligence",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); color: #e6edf3; }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid #30363d;
    }
    [data-testid="stMetric"] {
        background: rgba(22,27,34,0.85);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px 18px;
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important; font-size: 0.74rem !important;
        font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.06em;
    }
    [data-testid="stMetricValue"] {
        color: #f0f6fc !important; font-size: 1.75rem !important; font-weight: 700 !important;
    }
    .section-header {
        font-size: 1.05rem; font-weight: 600; color: #58a6ff;
        border-bottom: 1px solid #30363d; padding-bottom: 8px; margin: 20px 0 14px;
    }
    .stop-card {
        background: rgba(22,27,34,0.85); border: 1px solid #30363d;
        border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
        display: flex; align-items: flex-start; gap: 12px;
    }
    iframe { border-radius: 12px; border: 1px solid #30363d !important; }
    #MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Band config
# ---------------------------------------------------------------------------
BAND_COLOR = {
    "Critical": "#ff4444", "High": "#ff8c00",
    "Medium": "#ffd700", "Low": "#32cd32",
}
BAND_FILL = {
    "Critical": "#ff4444", "High": "#ff8c00",
    "Medium": "#ffd700", "Low": "#32cd32",
}

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center;padding:12px 0 18px;">
            <div style="font-size:2rem;">🚔</div>
            <div style="font-size:1rem;font-weight:700;color:#f0f6fc;">AI Parking Intelligence</div>
            <div style="font-size:0.7rem;color:#58a6ff;letter-spacing:0.1em;
                        text-transform:uppercase;margin-top:4px;">Enforcement Planning</div>
        </div>
        <hr style="border:none;border-top:1px solid #30363d;margin:0 0 14px;">
        """,
        unsafe_allow_html=True,
    )
    st.markdown("**NAVIGATION**")
    st.page_link("app.py",                    label="🏠 Home")
    st.page_link("pages/1_Command_Center.py", label="📊 Command Center")
    st.page_link("pages/2_Action_Center.py",  label="⚡ Action Center")
    st.page_link("pages/3_City_Risk_Map.py",  label="🗺️ City Risk Map")
    st.page_link("pages/7_Patrol_Planner.py", label="🛣️ Patrol Planner")

    st.markdown(
        "<hr style='border:none;border-top:1px solid #30363d;margin:12px 0;'>",
        unsafe_allow_html=True,
    )
    st.markdown("**ROUTE SELECTION**")

    all_stations = list_stations()
    selected_station = st.selectbox(
        "Police Station",
        options=all_stations,
        index=0,
        key="pp_station",
    )

    # Load routes for this station
    station_routes_df = get_patrol_routes(station=selected_station)
    route_ids = sorted(station_routes_df["route_id"].unique().tolist())

    selected_route = st.selectbox(
        "Patrol Route",
        options=route_ids,
        index=0,
        key="pp_route",
    )

    show_all_routes = st.toggle(
        "Show all station routes on map", value=False, key="pp_all_routes"
    )

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div style="padding:8px 0 4px;">
        <h1 style="font-size:2rem;font-weight:700;color:#f0f6fc;margin:0;">
            🛣️ Patrol Planner
        </h1>
        <p style="color:#8b949e;font-size:0.92rem;margin:4px 0 0;">
            Route visualisation and stop sequencing · {selected_station}
        </p>
    </div>
    <hr style="border:none;border-top:1px solid #30363d;margin:12px 0 20px;">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load route data
# ---------------------------------------------------------------------------
route_df = station_routes_df[station_routes_df["route_id"] == selected_route].copy()
route_df = route_df.sort_values("stop_order").reset_index(drop=True)

all_station_routes = station_routes_df.copy() if show_all_routes else route_df.copy()

# ---------------------------------------------------------------------------
# Route summary KPIs
# ---------------------------------------------------------------------------
total_stops = len(route_df)
total_dist  = float(route_df["distance_from_prev_km"].sum())
crit_stops  = int((route_df["priority_band"] == "Critical").sum())
high_stops  = int((route_df["priority_band"] == "High").sum())
top_score   = float(route_df["priority_score"].max()) if total_stops > 0 else 0.0

k1, k2, k3, k4, k5 = st.columns(5, gap="small")
with k1:
    st.metric("Total Stops", total_stops)
with k2:
    st.metric("Total Distance", f"{total_dist:.2f} km")
with k3:
    st.metric("🔴 Critical Stops", crit_stops)
with k4:
    st.metric("🟠 High Stops", high_stops)
with k5:
    st.metric("Peak Priority Score", f"{top_score:.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Build Folium map
# ---------------------------------------------------------------------------
st.markdown(
    f'<div class="section-header">ROUTE MAP — {selected_route}</div>',
    unsafe_allow_html=True,
)

map_df = all_station_routes.dropna(subset=["latitude", "longitude"])

if len(map_df) == 0:
    st.warning("No coordinate data available for this route.")
else:
    map_lat = float(map_df["latitude"].mean())
    map_lon = float(map_df["longitude"].mean())

    m = folium.Map(location=[map_lat, map_lon], zoom_start=14, tiles=None)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="© OpenStreetMap contributors © CARTO",
        name="Dark",
        max_zoom=20,
    ).add_to(m)

    # ---------- Draw selected route polyline ----------
    route_coords = list(zip(route_df["latitude"], route_df["longitude"]))
    if len(route_coords) > 1:
        folium.PolyLine(
            locations=route_coords,
            color="#58a6ff",
            weight=3.5,
            opacity=0.85,
            tooltip=f"Route: {selected_route}",
            dash_array=None,
        ).add_to(m)

    # ---------- Draw all-routes polylines (greyed) ----------
    if show_all_routes:
        for rid in route_ids:
            if rid == selected_route:
                continue
            other_df = station_routes_df[station_routes_df["route_id"] == rid].sort_values("stop_order")
            other_coords = list(zip(other_df["latitude"], other_df["longitude"]))
            if len(other_coords) > 1:
                folium.PolyLine(
                    locations=other_coords,
                    color="#30363d",
                    weight=2,
                    opacity=0.5,
                    tooltip=rid,
                ).add_to(m)

    # ---------- Stop markers ----------
    for _, row in route_df.iterrows():
        lat     = float(row["latitude"])
        lon     = float(row["longitude"])
        stop_n  = int(row["stop_order"])
        band    = str(row.get("priority_band", "Low"))
        score   = float(row.get("priority_score", 0) or 0)
        name    = str(row.get("hotspot_name", ""))
        dist_km = float(row.get("distance_from_prev_km", 0) or 0)
        color   = BAND_COLOR.get(band, "#58a6ff")

        popup_html = f"""
        <div style="font-family:Inter,sans-serif;min-width:200px;
                    background:#161b22;color:#e6edf3;border-radius:8px;padding:12px;">
            <div style="font-size:0.7rem;color:#58a6ff;text-transform:uppercase;
                        letter-spacing:0.08em;margin-bottom:4px;">Stop #{stop_n}</div>
            <div style="font-size:0.92rem;font-weight:700;color:#f0f6fc;
                        margin-bottom:8px;line-height:1.3;">{name}</div>
            <table style="width:100%;font-size:0.78rem;border-collapse:collapse;">
                <tr>
                    <td style="color:#8b949e;padding:2px 0;">Priority Band</td>
                    <td style="color:{color};font-weight:700;text-align:right;">{band}</td>
                </tr>
                <tr>
                    <td style="color:#8b949e;padding:2px 0;">Priority Score</td>
                    <td style="color:#f0f6fc;font-weight:600;text-align:right;">{score:.2f}</td>
                </tr>
                <tr>
                    <td style="color:#8b949e;padding:2px 0;">Dist from prev</td>
                    <td style="color:#f0f6fc;text-align:right;">{dist_km:.3f} km</td>
                </tr>
            </table>
        </div>
        """

        # Stop number circle
        folium.CircleMarker(
            location=[lat, lon],
            radius=14,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.25,
            weight=2.5,
            popup=folium.Popup(popup_html, max_width=250, parse_html=True),
            tooltip=folium.Tooltip(f"#{stop_n} {name[:30]} [{band}]", sticky=False),
        ).add_to(m)

        # Numbered label
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f"""<div style="
                    width:22px;height:22px;
                    background:{color};
                    border:2px solid #0d1117;
                    border-radius:50%;
                    display:flex;align-items:center;justify-content:center;
                    font-family:Inter,sans-serif;font-size:11px;
                    font-weight:700;color:#0d1117;
                    margin-top:-11px;margin-left:-11px;">
                    {stop_n}
                </div>""",
                icon_size=(22, 22),
                icon_anchor=(11, 11),
            ),
        ).add_to(m)

    # Start marker
    if len(route_df) > 0:
        start = route_df.iloc[0]
        folium.Marker(
            location=[float(start["latitude"]), float(start["longitude"])],
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
            tooltip="START",
        ).add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)

    map_col, detail_col = st.columns([3, 2], gap="large")

    with map_col:
        st_folium(
            m,
            width="100%",
            height=520,
            returned_objects=[],
            key="patrol_map",
        )

    with detail_col:
        st.markdown(
            '<div class="section-header" style="margin-top:0;">STOP SEQUENCE</div>',
            unsafe_allow_html=True,
        )

        for _, row in route_df.iterrows():
            stop_n  = int(row["stop_order"])
            band    = str(row.get("priority_band", "Low"))
            score   = float(row.get("priority_score", 0) or 0)
            name    = str(row.get("hotspot_name", ""))
            dist_km = float(row.get("distance_from_prev_km", 0) or 0)
            color   = BAND_COLOR.get(band, "#58a6ff")

            dist_str = (
                f"Start point" if stop_n == 1
                else f"+{dist_km:.3f} km from prev"
            )

            st.markdown(
                f"""
                <div style="background:rgba(22,27,34,0.85);border:1px solid #21262d;
                            border-left:3px solid {color};border-radius:8px;
                            padding:10px 14px;margin-bottom:7px;
                            display:flex;gap:12px;align-items:flex-start;">
                    <div style="min-width:28px;height:28px;background:{color};
                                border-radius:50%;display:flex;align-items:center;
                                justify-content:center;font-size:11px;
                                font-weight:700;color:#0d1117;flex-shrink:0;">
                        {stop_n}
                    </div>
                    <div style="flex:1;min-width:0;">
                        <div style="font-size:0.82rem;font-weight:600;color:#f0f6fc;
                                    line-height:1.3;margin-bottom:3px;
                                    overflow:hidden;text-overflow:ellipsis;
                                    white-space:nowrap;">{name}</div>
                        <div style="display:flex;gap:10px;font-size:0.74rem;flex-wrap:wrap;">
                            <span style="color:{color};font-weight:600;">{band}</span>
                            <span style="color:#8b949e;">Score: {score:.2f}</span>
                            <span style="color:#444d56;">{dist_str}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------------------------------------------------------------------------
# Priority distribution for this route (bar chart)
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<div class="section-header">ROUTE PRIORITY PROFILE</div>',
    unsafe_allow_html=True,
)

chart_left, chart_right = st.columns([2, 3], gap="large")

with chart_left:
    band_counts = route_df["priority_band"].value_counts()
    band_order  = ["Critical", "High", "Medium", "Low"]
    band_clrs   = ["#ff4444", "#ff8c00", "#ffd700", "#32cd32"]
    bvals = [int(band_counts.get(b, 0)) for b in band_order]

    fig_donut = go.Figure(go.Pie(
        labels=band_order,
        values=bvals,
        hole=0.55,
        marker=dict(colors=band_clrs, line=dict(color="#0d1117", width=2)),
        textinfo="label+value",
        textfont=dict(size=12, color="#f0f6fc"),
        hovertemplate="<b>%{label}</b><br>%{value} stops<extra></extra>",
    ))
    fig_donut.add_annotation(
        text=f"<b>{total_stops}</b><br><span style='font-size:9px'>stops</span>",
        x=0.5, y=0.5,
        font=dict(size=15, color="#f0f6fc", family="Inter"),
        showarrow=False,
    )
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8b949e"),
        height=260, margin=dict(l=0, r=0, t=8, b=8),
        showlegend=False,
        title=dict(text="Stops by Priority Band", font=dict(size=12, color="#8b949e")),
        hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

with chart_right:
    if len(route_df) > 0:
        stop_labels = [f"#{int(r['stop_order'])} {str(r['hotspot_name'])[:20]}"
                       for _, r in route_df.iterrows()]
        stop_scores = [float(r.get("priority_score", 0) or 0) for _, r in route_df.iterrows()]
        stop_colors = [BAND_COLOR.get(str(r.get("priority_band", "Low")), "#58a6ff")
                       for _, r in route_df.iterrows()]

        fig_bar = go.Figure(go.Bar(
            x=list(range(1, len(stop_labels) + 1)),
            y=stop_scores,
            marker=dict(
                color=stop_colors,
                line=dict(color="rgba(0,0,0,0.3)", width=1),
            ),
            text=[f"{s:.1f}" for s in stop_scores],
            textposition="outside",
            textfont=dict(size=10, color="#8b949e"),
            hovertemplate=(
                "<b>%{customdata}</b><br>"
                "Priority Score: %{y:.2f}<extra></extra>"
            ),
            customdata=stop_labels,
        ))
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,17,23,0.6)",
            font=dict(family="Inter", color="#8b949e"),
            xaxis=dict(
                title="Stop Order",
                gridcolor="#21262d",
                tickmode="linear",
                dtick=1,
                tickfont=dict(size=10),
            ),
            yaxis=dict(
                title="Priority Score",
                gridcolor="#21262d",
                range=[0, max(stop_scores) * 1.2 if stop_scores else 1],
            ),
            height=260,
            margin=dict(l=0, r=0, t=8, b=40),
            hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
            title=dict(text="Priority Score by Stop", font=dict(size=12, color="#8b949e")),
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# All routes for station (expandable table)
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
with st.expander(f"📋 All Routes — {selected_station} ({len(route_ids)} routes)", expanded=False):
    tbl = station_routes_df.copy()
    tbl = tbl.sort_values(["route_id", "stop_order"]).reset_index(drop=True)
    cols_show = [c for c in ["route_id", "stop_order", "hotspot_name", "priority_band",
                              "priority_score", "distance_from_prev_km"] if c in tbl.columns]
    tbl = tbl[cols_show].copy()
    tbl.rename(columns={
        "route_id": "Route", "stop_order": "Stop",
        "hotspot_name": "Hotspot", "priority_band": "Band",
        "priority_score": "Priority", "distance_from_prev_km": "Dist (km)",
    }, inplace=True)
    if "Priority" in tbl.columns:
        tbl["Priority"] = tbl["Priority"].round(2)
    if "Dist (km)" in tbl.columns:
        tbl["Dist (km)"] = tbl["Dist (km)"].round(3)
    st.dataframe(
        tbl, use_container_width=True, hide_index=True,
        column_config={
            "Route":    st.column_config.TextColumn("Route", width="medium"),
            "Stop":     st.column_config.NumberColumn("Stop", width="small"),
            "Hotspot":  st.column_config.TextColumn("Hotspot", width="large"),
            "Band":     st.column_config.TextColumn("Band", width="small"),
            "Priority": st.column_config.NumberColumn("Priority", format="%.2f"),
            "Dist (km)":st.column_config.NumberColumn("Dist (km)", format="%.3f"),
        },
    )

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
nav1, nav2 = st.columns(2, gap="medium")
with nav1:
    st.page_link("pages/2_Action_Center.py",
                 label="← Action Center", use_container_width=True)
with nav2:
    st.page_link("pages/8_ROI_Simulator.py",
                 label="📈 ROI Simulator →", use_container_width=True)
