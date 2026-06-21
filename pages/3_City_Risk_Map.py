"""
pages/3_City_Risk_Map.py
========================
City Risk Map — interactive Folium map of all 701 enforcement hotspots.

Features:
  - All 701 hotspots rendered as circle markers colour-coded by priority band
    Critical=Red | High=Orange | Medium=Yellow | Low=Green
  - Station filter, priority band filter, hotspot type filter
  - Rich popup: hotspot name, PCIS, priority score, violations, drift status
  - Layer groups for each priority band (toggle on/off)
  - Heatmap overlay toggle
  - Summary stats strip above the map
"""

import sys
from pathlib import Path

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import MarkerCluster, HeatMap, GroupedLayerControl
from streamlit_folium import st_folium

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_PAGE_DIR     = Path(__file__).resolve().parent
_PROJECT_ROOT = _PAGE_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data_service import get_hotspots, list_stations, list_bands

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="City Risk Map | AI Parking Intelligence",
    page_icon="🗺️",
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
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#161b22 0%,#0d1117 100%);
                                  border-right:1px solid #30363d; }
    [data-testid="stMetric"] { background:rgba(22,27,34,0.85); border:1px solid #30363d;
                                 border-radius:12px; padding:14px 16px; }
    [data-testid="stMetricLabel"] { color:#8b949e !important; font-size:0.74rem !important;
                                     font-weight:500 !important; text-transform:uppercase;
                                     letter-spacing:0.06em; }
    [data-testid="stMetricValue"] { color:#f0f6fc !important; font-size:1.6rem !important;
                                     font-weight:700 !important; }
    .section-header { font-size:1.05rem; font-weight:600; color:#58a6ff;
                       border-bottom:1px solid #30363d; padding-bottom:8px; margin:18px 0 14px; }
    #MainMenu { visibility:hidden; } footer { visibility:hidden; } header { visibility:hidden; }
    ::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-thumb { background:#30363d; border-radius:3px; }
    /* Map container */
    iframe { border-radius:12px; border:1px solid #30363d !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Band config — colours and radii
# ---------------------------------------------------------------------------
BAND_CONFIG = {
    "Critical": {"color": "#ff4444", "fill": "#ff4444", "radius": 14, "weight": 2.5},
    "High":     {"color": "#ff8c00", "fill": "#ff8c00", "radius": 11, "weight": 2.0},
    "Medium":   {"color": "#ffd700", "fill": "#ffd700", "radius":  8, "weight": 1.5},
    "Low":      {"color": "#32cd32", "fill": "#32cd32", "radius":  6, "weight": 1.0},
}

DRIFT_BADGE = {
    "Emerging":          "🔺 Emerging",
    "Cooling":           "🔻 Cooling",
    "Stable":            "〰️ Stable",
    "Low Activity":      "⬇️ Low Activity",
    "Insufficient Data": "❓ Insufficient Data",
    "Unknown":           "— Unknown",
}

# ---------------------------------------------------------------------------
# Sidebar — filters
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
    st.page_link("pages/3_City_Risk_Map.py",  label="🗺️ City Risk Map")

    st.markdown("<hr style='border:none;border-top:1px solid #30363d;margin:12px 0;'>",
                unsafe_allow_html=True)

    st.markdown("**MAP FILTERS**")

    all_stations = list_stations()
    station_opt  = st.selectbox(
        "Police Station",
        options=["All Stations"] + all_stations,
        index=0,
        key="map_station",
    )

    band_opts = st.multiselect(
        "Priority Band",
        options=list_bands(),
        default=list_bands(),
        key="map_bands",
    )

    type_opts = st.multiselect(
        "Hotspot Type",
        options=["Named Junction", "Discovered Unknown"],
        default=["Named Junction", "Discovered Unknown"],
        key="map_types",
    )

    show_heatmap = st.toggle("Show Heatmap Overlay", value=False, key="show_heat")
    show_cluster = st.toggle("Cluster Nearby Markers", value=False, key="show_cluster")

    st.markdown("<hr style='border:none;border-top:1px solid #30363d;margin:12px 0;'>",
                unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size:0.75rem;color:#8b949e;">
        <b style="color:#e6edf3;">Legend</b><br>
        <span style="color:#ff4444;">●</span> Critical<br>
        <span style="color:#ff8c00;">●</span> High<br>
        <span style="color:#ffd700;">●</span> Medium<br>
        <span style="color:#32cd32;">●</span> Low<br>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="padding:8px 0 4px;">
        <h1 style="font-size:2rem;font-weight:700;color:#f0f6fc;margin:0;">
            🗺️ City Risk Map
        </h1>
        <p style="color:#8b949e;font-size:0.92rem;margin:4px 0 0;">
            All 701 enforcement hotspots · Bengaluru BTP · Priority-band colour coding
        </p>
    </div>
    <hr style="border:none;border-top:1px solid #30363d;margin:12px 0 20px;">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load & filter data
# ---------------------------------------------------------------------------
with st.spinner("Loading hotspot data…"):
    station_filter = None if station_opt == "All Stations" else station_opt
    df_all = get_hotspots(station=station_filter)

# Apply band + type filters
if band_opts:
    df_map = df_all[df_all["priority_band"].isin(band_opts)].copy()
else:
    df_map = df_all.copy()

if type_opts:
    df_map = df_map[df_map["hotspot_type"].isin(type_opts)].copy()

df_map = df_map.dropna(subset=["latitude", "longitude"])

# ---------------------------------------------------------------------------
# Summary KPI strip
# ---------------------------------------------------------------------------
m1, m2, m3, m4, m5 = st.columns(5, gap="small")
with m1:
    st.metric("Showing Hotspots", f"{len(df_map):,}")
with m2:
    crit_n = int((df_map["priority_band"] == "Critical").sum())
    st.metric("🔴 Critical", f"{crit_n:,}")
with m3:
    high_n = int((df_map["priority_band"] == "High").sum())
    st.metric("🟠 High", f"{high_n:,}")
with m4:
    em_n = int((df_map.get("drift_status", pd.Series()) == "Emerging").sum()) if "drift_status" in df_map.columns else 0
    st.metric("🟡 Emerging", f"{em_n:,}")
with m5:
    total_v = int(df_map["violation_count"].sum()) if "violation_count" in df_map.columns else 0
    st.metric("Total Violations", f"{total_v:,}")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Build Folium map
# ---------------------------------------------------------------------------
# Centre on Bengaluru centroid of filtered data
if len(df_map) > 0:
    map_lat = float(df_map["latitude"].mean())
    map_lon = float(df_map["longitude"].mean())
else:
    map_lat, map_lon = 12.9716, 77.5946   # Bengaluru default

zoom_start = 11 if station_filter is None else 13

m = folium.Map(
    location=[map_lat, map_lon],
    zoom_start=zoom_start,
    tiles=None,
)

# Dark tile layer
folium.TileLayer(
    tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
         ' contributors &copy; <a href="https://carto.com/">CARTO</a>',
    name="Dark Map",
    max_zoom=20,
).add_to(m)

# Optional: satellite layer for context
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Tiles &copy; Esri",
    name="Satellite",
    max_zoom=20,
).add_to(m)

# Layer control groups per band
band_groups: dict = {}
for band in ["Critical", "High", "Medium", "Low"]:
    if band in band_opts:
        band_groups[band] = folium.FeatureGroup(name=f"● {band}", show=True)
        m.add_child(band_groups[band])

# Heatmap data
heat_data: list = []

# Marker cluster (optional)
cluster_group = MarkerCluster(name="Clusters", show=show_cluster)
if show_cluster:
    m.add_child(cluster_group)

# ---------------------------------------------------------------------------
# Render markers
# ---------------------------------------------------------------------------
for _, row in df_map.iterrows():
    band     = str(row.get("priority_band", "Low"))
    cfg      = BAND_CONFIG.get(band, BAND_CONFIG["Low"])
    lat      = float(row["latitude"])
    lon      = float(row["longitude"])
    name     = str(row.get("hotspot_name", "Unknown"))
    station  = str(row.get("police_station", "—"))
    priority = float(row.get("priority_score", 0.0))
    pcis     = float(row.get("pcis_score", 0.0))
    drift    = float(row.get("drift_score", 0.0)) if pd.notna(row.get("drift_score")) else 0.0
    drift_st = DRIFT_BADGE.get(str(row.get("drift_status", "Unknown")), "—")
    violations = int(row["violation_count"]) if pd.notna(row.get("violation_count")) else 0
    h_type   = str(row.get("hotspot_type", "—"))
    rank     = int(row["rank_city"]) if pd.notna(row.get("rank_city")) else "—"

    # Popup HTML
    popup_html = f"""
    <div style="font-family:Inter,sans-serif;min-width:240px;max-width:300px;
                background:#161b22;color:#e6edf3;border-radius:8px;padding:12px 14px;">
        <div style="font-size:0.7rem;text-transform:uppercase;letter-spacing:0.08em;
                    color:#58a6ff;margin-bottom:4px;">{h_type}</div>
        <div style="font-size:1rem;font-weight:700;color:#f0f6fc;
                    line-height:1.3;margin-bottom:10px;">{name}</div>
        <table style="width:100%;border-collapse:collapse;font-size:0.82rem;">
            <tr>
                <td style="color:#8b949e;padding:2px 0;">Station</td>
                <td style="color:#e6edf3;text-align:right;">{station}</td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:2px 0;">Priority Band</td>
                <td style="text-align:right;">
                    <span style="color:{cfg['color']};font-weight:700;">{band}</span>
                </td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:2px 0;">City Rank</td>
                <td style="color:#e6edf3;text-align:right;">#{rank}</td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:2px 0;">Priority Score</td>
                <td style="color:#f0f6fc;font-weight:600;text-align:right;">{priority:.2f}</td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:2px 0;">PCIS Score</td>
                <td style="color:#f0f6fc;text-align:right;">{pcis:.2f}</td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:2px 0;">Drift Score</td>
                <td style="color:#f0f6fc;text-align:right;">{drift:.1f}</td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:2px 0;">Drift Status</td>
                <td style="color:#f0f6fc;text-align:right;">{drift_st}</td>
            </tr>
            <tr>
                <td style="color:#8b949e;padding:2px 0;">Violations</td>
                <td style="color:#f0f6fc;font-weight:600;text-align:right;">{violations:,}</td>
            </tr>
        </table>
    </div>
    """

    tooltip_text = f"{name[:40]} | {band} | Score: {priority:.1f}"

    marker = folium.CircleMarker(
        location=[lat, lon],
        radius=cfg["radius"],
        color=cfg["color"],
        fill=True,
        fill_color=cfg["fill"],
        fill_opacity=0.75,
        weight=cfg["weight"],
        popup=folium.Popup(popup_html, max_width=320, parse_html=True),
        tooltip=folium.Tooltip(tooltip_text, sticky=False),
    )

    # Add to band group or cluster
    if show_cluster:
        marker.add_to(cluster_group)
    elif band in band_groups:
        marker.add_to(band_groups[band])
    else:
        marker.add_to(m)

    # Heatmap weight = priority_score
    heat_data.append([lat, lon, priority / 100.0])

# ---------------------------------------------------------------------------
# Heatmap overlay
# ---------------------------------------------------------------------------
if show_heatmap and heat_data:
    HeatMap(
        heat_data,
        name="Priority Heatmap",
        min_opacity=0.3,
        radius=20,
        blur=15,
        max_zoom=14,
        gradient={0.2: "#00ff00", 0.5: "#ffff00", 0.75: "#ff8800", 1.0: "#ff0000"},
    ).add_to(m)

# Layer control
folium.LayerControl(collapsed=False).add_to(m)

# ---------------------------------------------------------------------------
# Render map
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">ENFORCEMENT HOTSPOT MAP — BENGALURU</div>',
            unsafe_allow_html=True)

map_output = st_folium(
    m,
    width="100%",
    height=620,
    returned_objects=["last_object_clicked"],
    key="city_risk_map",
)

# ---------------------------------------------------------------------------
# Click detail panel
# ---------------------------------------------------------------------------
clicked = map_output.get("last_object_clicked") if map_output else None
if clicked:
    click_lat = clicked.get("lat")
    click_lng = clicked.get("lng")
    if click_lat and click_lng:
        dist = (
            (df_map["latitude"] - click_lat).pow(2) +
            (df_map["longitude"] - click_lng).pow(2)
        ).pow(0.5)
        if len(dist) > 0:
            nearest_idx = dist.idxmin()
            r = df_map.loc[nearest_idx]
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">SELECTED HOTSPOT DETAIL</div>',
                        unsafe_allow_html=True)
            d1, d2, d3, d4 = st.columns(4, gap="small")
            with d1:
                st.metric("Priority Score", f"{r.get('priority_score', 0):.2f}")
            with d2:
                st.metric("PCIS Score", f"{r.get('pcis_score', 0):.2f}")
            with d3:
                st.metric("Violations", f"{int(r.get('violation_count', 0)):,}" if pd.notna(r.get('violation_count')) else "—")
            with d4:
                st.metric("Priority Band", str(r.get("priority_band", "—")))

# ---------------------------------------------------------------------------
# Filtered table
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
with st.expander(f"📋 Hotspot List ({len(df_map)} shown)", expanded=False):
    table_cols = ["rank_city", "hotspot_name", "police_station", "priority_band",
                  "priority_score", "pcis_score", "drift_score", "violation_count", "drift_status"]
    available = [c for c in table_cols if c in df_map.columns]
    tbl = df_map[available].sort_values("priority_score", ascending=False).copy()
    tbl.rename(columns={
        "rank_city":      "Rank",
        "hotspot_name":   "Hotspot",
        "police_station": "Station",
        "priority_band":  "Band",
        "priority_score": "Priority",
        "pcis_score":     "PCIS",
        "drift_score":    "Drift",
        "violation_count":"Violations",
        "drift_status":   "Drift Status",
    }, inplace=True)
    if "Priority" in tbl.columns:
        tbl["Priority"] = tbl["Priority"].round(2)
    if "PCIS" in tbl.columns:
        tbl["PCIS"] = tbl["PCIS"].round(2)
    if "Drift" in tbl.columns:
        tbl["Drift"] = tbl["Drift"].round(1)

    st.dataframe(
        tbl,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank":       st.column_config.NumberColumn("Rank", width="small"),
            "Hotspot":    st.column_config.TextColumn("Hotspot", width="large"),
            "Station":    st.column_config.TextColumn("Station", width="medium"),
            "Band":       st.column_config.TextColumn("Band", width="small"),
            "Priority":   st.column_config.NumberColumn("Priority", format="%.2f"),
            "PCIS":       st.column_config.NumberColumn("PCIS", format="%.2f"),
            "Drift":      st.column_config.NumberColumn("Drift", format="%.1f"),
            "Violations": st.column_config.NumberColumn("Violations", format="%d"),
        },
    )

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.page_link("pages/1_Command_Center.py",
             label="← Back to Command Center", use_container_width=False)
