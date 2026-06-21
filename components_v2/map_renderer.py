"""
components_v2/map_renderer.py
=============================
Map rendering components for ParkSight AI V2.
Uses Folium with dark tiles for consistency with the ops-grade dark theme.
"""

import folium
from folium.plugins import HeatMap
import streamlit as st
from streamlit_folium import st_folium
from styles_v2.theme import COLORS, BAND_COLORS
import pandas as pd


# Bengaluru center coordinates
BENGALURU_CENTER = [12.9716, 77.5946]

# Dark tile providers
DARK_TILES = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
DARK_ATTR = '&copy; <a href="https://carto.com/">CARTO</a>'


def create_dark_map(center=None, zoom=12, height=500, width=None):
    """Create a base Folium map with dark CartoDB tiles.

    Parameters
    ----------
    center : list, optional
        [lat, lon] center point. Defaults to Bengaluru.
    zoom : int
        Initial zoom level.
    height : int
        Map height in pixels.

    Returns
    -------
    folium.Map
    """
    center = center or BENGALURU_CENTER
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles=DARK_TILES,
        attr=DARK_ATTR,
        control_scale=True,
    )
    return m


def add_hotspot_markers(m, hotspots_df, color_col="priority_band", popup_cols=None):
    """Add circle markers for hotspots, colored by priority band.

    Parameters
    ----------
    m : folium.Map
        Target map.
    hotspots_df : pd.DataFrame
        Must have 'latitude', 'longitude' columns. Optionally has color_col.
    color_col : str
        Column to use for color mapping.
    popup_cols : list of str, optional
        Columns to include in popup.
    """
    for _, row in hotspots_df.iterrows():
        lat = row.get("latitude")
        lon = row.get("longitude")
        if pd.isna(lat) or pd.isna(lon):
            continue

        band = str(row.get(color_col, "Low"))
        color = BAND_COLORS.get(band, COLORS["text_muted"])
        name = row.get("hotspot_name", "Unknown")

        # Build popup
        popup_html = f"""
        <div style="font-family:Inter,sans-serif; font-size:12px; min-width:180px;
                    background:{COLORS['surface']}; color:{COLORS['text_primary']};
                    padding:10px; border-radius:6px; border:1px solid {COLORS['border']};">
            <div style="font-weight:700; font-size:13px; margin-bottom:6px;
                        color:{COLORS['text_bright']};">{name}</div>
        """
        if popup_cols:
            for col in popup_cols:
                val = row.get(col, "N/A")
                label = col.replace("_", " ").title()
                popup_html += f"""
                    <div style="display:flex; justify-content:space-between; padding:2px 0;">
                        <span style="color:{COLORS['text_muted']};">{label}:</span>
                        <span style="font-weight:500;">{val}</span>
                    </div>
                """
        popup_html += "</div>"

        folium.CircleMarker(
            location=[lat, lon],
            radius=7 if band == "Critical" else 5,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{name} ({band})",
        ).add_to(m)


def add_heatmap(m, hotspots_df, weight_col="priority_score"):
    """Add a heatmap overlay based on hotspot positions and weights."""
    data = []
    for _, row in hotspots_df.iterrows():
        lat = row.get("latitude")
        lon = row.get("longitude")
        weight = row.get(weight_col, 1)
        if pd.notna(lat) and pd.notna(lon) and pd.notna(weight):
            data.append([float(lat), float(lon), float(weight)])

    if data:
        HeatMap(
            data,
            radius=25,
            blur=15,
            max_zoom=15,
            gradient={0.2: "#22c55e", 0.4: "#eab308", 0.6: "#f97316", 0.8: "#ef4444", 1.0: "#dc2626"},
        ).add_to(m)


def add_patrol_route(m, route_df, line_color=None):
    """Add a patrol route polyline with numbered stop markers.

    Parameters
    ----------
    m : folium.Map
        Target map.
    route_df : pd.DataFrame
        Must have latitude, longitude, stop_order, hotspot_name, priority_band columns.
    line_color : str, optional
        Override color for the route line.
    """
    color = line_color or COLORS["accent_cyan"]
    coords = []

    for _, row in route_df.iterrows():
        lat = row.get("latitude")
        lon = row.get("longitude")
        if pd.isna(lat) or pd.isna(lon):
            continue

        coords.append([float(lat), float(lon)])
        stop_num = int(row.get("stop_order", 0))
        name = row.get("hotspot_name", "")
        band = str(row.get("priority_band", "Low"))
        marker_color = BAND_COLORS.get(band, COLORS["text_muted"])

        # Numbered marker
        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(
                html=f"""
                <div style="background:{marker_color}; color:white; width:22px; height:22px;
                            border-radius:50%; display:flex; align-items:center; justify-content:center;
                            font-size:10px; font-weight:700; border:2px solid white;
                            box-shadow:0 0 6px rgba(0,0,0,0.4);">
                    {stop_num}
                </div>
                """,
                icon_size=(22, 22),
                icon_anchor=(11, 11),
            ),
            tooltip=f"Stop {stop_num}: {name}",
        ).add_to(m)

    # Draw route line
    if len(coords) >= 2:
        folium.PolyLine(
            coords,
            color=color,
            weight=3,
            opacity=0.8,
            dash_array="8 6",
        ).add_to(m)


def render_map(m, height=500, key=None):
    """Render a Folium map in Streamlit.

    Parameters
    ----------
    m : folium.Map
        The map to render.
    height : int
        Display height.
    key : str, optional
        Streamlit component key.
    """
    st_folium(m, height=height, use_container_width=True, key=key, returned_objects=[])
