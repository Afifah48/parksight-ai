"""
pages_v2/simulator.py
=====================
ROI Simulator — Interactive what-if analysis.
"""

import streamlit as st
import pandas as pd
from styles_v2.theme import COLORS, inject_v2_theme
from styles_v2.components import inject_component_css
from components_v2.sidebar import render_sidebar
from components_v2.topbar import render_topbar
from components_v2.chart_factory import waterfall_chart, grouped_bar_chart, scatter_chart

# ---------------------------------------------------------------------------
# Theme + sidebar
# ---------------------------------------------------------------------------
inject_v2_theme()
st.markdown(inject_component_css(), unsafe_allow_html=True)
render_sidebar(active_page="Simulator")

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
render_topbar(module_name="ROI Simulator")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    from src.data_service import get_roi_data

    roi_df = get_roi_data()
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar — Interactive controls
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"<div style='margin-top:16px; font-size:0.72rem; font-weight:600; "
        f"color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.08em;'>"
        f"Simulation Parameters</div>",
        unsafe_allow_html=True,
    )

    officers = st.slider(
        "Additional Officers", 2, 20, 5, key="roi_officers",
    )

    intensity_options = ["0.5×", "0.7×", "0.8×", "1.0×"]
    intensity = st.select_slider(
        "Enforcement Intensity", options=intensity_options,
        value="0.8×", key="roi_intensity",
    )
    intensity_val = float(intensity.replace("×", ""))

# ---------------------------------------------------------------------------
# Match to closest scenario
# ---------------------------------------------------------------------------
BASELINE_PCIS = 52.79

if not roi_df.empty:
    # Find closest scenario by officers and intensity
    roi_df["_officer_dist"] = (roi_df["additional_officers"] - officers).abs()
    roi_df["_intensity_dist"] = (roi_df["enforcement_intensity"] - intensity_val).abs()
    roi_df["_total_dist"] = roi_df["_officer_dist"] + roi_df["_intensity_dist"] * 10
    matched = roi_df.sort_values("_total_dist").iloc[0]

    pcis_red = matched.get("projected_pcis_reduction", 0)
    hotspots_improved = int(matched.get("projected_hotspot_reduction_count", 0))
    ro_contacts = int(matched.get("estimated_repeat_offender_reduction", 0))
    hotspots_targeted = int(matched.get("hotspots_targeted", 0))
    patrol_visits = int(matched.get("patrol_visits_added_per_month", 0))

    # Clean up temp columns
    roi_df = roi_df.drop(columns=["_officer_dist", "_intensity_dist", "_total_dist"])
else:
    pcis_red = 0
    hotspots_improved = 0
    ro_contacts = 0
    hotspots_targeted = 0
    patrol_visits = 0
    matched = {}

# ---------------------------------------------------------------------------
# KPI Strip
# ---------------------------------------------------------------------------
kpi_cols = st.columns(5)
with kpi_cols[0]:
    st.metric("Officers Deployed", officers)
with kpi_cols[1]:
    st.metric("Hotspots Targeted", hotspots_targeted)
with kpi_cols[2]:
    st.metric("PCIS Reduction", f"{pcis_red:.1f}")
with kpi_cols[3]:
    st.metric("Hotspots Improved", hotspots_improved)
with kpi_cols[4]:
    st.metric("Offender Contacts", ro_contacts)

st.markdown(f"<div style='height:12px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Charts row 1 — Waterfall + Scenario Comparison
# ---------------------------------------------------------------------------
chart_left, chart_right = st.columns([2, 3], gap="medium")

with chart_left:
    after_pcis = BASELINE_PCIS - pcis_red
    fig = waterfall_chart(
        categories=["Baseline PCIS", "Enforcement Impact", "After Enforcement"],
        values=[BASELINE_PCIS, -pcis_red, after_pcis],
        title="PCIS Impact Projection",
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True, key="waterfall")

with chart_right:
    if not roi_df.empty:
        fig = grouped_bar_chart(
            roi_df,
            x="scenario_id",
            y_cols=["projected_pcis_reduction", "projected_hotspot_reduction_count",
                    "estimated_repeat_offender_reduction"],
            names=["PCIS Reduction", "Hotspots Improved", "Offender Contacts"],
            title="All Scenarios Comparison",
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True, key="scenario_compare")

# ---------------------------------------------------------------------------
# Charts row 2 — Bubble chart + Matched scenario detail
# ---------------------------------------------------------------------------
detail_left, detail_right = st.columns([3, 2], gap="medium")

with detail_left:
    if not roi_df.empty:
        fig = scatter_chart(
            roi_df, x="additional_officers", y="projected_pcis_reduction",
            size_col="patrol_visits_added_per_month",
            title="Officers vs PCIS Reduction Landscape",
            height=350,
        )
        st.plotly_chart(fig, use_container_width=True, key="bubble")

with detail_right:
    st.markdown(
        f"""
        <div class="v2-panel">
            <div class="v2-panel-header">Matched Scenario Detail</div>
            <div style="font-size:1.1rem; font-weight:700; color:{COLORS['accent_cyan']};
                        margin-bottom:12px;">
                {matched.get('scenario_id', 'N/A') if isinstance(matched, (dict, pd.Series)) else 'N/A'}
            </div>
        """,
        unsafe_allow_html=True,
    )

    scenario_metrics = [
        ("Officers", officers),
        ("Intensity", intensity),
        ("Hotspots Targeted", hotspots_targeted),
        ("Patrol Visits/Month", patrol_visits),
        ("PCIS Reduction", f"{pcis_red:.2f}"),
        ("Hotspots Improved", hotspots_improved),
        ("Offender Contacts", ro_contacts),
    ]

    for label, val in scenario_metrics:
        st.markdown(
            f"""
            <div style="display:flex; justify-content:space-between; padding:4px 0;
                        border-bottom:1px solid {COLORS['border_subtle']};">
                <span style="font-size:0.76rem; color:{COLORS['text_secondary']};">{label}</span>
                <span style="font-size:0.76rem; font-weight:600;
                            color:{COLORS['text_bright']};">{val}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Full scenario table
# ---------------------------------------------------------------------------
st.markdown(f"<div style='height:18px;'></div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="v2-section-header">
        <span class="icon">📊</span>
        <span>All Scenarios</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if not roi_df.empty:
    display_cols = [c for c in roi_df.columns if not c.startswith("_")]
    st.dataframe(roi_df[display_cols], use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Model Assumptions
# ---------------------------------------------------------------------------
with st.expander("📋 Model Assumptions & Methodology"):
    st.markdown(
        f"""
        <div style="font-size:0.78rem; color:{COLORS['text_secondary']}; line-height:1.6;">
        <strong>Baseline Metrics:</strong><br>
        • Baseline PCIS: {BASELINE_PCIS} (city-wide average)<br>
        • Total Hotspots: 701 enforcement locations<br>
        • Total Violations: 298,450 records (Nov 2023 – Apr 2024)<br>
        • Repeat Offenders: 287 flagged vehicles<br><br>

        <strong>Simulation Model:</strong><br>
        • Officer visits/month: 20 per officer deployed<br>
        • Reduction per visit per intensity: 0.5%<br>
        • Max hotspot reduction cap: 70%<br>
        • RO capture rate: 8% per hotspot per visit<br>
        • PCIS enforcement factor: 0.40<br><br>

        <strong>Limitations:</strong><br>
        • Model assumes linear reduction within bounds<br>
        • Does not account for seasonal variation<br>
        • Offender contact estimates are probabilistic<br>
        </div>
        """,
        unsafe_allow_html=True,
    )
