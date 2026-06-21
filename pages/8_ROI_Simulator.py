"""
pages/8_ROI_Simulator.py
=========================
ROI Simulator — interactive what-if resource deployment modelling.

Features:
  - Officer allocation slider (2–20)
  - Enforcement intensity selector (0.5×, 0.7×, 0.8×, 1.0×)
  - Scenario selector (8 pre-computed scenarios from Phase 3)
  - Animated projected outputs: hotspot reduction, PCIS reduction, repeat offender contacts
  - Plotly impact comparison chart across all 8 scenarios
  - Waterfall chart: current PCIS → projected PCIS after enforcement
  - Scenario comparison table
  - Assumption transparency panel
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

_PAGE_DIR     = Path(__file__).resolve().parent
_PROJECT_ROOT = _PAGE_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data_service import get_roi_data

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ROI Simulator | AI Parking Intelligence",
    page_icon="📈",
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
        padding: 18px 20px;
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important; font-size: 0.76rem !important;
        font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.06em;
    }
    [data-testid="stMetricValue"] {
        color: #f0f6fc !important; font-size: 2.0rem !important; font-weight: 700 !important;
    }
    .section-header {
        font-size: 1.05rem; font-weight: 600; color: #58a6ff;
        border-bottom: 1px solid #30363d; padding-bottom: 8px; margin: 22px 0 14px;
    }
    .scenario-card {
        background: rgba(22,27,34,0.9); border: 1px solid #30363d;
        border-radius: 12px; padding: 20px; margin-bottom: 0;
    }
    .scenario-card-selected {
        border-color: #58a6ff;
        box-shadow: 0 0 18px rgba(88,166,255,0.15);
    }
    .impact-number {
        font-size: 2.4rem; font-weight: 800; line-height: 1;
    }
    #MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_BASELINE_PCIS     = 52.79   # city-wide mean PCIS (from Phase 2 summary)
_TOTAL_HOTSPOTS    = 701
_TOTAL_VIOLATIONS  = 298450
_REPEAT_OFFENDERS  = 287

INTENSITY_MAP = {
    "0.5× — Light enforcement": 0.5,
    "0.7× — Moderate enforcement": 0.7,
    "0.8× — Sustained enforcement": 0.8,
    "1.0× — Full enforcement": 1.0,
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
    st.page_link("pages/8_ROI_Simulator.py",  label="📈 ROI Simulator")

    st.markdown(
        "<hr style='border:none;border-top:1px solid #30363d;margin:12px 0;'>",
        unsafe_allow_html=True,
    )
    st.markdown("**DEPLOYMENT PARAMETERS**")

    officers = st.slider(
        "Additional Officers",
        min_value=2, max_value=20, value=5, step=1,
        key="roi_officers",
        help="Number of additional enforcement officers deployed.",
    )

    intensity_label = st.selectbox(
        "Enforcement Intensity",
        options=list(INTENSITY_MAP.keys()),
        index=1,
        key="roi_intensity",
        help="Intensity factor scales the number of effective patrol visits per officer.",
    )
    intensity_val = INTENSITY_MAP[intensity_label]

    st.markdown(
        "<div style='font-size:0.72rem;color:#444d56;margin-top:12px;'>"
        "Projections use the Phase 3 ROI simulation model. "
        "Figures are estimates based on historical enforcement patterns.</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Load ROI data
# ---------------------------------------------------------------------------
roi_df = get_roi_data()

# Find closest matching scenario
def _closest_scenario(df: pd.DataFrame, officers: int, intensity: float) -> dict:
    """Pick scenario closest to selected officers + intensity."""
    df = df.copy()
    df["_dist"] = (
        (df["additional_officers"] - officers).abs() * 2 +
        (df["enforcement_intensity"] - intensity).abs() * 10
    )
    idx = df["_dist"].idxmin()
    return df.loc[idx].to_dict()

matched = _closest_scenario(roi_df, officers, intensity_val)
scenario_id = str(matched.get("scenario_id", "—"))

# Interpolate projections (linear scaling from matched scenario)
officer_ratio = officers / max(float(matched.get("additional_officers", 1)), 1)
proj_hotspot_count  = round(float(matched.get("projected_hotspot_reduction_count", 0)) * officer_ratio)
proj_pcis_reduction = float(matched.get("projected_pcis_reduction", 0)) * officer_ratio
proj_ro_reduction   = round(float(matched.get("estimated_repeat_offender_reduction", 0)) * officer_ratio)
proj_visits         = round(float(matched.get("patrol_visits_added_per_month", 0)) * officer_ratio)
eff_pct             = float(matched.get("effective_reduction_pct", 0))
hotspots_targeted   = round(float(matched.get("hotspots_targeted", 0)) * officer_ratio)

# Cap projections at realistic bounds
proj_hotspot_count = min(proj_hotspot_count, _TOTAL_HOTSPOTS)
proj_ro_reduction  = min(proj_ro_reduction,  _REPEAT_OFFENDERS)
pcis_after         = max(0, _BASELINE_PCIS - proj_pcis_reduction)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div style="padding:8px 0 4px;">
        <h1 style="font-size:2rem;font-weight:700;color:#f0f6fc;margin:0;">
            📈 ROI Simulator
        </h1>
        <p style="color:#8b949e;font-size:0.92rem;margin:4px 0 0;">
            Enforcement resource deployment modelling ·
            Matched scenario: <span style="color:#58a6ff;">{scenario_id}</span>
        </p>
    </div>
    <hr style="border:none;border-top:1px solid #30363d;margin:12px 0 20px;">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Live projection KPIs — animated delta indicators
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="section-header">PROJECTED ENFORCEMENT IMPACT</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4, k5 = st.columns(5, gap="small")
with k1:
    st.metric(
        "Officers Deployed",
        f"{officers}",
        help="Additional officers assigned to enforcement operations.",
    )
with k2:
    st.metric(
        "Hotspots Targeted",
        f"{hotspots_targeted}",
        delta=f"{eff_pct:.0f}% reduction target",
        delta_color="normal",
        help="Hotspots covered by additional patrol visits.",
    )
with k3:
    st.metric(
        "PCIS Reduction",
        f"−{proj_pcis_reduction:.2f}",
        delta=f"{_BASELINE_PCIS:.1f} → {pcis_after:.1f}",
        delta_color="off",
        help="Projected reduction in mean city PCIS score.",
    )
with k4:
    st.metric(
        "Hotspots Improved",
        f"~{proj_hotspot_count}",
        delta=f"of {_TOTAL_HOTSPOTS} total",
        delta_color="off",
        help="Hotspots projected to reach lower severity tier.",
    )
with k5:
    st.metric(
        "Offender Contacts",
        f"~{proj_ro_reduction}",
        delta=f"of {_REPEAT_OFFENDERS} flagged",
        delta_color="off",
        help="Repeat offenders projected to be intercepted under this deployment.",
    )

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Row 2: Waterfall + Scenario comparison
# ---------------------------------------------------------------------------
left_col, right_col = st.columns([2, 3], gap="large")

with left_col:
    st.markdown(
        '<div class="section-header">PCIS IMPACT PROJECTION</div>',
        unsafe_allow_html=True,
    )

    fig_wfall = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Baseline<br>PCIS", "Projected<br>Reduction", "After<br>Enforcement"],
        y=[_BASELINE_PCIS, -proj_pcis_reduction, 0],
        connector=dict(line=dict(color="#30363d", width=1.5, dash="dot")),
        increasing=dict(marker=dict(color="#ff4444", line=dict(color="#ff6b6b", width=1))),
        decreasing=dict(marker=dict(color="#238636", line=dict(color="#2ea043", width=1))),
        totals=dict(marker=dict(color="#58a6ff", line=dict(color="#79c0ff", width=1))),
        text=[
            f"<b>{_BASELINE_PCIS:.1f}</b>",
            f"<b>−{proj_pcis_reduction:.2f}</b>",
            f"<b>{pcis_after:.1f}</b>",
        ],
        textposition="outside",
        textfont=dict(color="#e6edf3", size=13, family="Inter"),
        hoverinfo="x+y",
    ))
    fig_wfall.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,0.6)",
        font=dict(family="Inter", color="#8b949e"),
        yaxis=dict(
            title="Mean PCIS Score",
            gridcolor="#21262d",
            range=[0, _BASELINE_PCIS + 12],
            tickfont=dict(size=11),
        ),
        xaxis=dict(tickfont=dict(size=12, color="#e6edf3")),
        height=340,
        margin=dict(l=0, r=0, t=8, b=20),
        showlegend=False,
        hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
    )
    st.plotly_chart(fig_wfall, use_container_width=True, config={"displayModeBar": False})

with right_col:
    st.markdown(
        '<div class="section-header">ALL SCENARIOS — COMPARISON</div>',
        unsafe_allow_html=True,
    )

    # Multi-metric bar chart for all 8 scenarios
    scenario_labels = roi_df["scenario_id"].tolist()
    scenario_officers = roi_df["additional_officers"].tolist()
    pcis_reductions = roi_df["projected_pcis_reduction"].tolist()
    hotspot_reductions = roi_df["projected_hotspot_reduction_count"].tolist()
    ro_reductions = roi_df["estimated_repeat_offender_reduction"].tolist()

    # Highlight selected scenario
    highlight_colors_pcis = [
        "#58a6ff" if s == scenario_id else "#21262d"
        for s in scenario_labels
    ]
    highlight_colors_hs = [
        "#69db7c" if s == scenario_id else "#1a3020"
        for s in scenario_labels
    ]
    highlight_colors_ro = [
        "#da77f2" if s == scenario_id else "#2d1b3d"
        for s in scenario_labels
    ]

    fig_compare = go.Figure()
    fig_compare.add_trace(go.Bar(
        name="PCIS Reduction",
        x=scenario_labels,
        y=pcis_reductions,
        marker=dict(color=highlight_colors_pcis,
                    line=dict(color="rgba(88,166,255,0.2)", width=1)),
        text=[f"{v:.1f}" for v in pcis_reductions],
        textposition="outside",
        textfont=dict(size=10, color="#8b949e"),
        hovertemplate="<b>%{x}</b><br>PCIS Reduction: %{y:.2f}<extra></extra>",
    ))
    fig_compare.add_trace(go.Bar(
        name="Hotspots Improved",
        x=scenario_labels,
        y=hotspot_reductions,
        marker=dict(color=highlight_colors_hs,
                    line=dict(color="rgba(105,219,124,0.2)", width=1)),
        text=[f"{int(v)}" for v in hotspot_reductions],
        textposition="outside",
        textfont=dict(size=10, color="#8b949e"),
        hovertemplate="<b>%{x}</b><br>Hotspots Improved: %{y}<extra></extra>",
        visible="legendonly",
    ))
    fig_compare.add_trace(go.Bar(
        name="Offender Contacts",
        x=scenario_labels,
        y=ro_reductions,
        marker=dict(color=highlight_colors_ro,
                    line=dict(color="rgba(218,119,242,0.2)", width=1)),
        text=[f"{int(v)}" for v in ro_reductions],
        textposition="outside",
        textfont=dict(size=10, color="#8b949e"),
        hovertemplate="<b>%{x}</b><br>Offender Contacts: %{y}<extra></extra>",
        visible="legendonly",
    ))

    # Officer count line
    fig_compare.add_trace(go.Scatter(
        name="Officers",
        x=scenario_labels,
        y=scenario_officers,
        mode="lines+markers",
        line=dict(color="#ffd43b", width=2, dash="dot"),
        marker=dict(size=7, color="#ffd43b"),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Officers: %{y}<extra></extra>",
    ))

    fig_compare.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,0.6)",
        font=dict(family="Inter", color="#8b949e"),
        barmode="group",
        xaxis=dict(
            title="Scenario",
            gridcolor="#21262d",
            tickfont=dict(size=11, color="#e6edf3"),
        ),
        yaxis=dict(
            title="PCIS Reduction / Count",
            gridcolor="#21262d",
            tickfont=dict(size=11),
        ),
        yaxis2=dict(
            title=dict(
                text="Officers",
                font=dict(color="#ffd43b")
            ),
            overlaying="y",
            side="right",
            tickfont=dict(size=11, color="#ffd43b"),
            gridcolor="rgba(0,0,0,0)",
        ),
        
        legend=dict(
            orientation="h",
            x=0, y=1.08,
            font=dict(size=11, color="#e6edf3"),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=340,
        margin=dict(l=0, r=40, t=32, b=40),
        hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
    )
    st.plotly_chart(fig_compare, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Row 3: Bubble chart + matched scenario card
# ---------------------------------------------------------------------------
bub_col, card_col = st.columns([3, 2], gap="large")

with bub_col:
    st.markdown(
        '<div class="section-header">OFFICERS vs IMPACT — SCENARIO LANDSCAPE</div>',
        unsafe_allow_html=True,
    )

    bubble_colors = [
        "#58a6ff" if s == scenario_id else "#30363d"
        for s in roi_df["scenario_id"]
    ]
    bubble_borders = [
        "#58a6ff" if s == scenario_id else "#444d56"
        for s in roi_df["scenario_id"]
    ]

    fig_bubble = go.Figure(go.Scatter(
        x=roi_df["additional_officers"].tolist(),
        y=roi_df["projected_pcis_reduction"].tolist(),
        mode="markers+text",
        marker=dict(
            size=[float(v) * 1.8 for v in roi_df["patrol_visits_added_per_month"]],
            color=bubble_colors,
            line=dict(color=bubble_borders, width=2),
            sizemode="area",
            sizeref=2.0,
        ),
        text=roi_df["scenario_id"].tolist(),
        textposition="top center",
        textfont=dict(size=10, color="#e6edf3"),
        customdata=roi_df[["scenario_id", "hotspots_targeted",
                           "patrol_visits_added_per_month",
                           "estimated_repeat_offender_reduction"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Officers: %{x}<br>"
            "PCIS Reduction: %{y:.2f}<br>"
            "Hotspots Targeted: %{customdata[1]}<br>"
            "Patrol Visits/mo: %{customdata[2]}<br>"
            "Offender Contacts: %{customdata[3]}<extra></extra>"
        ),
    ))
    fig_bubble.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(13,17,23,0.6)",
    font=dict(family="Inter", color="#8b949e"),

    xaxis=dict(
        title="Additional Officers",
        gridcolor="#21262d",
        tickfont=dict(size=11),
    ),

    yaxis=dict(
        title="Projected PCIS Reduction",
        gridcolor="#21262d",
        tickfont=dict(size=11),
    ),

    height=320,
    margin=dict(l=0, r=0, t=8, b=40),

    hoverlabel=dict(
        bgcolor="#161b22",
        bordercolor="#30363d",
    ),

    annotations=[
        dict(
            text="Bubble size = patrol visits/month · Blue = matched scenario",
            x=0,
            y=-0.18,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=10, color="#444d56"),
        )
    ],
    )
    
    st.plotly_chart(fig_bubble, use_container_width=True, config={"displayModeBar": False})

with card_col:

    st.info(f"{scenario_id} · BEST MATCH")

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "Officers",
            int(matched.get("additional_officers", 0))
        )

    with c2:
        st.metric(
            "Reduction %",
            f"{float(matched.get('effective_reduction_pct',0)):.0f}%"
        )

    c3, c4 = st.columns(2)

    with c3:
        st.metric(
            "Visits/mo",
            int(matched.get("patrol_visits_added_per_month",0))
        )

    with c4:
        st.metric(
            "Targeted",
            int(matched.get("hotspots_targeted",0))
        )

    st.divider()

    st.write(
        f"""
PCIS reduction: {float(matched.get('projected_pcis_reduction',0)):.2f}

Hotspots improved: {int(matched.get('projected_hotspot_reduction_count',0))}

Offender contacts: {int(matched.get('estimated_repeat_offender_reduction',0))}

Intensity factor: {float(matched.get('enforcement_intensity',0)):.1f}
"""
    )

# ---------------------------------------------------------------------------
# Full scenario comparison table
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    '<div class="section-header">ALL SCENARIOS — FULL COMPARISON TABLE</div>',
    unsafe_allow_html=True,
)

display_roi = roi_df[[
    "scenario_id", "additional_officers", "hotspots_targeted",
    "patrol_visits_added_per_month", "enforcement_intensity",
    "effective_reduction_pct", "projected_pcis_reduction",
    "projected_hotspot_reduction_count", "estimated_repeat_offender_reduction",
]].copy()

display_roi.rename(columns={
    "scenario_id":                        "Scenario",
    "additional_officers":                "Officers",
    "hotspots_targeted":                  "Targeted",
    "patrol_visits_added_per_month":      "Visits/mo",
    "enforcement_intensity":              "Intensity",
    "effective_reduction_pct":            "Reduction %",
    "projected_pcis_reduction":           "PCIS −",
    "projected_hotspot_reduction_count":  "Hotspots ↓",
    "estimated_repeat_offender_reduction":"Offenders ↓",
}, inplace=True)

st.dataframe(
    display_roi,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Scenario":    st.column_config.TextColumn("Scenario", width="small"),
        "Officers":    st.column_config.NumberColumn("Officers", format="%d"),
        "Targeted":    st.column_config.NumberColumn("Targeted", format="%d"),
        "Visits/mo":   st.column_config.NumberColumn("Visits/mo", format="%d"),
        "Intensity":   st.column_config.NumberColumn("Intensity", format="%.1f"),
        "Reduction %": st.column_config.NumberColumn("Reduction %", format="%.1f%%"),
        "PCIS −":      st.column_config.NumberColumn("PCIS −", format="%.2f"),
        "Hotspots ↓":  st.column_config.NumberColumn("Hotspots ↓", format="%d"),
        "Offenders ↓": st.column_config.NumberColumn("Offenders ↓", format="%d"),
    },
)

# ---------------------------------------------------------------------------
# Assumption panel
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("🔍 Model Assumptions & Methodology", expanded=False):
    st.markdown(
        """
        <div style="font-size:0.85rem;color:#c9d1d9;line-height:1.8;">

        **A1 · Baseline enforcement density**
        Each hotspot currently receives approximately 4 patrol visits per month
        under existing officer capacity.

        **B1 · Officer visit capacity**
        Each additional officer can conduct approximately 20 targeted patrol
        visits per month at the specified enforcement locations.

        **C1 · Violation reduction rate**
        Each patrol visit reduces violations at 0.5% per visit at intensity = 1.0.
        Intensity factor scales this linearly (e.g. 0.5× → 0.25% per visit).

        **C2 · Reduction cap**
        Maximum achievable reduction is capped at 70% to account for demand
        inelasticity — some parking violations persist regardless of enforcement.

        **C3 · Repeat offender capture rate**
        8% of repeat offenders are expected to be intercepted per hotspot per
        patrol visit, based on average multi-hotspot activity patterns.

        **D1 · PCIS impact factor**
        Enforcement activity reduces PCIS by 0.4 points per percentage point
        of violation reduction, reflecting the multi-component nature of PCIS
        (daily density, peak-hour share, large vehicle share, main road share,
        repeat offender ratio).

        **Scope**
        All projections are city-wide estimates. Station-level projections
        available via the Action Center with station scope filter applied.
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
nav1, nav2 = st.columns(2, gap="medium")
with nav1:
    st.page_link("pages/7_Patrol_Planner.py",
                 label="← Patrol Planner", use_container_width=True)
with nav2:
    st.page_link("pages/6_Enforcement_Priority_Rankings.py",
                 label="🏆 Priority Rankings →", use_container_width=True)
