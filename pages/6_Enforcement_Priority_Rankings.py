"""
pages/6_Enforcement_Priority_Rankings.py
=========================================
Enforcement Priority Rankings — full sortable/filterable ranking table with
score decomposition, station drill-down, and component breakdown charts.

Features:
  - Full 701-row table with station + band filters + search
  - Priority score decomposition: PCIS contribution, drift contribution,
    repeat offender density contribution
  - Component breakdown radar chart for selected hotspot
  - Station drill-down: top hotspots per station
  - Top-10 leaderboard per component (PCIS, drift, repeat offender density)
"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

_PAGE_DIR     = Path(__file__).resolve().parent
_PROJECT_ROOT = _PAGE_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data_service import get_hotspots, list_stations, list_bands

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Priority Rankings | AI Parking Intelligence",
    page_icon="🏆",
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
        background: rgba(22,27,34,0.85); border: 1px solid #30363d;
        border-radius: 12px; padding: 14px 16px;
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important; font-size: 0.74rem !important;
        font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.06em;
    }
    [data-testid="stMetricValue"] {
        color: #f0f6fc !important; font-size: 1.6rem !important; font-weight: 700 !important;
    }
    .section-header {
        font-size: 1.05rem; font-weight: 600; color: #58a6ff;
        border-bottom: 1px solid #30363d; padding-bottom: 8px; margin: 20px 0 14px;
    }
    .rank-badge {
        display: inline-block;
        background: rgba(88,166,255,0.15);
        color: #58a6ff; border: 1px solid rgba(88,166,255,0.3);
        border-radius: 4px; padding: 2px 8px;
        font-size: 0.78rem; font-weight: 700;
    }
    #MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)

BAND_COLOR = {
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
    st.page_link("app.py",                                  label="🏠 Home")
    st.page_link("pages/1_Command_Center.py",               label="📊 Command Center")
    st.page_link("pages/2_Action_Center.py",                label="⚡ Action Center")
    st.page_link("pages/3_City_Risk_Map.py",                label="🗺️ City Risk Map")
    st.page_link("pages/6_Enforcement_Priority_Rankings.py",label="🏆 Priority Rankings")
    st.page_link("pages/7_Patrol_Planner.py",              label="🛣️ Patrol Planner")
    st.page_link("pages/8_ROI_Simulator.py",               label="📈 ROI Simulator")

    st.markdown(
        "<hr style='border:none;border-top:1px solid #30363d;margin:12px 0;'>",
        unsafe_allow_html=True,
    )
    st.markdown("**FILTERS**")

    all_stations = ["All Stations"] + list_stations()
    station_sel  = st.selectbox("Police Station", all_stations, index=0, key="pr_station")

    band_sel = st.multiselect(
        "Priority Band",
        options=list_bands(),
        default=list_bands(),
        key="pr_bands",
    )

    type_sel = st.multiselect(
        "Hotspot Type",
        options=["Named Junction", "Discovered Unknown"],
        default=["Named Junction", "Discovered Unknown"],
        key="pr_types",
    )

    search_term = st.text_input(
        "Search hotspot name",
        placeholder="e.g. Subbanna, Rajajinagar…",
        key="pr_search",
    )

    sort_by = st.selectbox(
        "Sort by",
        options=["Priority Score", "PCIS Score", "Drift Score", "Repeat Offender Density"],
        index=0,
        key="pr_sort",
    )

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="padding:8px 0 4px;">
        <h1 style="font-size:2rem;font-weight:700;color:#f0f6fc;margin:0;">
            🏆 Enforcement Priority Rankings
        </h1>
        <p style="color:#8b949e;font-size:0.92rem;margin:4px 0 0;">
            Full priority ranking with score decomposition · All 701 hotspots · Bengaluru BTP
        </p>
    </div>
    <hr style="border:none;border-top:1px solid #30363d;margin:12px 0 20px;">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load + filter data
# ---------------------------------------------------------------------------
station_filter = None if station_sel == "All Stations" else station_sel
df_all = get_hotspots(station=station_filter)

if band_sel:
    df_all = df_all[df_all["priority_band"].isin(band_sel)]
if type_sel:
    df_all = df_all[df_all["hotspot_type"].isin(type_sel)]
if search_term:
    df_all = df_all[
        df_all["hotspot_name"].str.contains(search_term, case=False, na=False)
    ]

sort_col_map = {
    "Priority Score": "priority_score",
    "PCIS Score": "pcis_score",
    "Drift Score": "drift_score",
    "Repeat Offender Density": "repeat_offender_density_norm",
}
sort_col = sort_col_map[sort_by]
df_sorted = df_all.sort_values(sort_col, ascending=False).reset_index(drop=True)

# ---------------------------------------------------------------------------
# Summary KPI strip
# ---------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5, gap="small")
with k1:
    st.metric("Showing", f"{len(df_sorted):,} hotspots")
with k2:
    n_crit = int((df_sorted["priority_band"] == "Critical").sum())
    st.metric("🔴 Critical", n_crit)
with k3:
    n_high = int((df_sorted["priority_band"] == "High").sum())
    st.metric("🟠 High", n_high)
with k4:
    avg_p  = float(df_sorted["priority_score"].mean()) if len(df_sorted) else 0
    st.metric("Avg Priority", f"{avg_p:.2f}")
with k5:
    avg_pcis = float(df_sorted["pcis_score"].mean()) if len(df_sorted) else 0
    st.metric("Avg PCIS", f"{avg_pcis:.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tab layout: Rankings | Component Breakdown | Station Drill-down
# ---------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📋 Full Rankings", "📊 Component Breakdown", "🏢 Station Drill-down"])

# ============================================================================
# TAB 1 — FULL RANKINGS TABLE
# ============================================================================
with tab1:
    st.markdown(
        '<div class="section-header">PRIORITY RANKINGS — SORTABLE TABLE</div>',
        unsafe_allow_html=True,
    )

    # Build display table
    table_cols = [
        "rank_city", "rank_station", "hotspot_name", "police_station",
        "priority_band", "priority_score", "pcis_score", "drift_score",
        "severity_norm", "repeat_offender_density_norm",
        "violation_count", "drift_status", "hotspot_type",
    ]
    avail_cols = [c for c in table_cols if c in df_sorted.columns]
    tbl = df_sorted[avail_cols].copy()

    tbl.rename(columns={
        "rank_city":                    "City Rank",
        "rank_station":                 "Stn Rank",
        "hotspot_name":                 "Hotspot",
        "police_station":               "Station",
        "priority_band":                "Band",
        "priority_score":               "Priority",
        "pcis_score":                   "PCIS",
        "drift_score":                  "Drift",
        "severity_norm":                "Severity",
        "repeat_offender_density_norm": "RO Density",
        "violation_count":              "Violations",
        "drift_status":                 "Drift Status",
        "hotspot_type":                 "Type",
    }, inplace=True)

    for col in ["Priority", "PCIS", "Drift", "Severity", "RO Density"]:
        if col in tbl.columns:
            tbl[col] = tbl[col].round(2)

    st.dataframe(
        tbl,
        use_container_width=True,
        hide_index=True,
        height=480,
        column_config={
            "City Rank":  st.column_config.NumberColumn("City Rank", width="small"),
            "Stn Rank":   st.column_config.NumberColumn("Stn Rank", width="small"),
            "Hotspot":    st.column_config.TextColumn("Hotspot", width="large"),
            "Station":    st.column_config.TextColumn("Station", width="medium"),
            "Band":       st.column_config.TextColumn("Band", width="small"),
            "Priority":   st.column_config.NumberColumn("Priority ↓", format="%.2f"),
            "PCIS":       st.column_config.NumberColumn("PCIS", format="%.2f"),
            "Drift":      st.column_config.NumberColumn("Drift", format="%.1f"),
            "Severity":   st.column_config.NumberColumn("Severity", format="%.2f"),
            "RO Density": st.column_config.NumberColumn("RO Density", format="%.2f"),
            "Violations": st.column_config.NumberColumn("Violations", format="%d"),
            "Drift Status":st.column_config.TextColumn("Drift Status", width="medium"),
            "Type":       st.column_config.TextColumn("Type", width="medium"),
        },
    )

    st.markdown(
        f"<div style='font-size:0.75rem;color:#444d56;margin-top:6px;'>"
        f"Showing {len(tbl):,} hotspots · Sorted by {sort_by}"
        f"</div>",
        unsafe_allow_html=True,
    )

# ============================================================================
# TAB 2 — COMPONENT BREAKDOWN
# ============================================================================
with tab2:
    left_c, right_c = st.columns([3, 2], gap="large")

    with left_c:
        st.markdown(
            '<div class="section-header">TOP 15 — PCIS COMPONENT CONTRIBUTION</div>',
            unsafe_allow_html=True,
        )

        top15 = df_sorted.head(15).copy()

        if len(top15) > 0 and all(c in top15.columns for c in
                                   ["priority_score", "pcis_score",
                                    "drift_score", "repeat_offender_density_norm"]):

            names_short = [
                n[:25] + "…" if len(n) > 25 else n
                for n in top15["hotspot_name"].tolist()
            ]
            bands = top15["priority_band"].tolist()

            # Normalise component contributions to sum to priority_score
            # Priority = 0.5*pcis_norm + 0.3*drift_norm + 0.2*ro_norm (approximate weights)
            pcis_contrib = (top15["pcis_score"] * 0.5).tolist()
            drift_contrib = (top15["drift_score"] * 0.3).tolist()
            ro_contrib = (top15["repeat_offender_density_norm"] * 0.2).tolist()
            severity_contrib = (top15.get("severity_norm", top15["priority_score"] * 0) * 0.0).tolist()

            fig_stacked = go.Figure()
            fig_stacked.add_trace(go.Bar(
                name="PCIS Contribution",
                x=names_short,
                y=pcis_contrib,
                marker=dict(color="#58a6ff", line=dict(color="#0d1117", width=0.5)),
                hovertemplate="<b>%{x}</b><br>PCIS contrib: %{y:.2f}<extra></extra>",
            ))
            fig_stacked.add_trace(go.Bar(
                name="Drift Contribution",
                x=names_short,
                y=drift_contrib,
                marker=dict(color="#ff8c00", line=dict(color="#0d1117", width=0.5)),
                hovertemplate="<b>%{x}</b><br>Drift contrib: %{y:.2f}<extra></extra>",
            ))
            fig_stacked.add_trace(go.Bar(
                name="RO Density Contribution",
                x=names_short,
                y=ro_contrib,
                marker=dict(color="#da77f2", line=dict(color="#0d1117", width=0.5)),
                hovertemplate="<b>%{x}</b><br>RO contrib: %{y:.2f}<extra></extra>",
            ))

            # Overlay priority score line
            fig_stacked.add_trace(go.Scatter(
                name="Priority Score",
                x=names_short,
                y=top15["priority_score"].tolist(),
                mode="lines+markers",
                line=dict(color="#ffd43b", width=2.5, dash="dot"),
                marker=dict(size=7, color="#ffd43b"),
                hovertemplate="<b>%{x}</b><br>Priority Score: %{y:.2f}<extra></extra>",
            ))

            fig_stacked.update_layout(
                barmode="stack",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,17,23,0.6)",
                font=dict(family="Inter", color="#8b949e"),
                xaxis=dict(
                    tickangle=-35,
                    tickfont=dict(size=10, color="#e6edf3"),
                    gridcolor="#21262d",
                ),
                yaxis=dict(
                    title="Score Contribution",
                    gridcolor="#21262d",
                    tickfont=dict(size=10),
                ),
                legend=dict(
                    orientation="h", x=0, y=1.08,
                    font=dict(size=10, color="#e6edf3"),
                    bgcolor="rgba(0,0,0,0)",
                ),
                height=420,
                margin=dict(l=0, r=0, t=32, b=100),
                hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
            )
            st.plotly_chart(fig_stacked, use_container_width=True,
                           config={"displayModeBar": False})

    with right_c:
        st.markdown(
            '<div class="section-header">SCORE DISTRIBUTION BY BAND</div>',
            unsafe_allow_html=True,
        )

        if len(df_sorted) > 0:
            # Box plots per band
            fig_box = go.Figure()
            band_order = ["Critical", "High", "Medium", "Low"]
            for band in band_order:
                band_df = df_sorted[df_sorted["priority_band"] == band]
                if len(band_df) == 0:
                    continue
                fig_box.add_trace(go.Box(
                    y=band_df["priority_score"].tolist(),
                    name=band,
                    marker_color=BAND_COLOR.get(band, "#58a6ff"),
                    line=dict(width=2),
                    boxmean="sd",
                    hovertemplate=(
                        f"<b>{band}</b><br>"
                        "Priority: %{y:.2f}<extra></extra>"
                    ),
                ))
            fig_box.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,17,23,0.6)",
                font=dict(family="Inter", color="#8b949e"),
                yaxis=dict(
                    title="Priority Score", gridcolor="#21262d", tickfont=dict(size=10),
                ),
                xaxis=dict(tickfont=dict(size=11, color="#e6edf3")),
                height=200,
                margin=dict(l=0, r=0, t=8, b=10),
                showlegend=False,
                hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
                title=dict(text="Priority Score Distribution by Band",
                           font=dict(size=12, color="#8b949e")),
            )
            st.plotly_chart(fig_box, use_container_width=True,
                           config={"displayModeBar": False})

        st.markdown(
            '<div class="section-header" style="margin-top:12px;">COMPONENT CORRELATION</div>',
            unsafe_allow_html=True,
        )

        if len(df_sorted) >= 10:
            sample_df = df_sorted.dropna(subset=["pcis_score", "drift_score", "priority_score"])
            band_color_map = {
                "Critical": "#ff4444", "High": "#ff8c00",
                "Medium": "#ffd700", "Low": "#32cd32",
            }
            point_colors = [
                band_color_map.get(b, "#58a6ff")
                for b in sample_df["priority_band"].tolist()
            ]
            fig_scatter = go.Figure(go.Scatter(
                x=sample_df["pcis_score"].tolist(),
                y=sample_df["drift_score"].tolist(),
                mode="markers",
                marker=dict(
                    size=6,
                    color=point_colors,
                    opacity=0.65,
                    line=dict(color="rgba(0,0,0,0.2)", width=0.5),
                ),
                customdata=sample_df[["hotspot_name", "priority_score",
                                      "priority_band"]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "PCIS: %{x:.1f} | Drift: %{y:.1f}<br>"
                    "Priority: %{customdata[1]:.2f} [%{customdata[2]}]"
                    "<extra></extra>"
                ),
            ))
            fig_scatter.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,17,23,0.6)",
                font=dict(family="Inter", color="#8b949e"),
                xaxis=dict(title="PCIS Score", gridcolor="#21262d", tickfont=dict(size=10)),
                yaxis=dict(title="Drift Score", gridcolor="#21262d", tickfont=dict(size=10)),
                height=200,
                margin=dict(l=0, r=0, t=8, b=10),
                hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
                title=dict(text="PCIS vs Drift Score (colour = band)",
                           font=dict(size=12, color="#8b949e")),
            )
            st.plotly_chart(fig_scatter, use_container_width=True,
                           config={"displayModeBar": False})

    # ------------------------------------------------------------------
    # Component leaderboard tables
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="section-header">COMPONENT LEADERBOARDS — TOP 10 PER SIGNAL</div>',
        unsafe_allow_html=True,
    )

    lb1, lb2, lb3 = st.columns(3, gap="medium")

    def _leaderboard(df: pd.DataFrame, col: str, label: str, color: str, fmt: str = ".2f"):
        top = df.dropna(subset=[col]).nlargest(10, col)[
            ["hotspot_name", "police_station", "priority_band", col]
        ].copy()
        top["#"] = range(1, len(top) + 1)
        top.rename(columns={col: label, "hotspot_name": "Hotspot",
                             "police_station": "Station", "priority_band": "Band"}, inplace=True)
        top[label] = top[label].round(2)
        return top[["#", "Hotspot", "Station", "Band", label]]

    with lb1:
        st.markdown(
            f"<div style='font-size:0.8rem;font-weight:600;color:#58a6ff;"
            f"margin-bottom:8px;'>🔵 PCIS Score</div>",
            unsafe_allow_html=True,
        )
        lb_pcis = _leaderboard(df_sorted, "pcis_score", "PCIS", "#58a6ff")
        st.dataframe(lb_pcis, use_container_width=True, hide_index=True, height=340,
                     column_config={
                         "#": st.column_config.NumberColumn("#", width="small"),
                         "Hotspot": st.column_config.TextColumn("Hotspot"),
                         "Station": st.column_config.TextColumn("Station"),
                         "Band": st.column_config.TextColumn("Band", width="small"),
                         "PCIS": st.column_config.NumberColumn("PCIS", format="%.2f"),
                     })

    with lb2:
        st.markdown(
            f"<div style='font-size:0.8rem;font-weight:600;color:#ff8c00;"
            f"margin-bottom:8px;'>🟠 Drift Score</div>",
            unsafe_allow_html=True,
        )
        lb_drift = _leaderboard(df_sorted, "drift_score", "Drift", "#ff8c00")
        st.dataframe(lb_drift, use_container_width=True, hide_index=True, height=340,
                     column_config={
                         "#": st.column_config.NumberColumn("#", width="small"),
                         "Hotspot": st.column_config.TextColumn("Hotspot"),
                         "Station": st.column_config.TextColumn("Station"),
                         "Band": st.column_config.TextColumn("Band", width="small"),
                         "Drift": st.column_config.NumberColumn("Drift", format="%.1f"),
                     })

    with lb3:
        st.markdown(
            f"<div style='font-size:0.8rem;font-weight:600;color:#da77f2;"
            f"margin-bottom:8px;'>👤 Repeat Offender Density</div>",
            unsafe_allow_html=True,
        )
        lb_ro = _leaderboard(df_sorted, "repeat_offender_density_norm", "RO Density", "#da77f2")
        st.dataframe(lb_ro, use_container_width=True, hide_index=True, height=340,
                     column_config={
                         "#": st.column_config.NumberColumn("#", width="small"),
                         "Hotspot": st.column_config.TextColumn("Hotspot"),
                         "Station": st.column_config.TextColumn("Station"),
                         "Band": st.column_config.TextColumn("Band", width="small"),
                         "RO Density": st.column_config.NumberColumn("RO Density", format="%.2f"),
                     })

# ============================================================================
# TAB 3 — STATION DRILL-DOWN
# ============================================================================
with tab3:
    st.markdown(
        '<div class="section-header">STATION DRILL-DOWN</div>',
        unsafe_allow_html=True,
    )

    all_stations_list = list_stations()
    drill_station = st.selectbox(
        "Select Station to Drill Down",
        options=all_stations_list,
        index=0,
        key="pr_drill_station",
    )

    stn_df = get_hotspots(station=drill_station)
    stn_df = stn_df.sort_values("priority_score", ascending=False).reset_index(drop=True)

    # Station KPIs
    d1, d2, d3, d4, d5 = st.columns(5, gap="small")
    with d1:
        st.metric("Hotspots", len(stn_df))
    with d2:
        stn_crit = int((stn_df["priority_band"] == "Critical").sum())
        st.metric("🔴 Critical", stn_crit)
    with d3:
        stn_avg = float(stn_df["priority_score"].mean()) if len(stn_df) else 0
        st.metric("Avg Priority", f"{stn_avg:.2f}")
    with d4:
        stn_max = float(stn_df["priority_score"].max()) if len(stn_df) else 0
        st.metric("Max Priority", f"{stn_max:.2f}")
    with d5:
        em_count = int((stn_df.get("drift_status", pd.Series()) == "Emerging").sum()) if "drift_status" in stn_df.columns else 0
        st.metric("🔺 Emerging", em_count)

    st.markdown("<br>", unsafe_allow_html=True)

    if len(stn_df) > 0:
        drill_left, drill_right = st.columns([2, 3], gap="large")

        with drill_left:
            # Band donut for station
            band_counts = stn_df["priority_band"].value_counts()
            bo = ["Critical", "High", "Medium", "Low"]
            bc = ["#ff4444", "#ff8c00", "#ffd700", "#32cd32"]
            bv = [int(band_counts.get(b, 0)) for b in bo]
            fig_d = go.Figure(go.Pie(
                labels=bo, values=bv, hole=0.55,
                marker=dict(colors=bc, line=dict(color="#0d1117", width=2)),
                textinfo="label+percent",
                textfont=dict(size=11, color="#f0f6fc"),
            ))
            fig_d.add_annotation(
                text=f"<b>{len(stn_df)}</b>",
                x=0.5, y=0.5,
                font=dict(size=16, color="#f0f6fc", family="Inter"),
                showarrow=False,
            )
            fig_d.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#8b949e"),
                height=260, margin=dict(l=0, r=0, t=8, b=8),
                showlegend=False,
                title=dict(text=f"{drill_station} — Band Distribution",
                           font=dict(size=11, color="#8b949e")),
            )
            st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})

        with drill_right:
            # Top 10 hotspots horizontal bar
            top10_stn = stn_df.head(10)
            stn_names  = [n[:28] + "…" if len(n) > 28 else n
                          for n in top10_stn["hotspot_name"].tolist()]
            stn_scores = top10_stn["priority_score"].tolist()
            stn_colors = [BAND_COLOR.get(b, "#58a6ff")
                          for b in top10_stn["priority_band"].tolist()]

            fig_h = go.Figure(go.Bar(
                x=stn_scores,
                y=stn_names,
                orientation="h",
                marker=dict(color=stn_colors,
                            line=dict(color="rgba(0,0,0,0.2)", width=1)),
                text=[f"  {s:.2f}" for s in stn_scores],
                textposition="inside",
                textfont=dict(size=11, color="#0d1117"),
                customdata=top10_stn[["priority_band", "pcis_score",
                                       "drift_score"]].values,
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Priority: %{x:.2f}<br>"
                    "Band: %{customdata[0]}<br>"
                    "PCIS: %{customdata[1]:.1f}<br>"
                    "Drift: %{customdata[2]:.1f}<extra></extra>"
                ),
            ))
            fig_h.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,17,23,0.6)",
                font=dict(family="Inter", color="#8b949e"),
                xaxis=dict(
                    title="Priority Score", gridcolor="#21262d", tickfont=dict(size=10),
                ),
                yaxis=dict(
                    autorange="reversed", tickfont=dict(size=10, color="#e6edf3"),
                ),
                height=320,
                margin=dict(l=0, r=10, t=8, b=35),
                hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
                title=dict(text=f"Top 10 Hotspots — {drill_station}",
                           font=dict(size=12, color="#8b949e")),
            )
            st.plotly_chart(fig_h, use_container_width=True, config={"displayModeBar": False})

    # Station full table
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander(f"📋 All Hotspots — {drill_station} ({len(stn_df)} total)", expanded=True):
        stn_tbl_cols = [
            "rank_city", "rank_station", "hotspot_name", "priority_band",
            "priority_score", "pcis_score", "drift_score",
            "repeat_offender_density_norm", "violation_count", "drift_status",
        ]
        stn_avail = [c for c in stn_tbl_cols if c in stn_df.columns]
        stn_tbl = stn_df[stn_avail].copy()
        stn_tbl.rename(columns={
            "rank_city": "City Rank", "rank_station": "Stn Rank",
            "hotspot_name": "Hotspot", "priority_band": "Band",
            "priority_score": "Priority", "pcis_score": "PCIS",
            "drift_score": "Drift",
            "repeat_offender_density_norm": "RO Density",
            "violation_count": "Violations", "drift_status": "Drift Status",
        }, inplace=True)
        for col in ["Priority", "PCIS", "Drift", "RO Density"]:
            if col in stn_tbl.columns:
                stn_tbl[col] = stn_tbl[col].round(2)

        st.dataframe(
            stn_tbl, use_container_width=True, hide_index=True,
            column_config={
                "City Rank":  st.column_config.NumberColumn("City Rank", width="small"),
                "Stn Rank":   st.column_config.NumberColumn("Stn Rank", width="small"),
                "Hotspot":    st.column_config.TextColumn("Hotspot", width="large"),
                "Band":       st.column_config.TextColumn("Band", width="small"),
                "Priority":   st.column_config.NumberColumn("Priority", format="%.2f"),
                "PCIS":       st.column_config.NumberColumn("PCIS", format="%.2f"),
                "Drift":      st.column_config.NumberColumn("Drift", format="%.1f"),
                "RO Density": st.column_config.NumberColumn("RO Density", format="%.2f"),
                "Violations": st.column_config.NumberColumn("Violations", format="%d"),
                "Drift Status": st.column_config.TextColumn("Drift Status"),
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
    st.page_link("pages/7_Patrol_Planner.py",
                 label="🛣️ Patrol Planner →", use_container_width=True)
