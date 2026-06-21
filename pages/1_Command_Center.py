"""
pages/1_Command_Center.py
=========================
Command Center — citywide situation awareness dashboard.

Screens:
  - KPI strip: Total Hotspots | Critical | Emerging | Repeat Offenders | Patrol Routes
  - Top 10 stations by risk (bar chart)
  - Critical hotspot table (top 20 city-wide)
  - Priority band distribution (donut chart)
  - Quick navigation to other screens
"""

import sys
from pathlib import Path

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Path bootstrap — ensure src/ is importable regardless of working directory
# ---------------------------------------------------------------------------
_PAGE_DIR     = Path(__file__).resolve().parent
_PROJECT_ROOT = _PAGE_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data_service import (
    city_kpis,
    get_priority_hotspots,
    get_station_summary,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Command Center | AI Parking Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global styles (duplicated from app.py so the page works standalone)
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
                                 border-radius:12px; padding:18px 20px; }
    [data-testid="stMetricLabel"] { color:#8b949e !important; font-size:0.76rem !important;
                                     font-weight:500 !important; text-transform:uppercase;
                                     letter-spacing:0.06em; }
    [data-testid="stMetricValue"] { color:#f0f6fc !important; font-size:1.9rem !important;
                                     font-weight:700 !important; }
    .section-header { font-size:1.05rem; font-weight:600; color:#58a6ff;
                       border-bottom:1px solid #30363d; padding-bottom:8px;
                       margin:20px 0 14px; }
    .kpi-critical [data-testid="stMetricValue"] { color:#ff6b6b !important; }
    .kpi-emerging [data-testid="stMetricValue"] { color:#ffa94d !important; }
    .kpi-offender [data-testid="stMetricValue"] { color:#da77f2 !important; }
    #MainMenu { visibility:hidden; } footer { visibility:hidden; } header { visibility:hidden; }
    ::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-thumb { background:#30363d; border-radius:3px; }
    </style>
    """,
    unsafe_allow_html=True,
)

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
    st.page_link("app.py",                  label="🏠 Home")
    st.page_link("pages/1_Command_Center.py", label="📊 Command Center")
    st.page_link("pages/3_City_Risk_Map.py",  label="🗺️ City Risk Map")


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="padding:8px 0 4px;">
        <h1 style="font-size:2rem;font-weight:700;color:#f0f6fc;margin:0;">
            📊 Command Center
        </h1>
        <p style="color:#8b949e;font-size:0.92rem;margin:4px 0 0;">
            Citywide enforcement intelligence · Bengaluru BTP · Nov 2023 – Apr 2024
        </p>
    </div>
    <hr style="border:none;border-top:1px solid #30363d;margin:12px 0 24px;">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
with st.spinner("Loading intelligence data…"):
    kpis       = city_kpis()
    station_df = get_station_summary()
    top20      = get_priority_hotspots(top_n=20)

# ---------------------------------------------------------------------------
# KPI Strip — Row 1
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">SITUATION OVERVIEW</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5, gap="small")

with k1:
    st.metric(
        label="Total Hotspots",
        value=f"{kpis['total_hotspots']:,}",
        help="All enforcement hotspots across 54 police stations.",
    )
with k2:
    st.metric(
        label="🔴 Critical",
        value=f"{kpis['critical_hotspots']:,}",
        delta=f"Top 15% by priority score",
        delta_color="off",
        help="Hotspots in the Critical priority band (top 15th percentile).",
    )
with k3:
    st.metric(
        label="🟠 Emerging",
        value=f"{kpis['emerging_hotspots']:,}",
        delta="Drift Z > 1.5σ",
        delta_color="off",
        help="Named hotspots showing statistically significant violation acceleration.",
    )
with k4:
    st.metric(
        label="👤 Repeat Offenders",
        value=f"{kpis['repeat_offenders']:,}",
        delta="≥8 violations, ≥2 hotspots",
        delta_color="off",
        help="Vehicles flagged as persistent violators.",
    )
with k5:
    st.metric(
        label="🛣️ Patrol Routes",
        value=f"{kpis['patrol_routes']:,}",
        delta="Across 54 stations",
        delta_color="off",
        help="Pre-computed nearest-neighbour patrol sequences.",
    )

st.markdown("<br>", unsafe_allow_html=True)

# Second KPI row — volume context
k6, k7, k8, k9 = st.columns(4, gap="small")
with k6:
    st.metric("Total Violations", f"{kpis['total_violations']:,}")
with k7:
    st.metric("Highest Risk Station", kpis["top_station"])
with k8:
    st.metric("City #1 Hotspot", kpis["top_hotspot_name"][:28] + "…"
              if len(kpis["top_hotspot_name"]) > 28 else kpis["top_hotspot_name"])
with k9:
    st.metric("City #1 Priority Score", f"{kpis['top_priority_score']:.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Row 2 — Station leaderboard + Band distribution
# ---------------------------------------------------------------------------
col_left, col_right = st.columns([3, 2], gap="large")

with col_left:
    st.markdown('<div class="section-header">TOP 10 STATIONS BY PEAK PRIORITY SCORE</div>',
                unsafe_allow_html=True)

    top10_stations = station_df.head(10).copy()
    top10_stations["station_label"] = top10_stations["police_station"].str[:22]

    # Colour bars by critical count intensity
    max_crit = top10_stations["critical_count"].max() or 1
    bar_colors = [
        f"rgba(255, {max(30, 107 - int(c / max_crit * 80))}, {max(30, 107 - int(c / max_crit * 80))}, 0.85)"
        for c in top10_stations["critical_count"]
    ]

    fig_stations = go.Figure(go.Bar(
        x=top10_stations["max_priority"],
        y=top10_stations["station_label"],
        orientation="h",
        marker=dict(color=bar_colors, line=dict(color="rgba(255,107,107,0.3)", width=1)),
        text=[f"  {s:.1f}" for s in top10_stations["max_priority"]],
        textposition="inside",
        textfont=dict(size=12, color="#f0f6fc"),
        customdata=top10_stations[["total_hotspots", "critical_count",
                                    "emerging_count", "total_violations"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Peak Priority: %{x:.2f}<br>"
            "Hotspots: %{customdata[0]}<br>"
            "Critical: %{customdata[1]}<br>"
            "Emerging: %{customdata[2]}<br>"
            "Violations: %{customdata[3]:,}<extra></extra>"
        ),
    ))
    fig_stations.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(13,17,23,0.6)",
        font=dict(family="Inter", color="#8b949e"),
        xaxis=dict(
            title="Peak Priority Score",
            gridcolor="#21262d",
            showline=False,
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(size=12, color="#e6edf3"),
        ),
        height=360,
        margin=dict(l=0, r=20, t=10, b=40),
        hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d", font_size=13),
    )
    st.plotly_chart(fig_stations, use_container_width=True, config={"displayModeBar": False})

with col_right:
    st.markdown('<div class="section-header">PRIORITY BAND DISTRIBUTION</div>',
                unsafe_allow_html=True)

    band_counts = top20["priority_band"].value_counts() if len(top20) else None
    all_hotspots = get_priority_hotspots(top_n=701)
    band_series  = all_hotspots["priority_band"].value_counts()

    band_order  = ["Critical", "High", "Medium", "Low"]
    band_colors = ["#ff6b6b", "#ffa94d", "#ffd43b", "#69db7c"]
    band_vals   = [int(band_series.get(b, 0)) for b in band_order]

    fig_donut = go.Figure(go.Pie(
        labels=band_order,
        values=band_vals,
        hole=0.58,
        marker=dict(colors=band_colors,
                    line=dict(color="#0d1117", width=2)),
        textinfo="label+percent",
        textfont=dict(size=12, color="#f0f6fc"),
        hovertemplate="<b>%{label}</b><br>%{value} hotspots<br>%{percent}<extra></extra>",
    ))
    fig_donut.add_annotation(
        text=f"<b>701</b><br><span style='font-size:10px'>hotspots</span>",
        x=0.5, y=0.5,
        font=dict(size=16, color="#f0f6fc", family="Inter"),
        showarrow=False,
        align="center",
    )
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#8b949e"),
        showlegend=True,
        legend=dict(
            orientation="v",
            x=1.0, y=0.5,
            font=dict(size=12, color="#e6edf3"),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=340,
        margin=dict(l=0, r=10, t=10, b=10),
        hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Row 3 — Critical hotspot table
# ---------------------------------------------------------------------------
st.markdown('<div class="section-header">TOP 20 CRITICAL HOTSPOTS — CITY-WIDE RANKING</div>',
            unsafe_allow_html=True)

display_cols = [
    "rank_city", "hotspot_name", "police_station", "priority_band",
    "priority_score", "pcis_score", "drift_score", "violation_count",
]
available = [c for c in display_cols if c in top20.columns]
table_df  = top20[available].copy()

col_renames = {
    "rank_city":       "Rank",
    "hotspot_name":    "Hotspot",
    "police_station":  "Station",
    "priority_band":   "Band",
    "priority_score":  "Priority",
    "pcis_score":      "PCIS",
    "drift_score":     "Drift",
    "violation_count": "Violations",
}
table_df.rename(columns={k: v for k, v in col_renames.items() if k in table_df.columns},
                inplace=True)

if "Priority" in table_df.columns:
    table_df["Priority"] = table_df["Priority"].round(2)
if "PCIS" in table_df.columns:
    table_df["PCIS"] = table_df["PCIS"].round(2)
if "Drift" in table_df.columns:
    table_df["Drift"] = table_df["Drift"].round(1)

st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Rank":       st.column_config.NumberColumn("Rank", width="small"),
        "Hotspot":    st.column_config.TextColumn("Hotspot", width="large"),
        "Station":    st.column_config.TextColumn("Station", width="medium"),
        "Band":       st.column_config.TextColumn("Band", width="small"),
        "Priority":   st.column_config.NumberColumn("Priority Score", format="%.2f"),
        "PCIS":       st.column_config.NumberColumn("PCIS", format="%.2f"),
        "Drift":      st.column_config.NumberColumn("Drift", format="%.1f"),
        "Violations": st.column_config.NumberColumn("Violations", format="%d"),
    },
)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Row 4 — Station detail table
# ---------------------------------------------------------------------------
with st.expander("📋 Full Station Risk Summary", expanded=False):
    st.markdown('<div class="section-header">ALL STATIONS — RISK SUMMARY</div>',
                unsafe_allow_html=True)

    station_display = station_df.copy()
    station_display.rename(columns={
        "police_station":        "Station",
        "total_hotspots":        "Hotspots",
        "critical_count":        "Critical",
        "high_count":            "High",
        "medium_count":          "Medium",
        "low_count":             "Low",
        "emerging_count":        "Emerging",
        "avg_priority":          "Avg Priority",
        "max_priority":          "Max Priority",
        "total_violations":      "Violations",
        "repeat_offender_count": "Repeat Offenders",
    }, inplace=True)

    st.dataframe(
        station_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Station":         st.column_config.TextColumn("Station", width="medium"),
            "Hotspots":        st.column_config.NumberColumn("Hotspots"),
            "Critical":        st.column_config.NumberColumn("Critical"),
            "High":            st.column_config.NumberColumn("High"),
            "Emerging":        st.column_config.NumberColumn("Emerging"),
            "Max Priority":    st.column_config.NumberColumn("Max Priority", format="%.2f"),
            "Avg Priority":    st.column_config.NumberColumn("Avg Priority", format="%.2f"),
            "Violations":      st.column_config.NumberColumn("Violations", format="%d"),
            "Repeat Offenders":st.column_config.NumberColumn("Repeat Offenders"),
        },
    )

# ---------------------------------------------------------------------------
# Quick navigation
# ---------------------------------------------------------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown('<div class="section-header">QUICK NAVIGATION</div>', unsafe_allow_html=True)

n1, n2 = st.columns(2, gap="medium")
with n1:
    st.page_link(
        "pages/3_City_Risk_Map.py",
        label="🗺️  Open City Risk Map — All 701 hotspots on the map",
        use_container_width=True,
    )
