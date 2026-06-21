"""
components_v2/allocation_matrix.py
==================================
Patrol allocation timeline grid for the Planning page.
Renders a zone × time-slot matrix with colored officer assignment blocks.
"""

import streamlit as st
import pandas as pd
from styles_v2.theme import COLORS


def render_allocation_matrix(routes_df, time_slots=None, title="Allocation Matrix"):
    """Render the patrol allocation matrix matching Screenshot 5.

    Parameters
    ----------
    routes_df : pd.DataFrame
        Patrol routes with: police_station, route_id, stop_order, hotspot_name,
        priority_band, priority_score.
    time_slots : list of str, optional
        Time slot labels. Defaults to hourly 08:00-12:00.
    title : str
        Section title.
    """
    if time_slots is None:
        time_slots = ["08:00", "09:00", "10:00", "11:00", "12:00"]

    # Group routes by station and create allocation blocks
    stations = routes_df["police_station"].unique()[:6]  # Limit to 6 for display

    # Build header
    header_cells = f'<th style="text-align:left;">Zone / Time</th>'
    for slot in time_slots:
        header_cells += f"<th>{slot}</th>"

    # Build rows
    rows_html = ""
    assignment_types = [
        ("Patrol", "v2-matrix-patrol"),
        ("Priority", "v2-matrix-priority"),
        ("Static", "v2-matrix-static"),
        ("Relief", "v2-matrix-relief"),
        ("Break", "v2-matrix-break"),
    ]

    for i, station in enumerate(stations):
        station_routes = routes_df[routes_df["police_station"] == station]
        route_ids = station_routes["route_id"].unique()

        # Abbreviate station name
        station_short = station.replace("Traffic PS", "").replace("PS", "").strip()
        if len(station_short) > 18:
            station_short = station_short[:18] + "…"

        cells = f"""
            <td style="text-align:left; font-weight:600; color:{COLORS['text_primary']};
                       font-size:0.78rem; padding:8px 10px;">{station_short}</td>
        """

        # Assign blocks to time slots (deterministic based on route data)
        for j, slot in enumerate(time_slots):
            if len(route_ids) == 0:
                cells += "<td></td>"
                continue

            # Determine assignment type based on position
            route_idx = j % max(len(route_ids), 1)
            route_id = route_ids[min(route_idx, len(route_ids) - 1)]

            # Check priority
            route_data = station_routes[station_routes["route_id"] == route_id]
            has_critical = (route_data["priority_band"] == "Critical").any() if "priority_band" in route_data.columns else False

            # Cycle through assignment types
            if j == len(time_slots) - 2 and i % 3 == 0:
                # Some get break
                atype, aclass = "Break", "v2-matrix-break"
            elif has_critical and j < 2:
                atype, aclass = "Priority", "v2-matrix-priority"
                label = f"OFC-{(i*3 + j + 1):02d} ({atype})"
            elif j >= len(time_slots) - 1:
                atype, aclass = "Relief", "v2-matrix-relief"
            else:
                atype, aclass = "Patrol", "v2-matrix-patrol"

            if atype == "Break":
                label = "Break"
            else:
                label = f"OFC-{(i*3 + j + 1):02d} ({atype})"

            cells += f'<td><span class="v2-matrix-cell {aclass}">{label}</span></td>'

        rows_html += f"<tr>{cells}</tr>"

    # Time navigation
    nav_html = f"""
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div class="v2-section-header" style="margin-bottom:0; border-bottom:none;">
                <span class="icon">📊</span> {title}
            </div>
            <div style="display:flex; align-items:center; gap:12px; font-size:0.78rem;
                        color:{COLORS['text_secondary']};">
                <span style="cursor:pointer;">‹</span>
                <span style="font-weight:600;">08:00 - 12:00</span>
                <span style="cursor:pointer;">›</span>
            </div>
        </div>
    """

    st.markdown(
        f"""
        {nav_html}
        <table class="v2-matrix">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )
