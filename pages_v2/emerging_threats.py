"""
pages_v2/emerging_threats.py
============================
Emerging Threat Center — Screenshot 3.
Active hotspot alerts, ranking table, risk acceleration chart.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from styles_v2.theme import COLORS, inject_v2_theme
from styles_v2.components import inject_component_css
from components_v2.sidebar import render_sidebar
from components_v2.topbar import render_topbar
from components_v2.data_table import render_ranking_table
from components_v2.chart_factory import risk_acceleration_chart
from components_v2.action_card import render_action_card, render_station_status_card
from components_v2.alert_badge import count_badge

# ---------------------------------------------------------------------------
# Theme + sidebar
# ---------------------------------------------------------------------------
inject_v2_theme()
st.markdown(inject_component_css(), unsafe_allow_html=True)
render_sidebar(active_page="Intelligence")

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
render_topbar(search_placeholder="Search operational entities...")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    from src.data_service import get_emerging_hotspots, get_station_summary
    from src.recommendation_engine import generate_recommendations

    emerging_df = get_emerging_hotspots(status="Emerging")
    all_emerging = pd.concat([
        get_emerging_hotspots(status="Emerging"),
        get_emerging_hotspots(status="Cooling"),
        get_emerging_hotspots(status="Stable"),
    ], ignore_index=True)
    station_summary = get_station_summary()
    recommendations = generate_recommendations()
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# Page header with countdown
# ---------------------------------------------------------------------------
header_left, header_right = st.columns([3, 1])

with header_left:
    st.markdown(
        f"""
        <div>
            <h1 style="font-size:1.8rem; font-weight:700; color:{COLORS['text_bright']};
                       margin:0 0 4px 0;">
                Emerging Threat Center
            </h1>
            <p style="font-size:0.85rem; color:{COLORS['text_secondary']}; margin:0;">
                Real-time identification of accelerating congestion risks.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_right:
    st.markdown(
        f"""
        <div class="v2-countdown">
            <div class="v2-countdown-label">T-Minus</div>
            <div class="v2-countdown-value">00:14:22</div>
            <div class="v2-countdown-sub">to next cycle</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(f"<hr style='border:none; border-top:1px solid {COLORS['border']}; margin:12px 0 18px;'>",
            unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 3-column layout
# ---------------------------------------------------------------------------
col_left, col_center, col_right = st.columns([1.3, 2, 1.5], gap="medium")

# ========================== LEFT — Active Hotspots ==========================
with col_left:
    emerging_count = len(emerging_df) if not emerging_df.empty else 0
    new_count = min(emerging_count, 4)

    st.markdown(
        f"""
        <div class="v2-section-header">
            <span class="icon">⚠️</span>
            <span>Active Hotspots</span>
            {count_badge(new_count, "NEW")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Alert cards from emerging data
    now = datetime.now()
    alert_templates = [
        {
            "type": "CRITICAL DENSITY",
            "css": "critical",
            "time": f"{now.hour}:{now.minute:02d} AM",
        },
        {
            "type": "FORMING QUEUE",
            "css": "high",
            "time": f"{now.hour}:{(now.minute - 2) % 60:02d} AM",
        },
        {
            "type": "SENSOR ANOMALY",
            "css": "elevated",
            "time": f"{now.hour - 1}:{now.minute:02d} AM",
        },
    ]

    for i, tmpl in enumerate(alert_templates):
        if i < len(emerging_df):
            row = emerging_df.iloc[i]
            name = row.get("hotspot_name", "Unknown Location")
            drift = row.get("drift_score", 0)
        else:
            name = "Unknown Location"
            drift = 0

        descs = [
            f"Velocity dropped {drift:.0f}% in last 10m.",
            f"Abnormal volume spike detected. Drift: {drift:.1f}",
            "Camera feed obstructed.",
        ]

        st.markdown(
            f"""
            <div class="v2-alert-card {tmpl['css']}">
                <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                    <span style="font-size:0.66rem; font-weight:700; color:{COLORS[tmpl['css']]};
                                text-transform:uppercase; letter-spacing:0.06em;">
                        {tmpl['type']}
                    </span>
                    <span class="v2-alert-time">{tmpl['time']}</span>
                </div>
                <div class="v2-alert-title" style="margin-top:4px;">{name}</div>
                <div class="v2-alert-text">{descs[i]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ========================== CENTER — Rankings Table ==========================
with col_center:
    if not emerging_df.empty:
        # Add volume column if missing
        display_df = emerging_df.copy()
        if "total_violations" not in display_df.columns:
            display_df["total_violations"] = 0
        if "drift_status" not in display_df.columns:
            display_df["drift_status"] = "Emerging"

        render_ranking_table(display_df, title="Emerging Hotspot Rankings", max_rows=8)
    else:
        st.info("No emerging hotspots detected in the current cycle.")

    # Station status cards below
    st.markdown(f"<div style='height:18px;'></div>", unsafe_allow_html=True)

    if not station_summary.empty:
        top_stations = station_summary.head(2)
        s_col1, s_col2 = st.columns(2)

        with s_col1:
            s1 = top_stations.iloc[0]
            render_station_status_card(
                station_name=s1["police_station"].replace("Traffic PS", "").strip(),
                status="Critical Load" if s1.get("critical_count", 0) > 3 else "Elevated",
                active_units=int(s1.get("critical_count", 0) + s1.get("high_count", 0)),
                total_units=int(s1.get("total_hotspots", 10)),
            )

        if len(top_stations) > 1:
            with s_col2:
                s2 = top_stations.iloc[1]
                render_station_status_card(
                    station_name=s2["police_station"].replace("Traffic PS", "").strip(),
                    status="Elevated" if s2.get("critical_count", 0) > 1 else "Normal",
                    active_units=int(s2.get("critical_count", 0) + s2.get("high_count", 0)),
                    total_units=int(s2.get("total_hotspots", 10)),
                )

# ========================== RIGHT — Risk Acceleration ==========================
with col_right:
    if not emerging_df.empty:
        fig = risk_acceleration_chart(emerging_df, height=380)
        st.plotly_chart(fig, use_container_width=True, key="risk_accel")

    # Global Drift Coefficient
    avg_drift = emerging_df["drift_score"].mean() if not emerging_df.empty else 0
    st.markdown(
        f"""
        <div style="background:{COLORS['surface']}; border:1px solid {COLORS['border']};
                    border-radius:8px; padding:12px; margin-top:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.76rem; font-weight:600; color:{COLORS['critical']};">
                    Global Drift Coefficient
                </span>
                <span style="font-size:1.1rem; font-weight:700; color:{COLORS['critical']};">
                    +{avg_drift:.1f}σ
                </span>
            </div>
            <div class="v2-progress" style="margin-top:8px;">
                <div class="v2-progress-fill" style="width:{min(avg_drift * 10, 100):.0f}%;
                            background:{COLORS['critical']};"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Recommended Actions
# ---------------------------------------------------------------------------
st.markdown(f"<div style='height:18px;'></div>", unsafe_allow_html=True)

top_actions = recommendations.get("top_actions", [])
if top_actions:
    st.markdown(
        f"""
        <div class="v2-section-header">
            <span class="icon">⚡</span>
            <span>Recommended Actions</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    act_cols = st.columns(min(len(top_actions), 3))
    for i, action in enumerate(top_actions[:3]):
        with act_cols[i]:
            render_action_card(
                title=action.get("hotspot_name", ""),
                description=action.get("reason", ""),
                priority_band=action.get("priority_band", "High"),
                action_type=action.get("action_type", ""),
            )
