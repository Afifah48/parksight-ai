"""
components_v2/data_table.py
===========================
Styled HTML data-table renderers for ParkSight AI V2.
Produces dark-themed tables with color-coded cells and hover effects.
"""

import streamlit as st
import pandas as pd
from styles_v2.theme import COLORS, BAND_COLORS, FONT_MONO
from components_v2.alert_badge import priority_badge, trend_arrow, status_dot


def render_priority_table(df, columns_config, max_rows=10, title=None, show_chevron=False):
    """Render a styled HTML table with priority-aware formatting.

    Parameters
    ----------
    df : pd.DataFrame
        Source data.
    columns_config : list of dict
        Each dict has: key (column name), label (header text),
        fmt (optional: 'badge', 'number', 'trend', 'dot', 'text'), align ('left'/'right'/'center').
    max_rows : int
        Maximum rows to display.
    title : str, optional
        Table title/header.
    show_chevron : bool
        Show expand chevron after title.
    """
    title_html = ""
    if title:
        chevron = " ∨" if show_chevron else ""
        title_html = f"""
            <div class="v2-section-header">
                <span>{title}</span>{chevron}
            </div>
        """

    # Build header
    header_cells = ""
    for col in columns_config:
        align = col.get("align", "left")
        header_cells += f'<th style="text-align:{align};">{col["label"]}</th>'

    # Build rows
    rows_html = ""
    for _, row in df.head(max_rows).iterrows():
        cells = ""
        for col in columns_config:
            key = col["key"]
            fmt = col.get("fmt", "text")
            align = col.get("align", "left")
            val = row.get(key, "")

            if fmt == "badge" and pd.notna(val):
                cell_content = priority_badge(str(val))
            elif fmt == "number":
                try:
                    num = float(val)
                    if num == int(num):
                        cell_content = f'<span class="col-num" style="color:{COLORS["accent_cyan"]};">{int(num):,}</span>'
                    else:
                        cell_content = f'<span class="col-num" style="color:{COLORS["accent_cyan"]};">{num:.1f}</span>'
                except (ValueError, TypeError):
                    cell_content = str(val)
            elif fmt == "score":
                try:
                    num = float(val)
                    # Color-code scores
                    if num >= 80:
                        color = COLORS["critical"]
                    elif num >= 60:
                        color = COLORS["high"]
                    elif num >= 40:
                        color = COLORS["medium"]
                    else:
                        color = COLORS["low"]
                    cell_content = f'<span class="col-num" style="color:{color}; font-weight:600;">{num:.1f}</span>'
                except (ValueError, TypeError):
                    cell_content = str(val)
            elif fmt == "trend":
                direction = str(val).lower() if pd.notna(val) else "flat"
                if "emerg" in direction or "accel" in direction:
                    cell_content = trend_arrow("up")
                elif "cool" in direction or "decel" in direction:
                    cell_content = trend_arrow("down")
                else:
                    cell_content = trend_arrow("flat")
            elif fmt == "dot":
                band = str(val).lower() if pd.notna(val) else "low"
                cell_content = status_dot(band)
            else:
                cell_content = str(val) if pd.notna(val) else ""

            cells += f'<td style="text-align:{align};">{cell_content}</td>'

        rows_html += f"<tr>{cells}</tr>"

    st.markdown(
        f"""
        {title_html}
        <table class="v2-table">
            <thead><tr>{header_cells}</tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


def render_ranking_table(df, title="Emerging Hotspot Rankings", max_rows=8):
    """Render the emerging hotspot ranking table matching Screenshot 3."""
    columns = [
        {"key": "hotspot_name", "label": "Location ID", "fmt": "text"},
        {"key": "police_station", "label": "Zone", "fmt": "text"},
        {"key": "drift_score", "label": "Risk Score", "fmt": "score", "align": "right"},
        {"key": "drift_status", "label": "Drift", "fmt": "trend", "align": "center"},
        {"key": "total_violations", "label": "Volume", "fmt": "number", "align": "right"},
    ]
    render_priority_table(df, columns, max_rows=max_rows, title=title)


def render_offender_table(df, title="Top Offenders (72h)", max_rows=6):
    """Render the repeat offender table matching Screenshot 4."""
    columns = [
        {"key": "vehicle_number", "label": "Plate No.", "fmt": "text"},
        {"key": "total_violations", "label": "Violations", "fmt": "number", "align": "right"},
        {"key": "offender_score", "label": "Trend", "fmt": "trend", "align": "center"},
    ]
    render_priority_table(df, columns, max_rows=max_rows, title=title)
