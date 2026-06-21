"""
pages/2_Action_Center.py
========================
Action Center — per-station operational decision hub.

This is the central screen of the enforcement command center. It synthesises
all intelligence signals (PCIS, drift, repeat offenders, patrol routes) into
five operational sections:

  1. Today's Enforcement Plan     — Top 5 actionable recommendations
  2. Emerging Threat Alerts       — Hotspots with accelerating violation rates
  3. Officer Deployment Suggestions — Station-level patrol assignments
  4. Repeat Offender Targets      — High-value vehicle interception list
  5. Expected Impact              — ROI projection for current scope

Station filter in sidebar scopes all five sections simultaneously.
"""
import html
import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Path bootstrap
# ---------------------------------------------------------------------------
_PAGE_DIR     = Path(__file__).resolve().parent
_PROJECT_ROOT = _PAGE_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.data_service import list_stations
from src.recommendation_engine import generate_recommendations

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Action Center | AI Parking Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global styles
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
        color: #8b949e !important;
        font-size: 0.74rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    [data-testid="stMetricValue"] {
        color: #f0f6fc !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }
    .section-header {
        font-size: 1.05rem;
        font-weight: 600;
        color: #58a6ff;
        border-bottom: 1px solid #30363d;
        padding-bottom: 8px;
        margin: 22px 0 16px;
    }
    /* Action cards */
    .action-card {
        background: rgba(22,27,34,0.9);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 12px;
        transition: border-color 0.2s;
    }
    .action-card:hover { border-color: #58a6ff; }
    .action-card-critical { border-left: 4px solid #ff4444; }
    .action-card-high     { border-left: 4px solid #ff8c00; }
    .action-card-medium   { border-left: 4px solid #ffd700; }
    .action-card-low      { border-left: 4px solid #32cd32; }
    .action-card-urgent   { border-left: 4px solid #ff4444;
                             background: rgba(255,68,68,0.06); }
    /* Alert banner */
    .alert-banner {
        background: rgba(255,68,68,0.1);
        border: 1px solid rgba(255,68,68,0.4);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    .alert-banner-high {
        background: rgba(255,140,0,0.1);
        border: 1px solid rgba(255,140,0,0.4);
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    /* Offender card */
    .offender-card {
        background: rgba(22,27,34,0.9);
        border: 1px solid #30363d;
        border-left: 4px solid #da77f2;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    /* Deployment card */
    .deploy-card {
        background: rgba(22,27,34,0.9);
        border: 1px solid #30363d;
        border-left: 4px solid #58a6ff;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    #MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — station scope filter
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

    st.markdown(
        "<hr style='border:none;border-top:1px solid #30363d;margin:12px 0;'>",
        unsafe_allow_html=True,
    )
    st.markdown("**SCOPE**")

    all_stations = list_stations()
    station_sel  = st.selectbox(
        "Police Station",
        options=["All Stations"] + all_stations,
        index=0,
        key="ac_station",
        help="Filter all recommendations to a single police station.",
    )
    station_filter = None if station_sel == "All Stations" else station_sel

    st.markdown(
        "<div style='font-size:0.72rem;color:#444d56;margin-top:12px;'>"
        "All recommendations are generated from pre-computed enforcement intelligence. "
        "No live data required.</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
scope_label = station_filter if station_filter else "All Stations — Bengaluru BTP"
st.markdown(
    f"""
    <div style="padding:8px 0 4px;">
        <h1 style="font-size:2rem;font-weight:700;color:#f0f6fc;margin:0;">
            ⚡ Action Center
        </h1>
        <p style="color:#8b949e;font-size:0.92rem;margin:4px 0 0;">
            Operational enforcement recommendations · {scope_label}
        </p>
    </div>
    <hr style="border:none;border-top:1px solid #30363d;margin:12px 0 20px;">
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Load recommendations
# ---------------------------------------------------------------------------
with st.spinner("Generating enforcement recommendations…"):
    recs = generate_recommendations(station=station_filter)

top_actions        = recs["top_actions"]
emerging_alerts    = recs["emerging_alerts"]
patrol_deployments = recs["patrol_deployments"]
offender_targets   = recs["offender_targets"]
expected_impact    = recs["expected_impact"]
stations_at_risk   = recs["stations_at_risk"]

# ---------------------------------------------------------------------------
# Scope KPI strip
# ---------------------------------------------------------------------------
k1, k2, k3, k4, k5 = st.columns(5, gap="small")
with k1:
    st.metric("Active Actions", len(top_actions))
with k2:
    st.metric("🚨 Threat Alerts", len(emerging_alerts))
with k3:
    st.metric("🛣️ Deployment Plans", len(patrol_deployments))
with k4:
    st.metric("👤 Offender Targets", len(offender_targets))
with k5:
    n_crit = expected_impact.get("n_critical_in_scope", 0)
    st.metric("🔴 Critical in Scope", n_crit)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 1 — TODAY'S ENFORCEMENT PLAN
# ============================================================================
st.markdown(
    '<div class="section-header">📋 TODAY\'S ENFORCEMENT PLAN — TOP ACTIONS</div>',
    unsafe_allow_html=True,
)

if not top_actions:
    st.info("No critical or high-priority hotspots in the selected scope.")
else:
    for i, action in enumerate(top_actions, start=1):
        band      = action["priority_band"]
        card_cls  = f"action-card action-card-{band.lower()}"
        # Boost style for URGENT
        if "URGENT" in action["action_type"]:
            card_cls = "action-card action-card-urgent"

        band_color = {
            "Critical": "#ff4444", "High": "#ff8c00",
            "Medium":   "#ffd700", "Low":  "#32cd32",
        }.get(band, "#58a6ff")

        drift_badge = ""
        if action["drift_status"] == "Emerging" and action["drift_score"] >= 70:
            drift_badge = (
                f'<span style="background:rgba(255,68,68,0.15);color:#ff6b6b;'
                f'border:1px solid rgba(255,68,68,0.4);border-radius:4px;'
                f'padding:2px 8px;font-size:0.72rem;font-weight:600;margin-left:8px;">'
                f'🔺 EMERGING</span>'
            )

        st.markdown(
            f"""
            <div class="{card_cls}">
                <div style="display:flex;align-items:center;justify-content:space-between;
                            margin-bottom:8px;">
                    <div>
                        <span style="font-size:0.78rem;font-weight:700;color:{band_color};
                                     text-transform:uppercase;letter-spacing:0.08em;">
                            {action['action_type']}
                        </span>
                        {drift_badge}
                    </div>
                    <span style="font-size:0.78rem;color:#8b949e;">
                        Action #{i} · Rank #{action['rank_city']} city-wide
                    </span>
                </div>
                <div style="font-size:1rem;font-weight:600;color:#f0f6fc;margin-bottom:4px;">
                    {html.escape(str(action['hotspot_name']))}
                </div>
                <div style="font-size:0.82rem;color:#8b949e;margin-bottom:10px;">
                    📍 {html.escape(str(action['police_station']))}
                </div>
                <div style="display:flex;gap:20px;margin-bottom:10px;flex-wrap:wrap;">
                    <span style="font-size:0.82rem;">
                        <span style="color:#8b949e;">Priority:</span>
                        <span style="color:#f0f6fc;font-weight:600;">
                            {action['priority_score']:.2f}
                        </span>
                    </span>
                    <span style="font-size:0.82rem;">
                        <span style="color:#8b949e;">PCIS:</span>
                        <span style="color:#f0f6fc;font-weight:600;">
                            {action['pcis_score']:.1f}
                        </span>
                    </span>
                    <span style="font-size:0.82rem;">
                        <span style="color:#8b949e;">Drift:</span>
                        <span style="color:#f0f6fc;font-weight:600;">
                            {action['drift_score']:.1f}
                        </span>
                    </span>
                    <span style="font-size:0.82rem;">
                        <span style="color:#8b949e;">Violations:</span>
                        <span style="color:#f0f6fc;font-weight:600;">
                            {action['violation_count']:,}
                        </span>
                    </span>
                </div>
                <div style="font-size:0.84rem;color:#c9d1d9;
                            background:rgba(13,17,23,0.5);border-radius:6px;
                            padding:10px 12px;line-height:1.5;">
                    💡 {html.escape(str(action['reason']))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================================
# SECTION 2 — EMERGING THREAT ALERTS
# ============================================================================
st.markdown(
    '<div class="section-header">🚨 EMERGING THREAT ALERTS</div>',
    unsafe_allow_html=True,
)

if not emerging_alerts:
    st.success("✅ No high-drift emerging hotspots in selected scope.")
else:
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        for alert in emerging_alerts[:6]:
            urgency     = alert["urgency"]
            banner_cls  = "alert-banner" if urgency == "CRITICAL" else "alert-banner-high"
            urgency_col = "#ff4444" if urgency == "CRITICAL" else "#ff8c00"

            st.markdown(
                f"""
                <div class="{banner_cls}">
                    <div style="display:flex;justify-content:space-between;
                                align-items:center;margin-bottom:6px;">
                        <span style="font-size:0.78rem;font-weight:700;
                                     color:{urgency_col};text-transform:uppercase;
                                     letter-spacing:0.08em;">
                            ⚠️ {urgency} DRIFT
                        </span>
                        <span style="font-size:0.78rem;color:#8b949e;">
                            Drift: {alert['drift_score']:.1f}/100
                        </span>
                    </div>
                    <div style="font-size:0.95rem;font-weight:600;color:#f0f6fc;
                                margin-bottom:3px;">
                        {html.escape(str(alert['hotspot_name']))}
                    </div>
                    <div style="font-size:0.8rem;color:#8b949e;margin-bottom:8px;">
                        📍 {html.escape(str(alert['police_station']))} &nbsp;·&nbsp;
                        Route: <span style="color:#58a6ff;">{alert['patrol_route']}</span>
                    </div>
                    <div style="display:flex;gap:16px;margin-bottom:8px;flex-wrap:wrap;">
                        <span style="font-size:0.8rem;">
                            <span style="color:#8b949e;">Current rate:</span>
                            <span style="color:#f0f6fc;font-weight:600;">
                                {alert['mean_weekly_recent']:.1f}/wk
                            </span>
                        </span>
                        <span style="font-size:0.8rem;">
                            <span style="color:#8b949e;">Prior baseline:</span>
                            <span style="color:#f0f6fc;">
                                {alert['mean_weekly_prior']:.1f}/wk
                            </span>
                        </span>
                        <span style="font-size:0.8rem;">
                            <span style="color:#8b949e;">Change:</span>
                            <span style="color:{urgency_col};font-weight:600;">
                                {alert['pct_increase']:+.0f}%
                            </span>
                        </span>
                    </div>
                    <div style="font-size:0.8rem;color:#c9d1d9;font-style:italic;">
                        → {html.escape(str(alert['recommended_action']))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_right:
        if emerging_alerts:
            alert_names   = [a["hotspot_name"][:22] + "…"
                             if len(a["hotspot_name"]) > 22 else a["hotspot_name"]
                             for a in emerging_alerts[:8]]
            alert_drifts  = [a["drift_score"] for a in emerging_alerts[:8]]
            alert_colors  = [
                "#ff4444" if d >= 95 else "#ff8c00" if d >= 80 else "#ffd700"
                for d in alert_drifts
            ]

            fig_alerts = go.Figure(go.Bar(
                x=alert_drifts,
                y=alert_names,
                orientation="h",
                marker=dict(color=alert_colors,
                            line=dict(color="rgba(255,68,68,0.2)", width=1)),
                text=[f"  {d:.1f}" for d in alert_drifts],
                textposition="inside",
                textfont=dict(size=11, color="#f0f6fc"),
                hovertemplate="<b>%{y}</b><br>Drift Score: %{x:.1f}<extra></extra>",
            ))
            fig_alerts.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,17,23,0.6)",
                font=dict(family="Inter", color="#8b949e"),
                xaxis=dict(
                    title="Drift Score (0–100)",
                    range=[0, 105],
                    gridcolor="#21262d",
                    tickfont=dict(size=10),
                ),
                yaxis=dict(autorange="reversed", tickfont=dict(size=10, color="#e6edf3")),
                height=max(220, len(emerging_alerts[:8]) * 38),
                margin=dict(l=0, r=10, t=8, b=35),
                hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
                title=dict(text="Drift Score by Hotspot", font=dict(size=12, color="#8b949e")),
            )
            st.plotly_chart(fig_alerts, use_container_width=True,
                           config={"displayModeBar": False})

# ============================================================================
# SECTION 3 — OFFICER DEPLOYMENT SUGGESTIONS
# ============================================================================
st.markdown(
    '<div class="section-header">🛣️ OFFICER DEPLOYMENT SUGGESTIONS</div>',
    unsafe_allow_html=True,
)

if not patrol_deployments:
    st.info("No deployment suggestions for the selected scope.")
else:
    deploy_cols = st.columns(min(3, len(patrol_deployments)), gap="medium")
    for i, dep in enumerate(patrol_deployments[:6]):
        col = deploy_cols[i % len(deploy_cols)]
        with col:
            target_html = ""
            for t in dep["target_hotspots"]:
                t_color = {
                    "Critical": "#ff4444", "High": "#ff8c00",
                    "Medium": "#ffd700", "Low": "#32cd32",
                }.get(t["band"], "#58a6ff")
                target_html += (
                    f'<div style="font-size:0.78rem;color:#c9d1d9;padding:3px 0;">'
                    f'<span style="color:{t_color};">●</span> '
                    f'{t["name"]} '
                    f'<span style="color:#8b949e;">[{t["score"]:.1f}]</span>'
                    f'</div>'
                )

            routes_str = ", ".join(dep["patrol_routes"]) if dep["patrol_routes"] else "—"

            st.markdown(
                f"""
                <div class="deploy-card">
                    <div style="font-size:0.72rem;color:#58a6ff;text-transform:uppercase;
                                letter-spacing:0.08em;font-weight:600;margin-bottom:6px;">
                        STATION DEPLOYMENT
                    </div>
                    <div style="font-size:1rem;font-weight:700;color:#f0f6fc;
                                margin-bottom:8px;">
                        {html.escape(str(dep['police_station']))}
                    </div>
                    <div style="display:flex;gap:12px;margin-bottom:10px;flex-wrap:wrap;">
                        <div style="text-align:center;background:rgba(88,166,255,0.1);
                                    border-radius:8px;padding:6px 12px;">
                            <div style="font-size:1.3rem;font-weight:700;color:#58a6ff;">
                                {dep['officers_recommended']}
                            </div>
                            <div style="font-size:0.68rem;color:#8b949e;text-transform:uppercase;">
                                Officers
                            </div>
                        </div>
                        <div style="text-align:center;background:rgba(255,68,68,0.1);
                                    border-radius:8px;padding:6px 12px;">
                            <div style="font-size:1.3rem;font-weight:700;color:#ff4444;">
                                {dep['critical_hotspots']}
                            </div>
                            <div style="font-size:0.68rem;color:#8b949e;text-transform:uppercase;">
                                Critical
                            </div>
                        </div>
                        <div style="text-align:center;background:rgba(22,27,34,0.9);
                                    border-radius:8px;padding:6px 12px;">
                            <div style="font-size:1.3rem;font-weight:700;color:#e6edf3;">
                                {dep['n_routes']}
                            </div>
                            <div style="font-size:0.68rem;color:#8b949e;text-transform:uppercase;">
                                Routes
                            </div>
                        </div>
                    </div>
                    <div style="font-size:0.75rem;color:#8b949e;margin-bottom:6px;">
                        Routes: <span style="color:#58a6ff;">{routes_str}</span>
                    </div>
                    <div style="font-size:0.78rem;color:#8b949e;margin-bottom:8px;">
                        Priority targets:
                    </div>
                    {target_html}
                    <div style="font-size:0.75rem;color:#6e7681;margin-top:8px;
                                border-top:1px solid #21262d;padding-top:8px;">
                        {html.escape(str(dep['deployment_note']))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ============================================================================
# SECTION 4 — REPEAT OFFENDER TARGETS
# ============================================================================
st.markdown(
    '<div class="section-header">👤 REPEAT OFFENDER TARGETS</div>',
    unsafe_allow_html=True,
)

if not offender_targets:
    st.info("No high-score repeat offenders in the selected scope.")
else:
    ot_left, ot_right = st.columns([3, 2], gap="large")

    with ot_left:
        for off in offender_targets[:8]:
            peak_color = "#ff8c00" if off["peak_pct"] >= 50 else "#58a6ff"
            hotspot_str = " · ".join(
                [h[:30] for h in off["hotspot_names"][:3]]
            )
            station_str = " | ".join(off["police_stations"][:2])

            st.markdown(
                f"""
                <div class="offender-card">
                    <div style="display:flex;justify-content:space-between;
                                align-items:flex-start;margin-bottom:6px;">
                        <div>
                            <span style="font-size:1rem;font-weight:700;
                                         color:#f0f6fc;font-family:monospace;">
                                {html.escape(str(off['vehicle_number']))}
                            </span>
                            <span style="font-size:0.72rem;color:#8b949e;
                                         margin-left:10px;">
                                {html.escape(str(off['top_violation_type']))}
                            </span>
                        </div>
                        <span style="background:rgba(218,119,242,0.15);
                                     color:#da77f2;border-radius:4px;
                                     padding:2px 8px;font-size:0.72rem;
                                     font-weight:700;">
                            Score {off['offender_score']:.0f}
                        </span>
                    </div>
                    <div style="display:flex;gap:16px;margin-bottom:8px;flex-wrap:wrap;">
                        <span style="font-size:0.8rem;">
                            <span style="color:#8b949e;">Violations:</span>
                            <span style="color:#ff4444;font-weight:700;">
                                {off['total_violations']}
                            </span>
                        </span>
                        <span style="font-size:0.8rem;">
                            <span style="color:#8b949e;">Locations:</span>
                            <span style="color:#f0f6fc;font-weight:600;">
                                {off['distinct_hotspot_count']}
                            </span>
                        </span>
                        <span style="font-size:0.8rem;">
                            <span style="color:#8b949e;">Active span:</span>
                            <span style="color:#f0f6fc;">{off['active_span_days']} days</span>
                        </span>
                        <span style="font-size:0.8rem;">
                            <span style="color:#8b949e;">Peak hr:</span>
                            <span style="color:{peak_color};font-weight:600;">
                                {off['peak_pct']:.0f}%
                            </span>
                        </span>
                    </div>
                    <div style="font-size:0.78rem;color:#8b949e;margin-bottom:4px;">
                        📍 {hotspot_str}
                    </div>
                    <div style="font-size:0.78rem;color:#8b949e;margin-bottom:8px;">
                        Station: {station_str}
                    </div>
                    <div style="font-size:0.78rem;color:#c9d1d9;
                                background:rgba(13,17,23,0.5);border-radius:6px;
                                padding:8px 10px;">
                        → {html.escape(str(off['intercept_note']))}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with ot_right:
        if offender_targets:
            off_vehicles  = [o["vehicle_number"][-8:] for o in offender_targets[:8]]
            off_scores    = [o["offender_score"] for o in offender_targets[:8]]
            off_viols     = [o["total_violations"] for o in offender_targets[:8]]
            off_colors    = [
                "#da77f2" if s >= 80 else "#c084fc" if s >= 60 else "#a855f7"
                for s in off_scores
            ]

            fig_off = go.Figure()
            fig_off.add_trace(go.Bar(
                x=off_scores,
                y=off_vehicles,
                orientation="h",
                name="Offender Score",
                marker=dict(color=off_colors,
                            line=dict(color="rgba(218,119,242,0.2)", width=1)),
                text=[f"  {s:.0f}" for s in off_scores],
                textposition="inside",
                textfont=dict(size=11, color="#f0f6fc"),
                hovertemplate=(
                    "<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>"
                ),
            ))
            fig_off.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(13,17,23,0.6)",
                font=dict(family="Inter", color="#8b949e"),
                xaxis=dict(
                    title="Offender Score (0–100)",
                    range=[0, 110],
                    gridcolor="#21262d",
                    tickfont=dict(size=10),
                ),
                yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#e6edf3")),
                height=max(220, len(offender_targets[:8]) * 38),
                margin=dict(l=0, r=10, t=8, b=35),
                hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
                title=dict(text="Offender Score Ranking",
                           font=dict(size=12, color="#8b949e")),
                showlegend=False,
            )
            st.plotly_chart(fig_off, use_container_width=True,
                           config={"displayModeBar": False})

# ============================================================================
# SECTION 5 — EXPECTED IMPACT
# ============================================================================
st.markdown(
    '<div class="section-header">📈 EXPECTED IMPACT — DEPLOYMENT PROJECTION</div>',
    unsafe_allow_html=True,
)

roi = expected_impact.get("roi_scenario", {})

imp_left, imp_right = st.columns([3, 2], gap="large")

with imp_left:
    st.markdown(
        """
        <div style="font-size:0.82rem;color:#8b949e;margin-bottom:14px;">
            Based on ROI simulation model. All projections assume standard
            enforcement intensity. Figures are estimates, not guarantees.
        </div>
        """,
        unsafe_allow_html=True,
    )

    i1, i2, i3 = st.columns(3, gap="small")
    with i1:
        st.metric(
            "Projected PCIS Reduction",
            f"−{expected_impact['projected_pcis_reduction']:.1f}",
            help="Estimated reduction in mean PCIS score across targeted hotspots.",
        )
    with i2:
        st.metric(
            "Hotspots Improved",
            f"~{expected_impact['projected_hotspot_reduction']}",
            help="Estimated number of hotspots reaching lower severity after enforcement.",
        )
    with i3:
        st.metric(
            "Offender Contacts",
            f"~{expected_impact['estimated_ro_reduction']}",
            help="Estimated repeat offenders intercepted under this deployment.",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if roi:
        officers   = int(roi.get("additional_officers", 0) or 0)
        hotspots_t = int(roi.get("hotspots_targeted", 0) or 0)
        visits     = int(roi.get("patrol_visits_added_per_month", 0) or 0)
        eff_pct    = float(roi.get("effective_reduction_pct", 0) or 0)
        intensity  = float(roi.get("enforcement_intensity", 0) or 0)

        st.markdown(
            f"""
            <div style="background:rgba(22,27,34,0.9);border:1px solid #30363d;
                        border-radius:10px;padding:16px 18px;">
                <div style="font-size:0.78rem;color:#58a6ff;font-weight:600;
                            text-transform:uppercase;letter-spacing:0.06em;
                            margin-bottom:10px;">
                    Matched Scenario: {roi.get('scenario_id', '—')}
                </div>
                <div style="display:flex;gap:20px;flex-wrap:wrap;">
                    <div>
                        <div style="font-size:1.4rem;font-weight:700;color:#58a6ff;">
                            {officers}
                        </div>
                        <div style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;">
                            Officers Needed
                        </div>
                    </div>
                    <div>
                        <div style="font-size:1.4rem;font-weight:700;color:#f0f6fc;">
                            {hotspots_t}
                        </div>
                        <div style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;">
                            Hotspots Targeted
                        </div>
                    </div>
                    <div>
                        <div style="font-size:1.4rem;font-weight:700;color:#69db7c;">
                            {eff_pct:.0f}%
                        </div>
                        <div style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;">
                            Reduction Target
                        </div>
                    </div>
                    <div>
                        <div style="font-size:1.4rem;font-weight:700;color:#ffd43b;">
                            {visits:,}
                        </div>
                        <div style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;">
                            Patrol Visits/Month
                        </div>
                    </div>
                    <div>
                        <div style="font-size:1.4rem;font-weight:700;color:#ffa94d;">
                            {intensity:.1f}×
                        </div>
                        <div style="font-size:0.7rem;color:#8b949e;text-transform:uppercase;">
                            Intensity Factor
                        </div>
                    </div>
                </div>
                <div style="font-size:0.72rem;color:#444d56;margin-top:12px;border-top:
                            1px solid #21262d;padding-top:10px;">
                    Model assumptions: baseline=4 violations/hotspot/month,
                    20 visits/officer/month, 0.5%/visit reduction at intensity=1,
                    cap=70%, RO capture=8%/hotspot/visit.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with imp_right:
    # Waterfall chart: current state → projected reduction
    if roi:
        pcis_start  = 52.79   # mean PCIS from Phase 2 (documented in reports)
        pcis_reduce = float(expected_impact["projected_pcis_reduction"])
        pcis_end    = max(0, pcis_start - pcis_reduce)

        fig_wfall = go.Figure(go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=["Baseline PCIS", "Projected Reduction", "After Enforcement"],
            y=[pcis_start, -pcis_reduce, 0],
            connector=dict(line=dict(color="#30363d", width=1)),
            increasing=dict(marker=dict(color="#ff4444")),
            decreasing=dict(marker=dict(color="#69db7c")),
            totals=dict(marker=dict(color="#58a6ff")),
            text=[f"{pcis_start:.1f}", f"−{pcis_reduce:.1f}", f"{pcis_end:.1f}"],
            textposition="outside",
            textfont=dict(color="#e6edf3", size=12),
        ))
        fig_wfall.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(13,17,23,0.6)",
            font=dict(family="Inter", color="#8b949e"),
            yaxis=dict(
                title="Mean PCIS Score",
                gridcolor="#21262d",
                range=[0, pcis_start + 10],
            ),
            xaxis=dict(tickfont=dict(size=11, color="#e6edf3")),
            height=280,
            margin=dict(l=0, r=0, t=12, b=10),
            showlegend=False,
            hoverlabel=dict(bgcolor="#161b22", bordercolor="#30363d"),
            title=dict(text="PCIS Reduction Projection",
                       font=dict(size=12, color="#8b949e")),
        )
        st.plotly_chart(fig_wfall, use_container_width=True,
                       config={"displayModeBar": False})

# ---------------------------------------------------------------------------
# Stations at risk strip
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="section-header">🏆 HIGHEST RISK STATIONS</div>',
    unsafe_allow_html=True,
)

if stations_at_risk:
    cols_stn = st.columns(len(stations_at_risk), gap="small")
    for i, stn in enumerate(stations_at_risk):
        with cols_stn[i]:
            st.markdown(
                f"""
                <div style="background:rgba(22,27,34,0.85);border:1px solid #30363d;
                            border-radius:10px;padding:14px;text-align:center;">
                    <div style="font-size:0.78rem;font-weight:600;color:#f0f6fc;
                                margin-bottom:8px;min-height:32px;">
                        {stn['police_station']}
                    </div>
                    <div style="font-size:1.5rem;font-weight:700;color:#ff4444;">
                        {stn['max_priority']:.1f}
                    </div>
                    <div style="font-size:0.68rem;color:#8b949e;text-transform:uppercase;
                                margin-bottom:8px;">Peak Priority</div>
                    <div style="font-size:0.76rem;color:#8b949e;">
                        🔴 {stn['critical_count']} critical
                        &nbsp;·&nbsp;
                        🔺 {stn['emerging_count']} emerging
                    </div>
                    <div style="font-size:0.74rem;color:#6e7681;margin-top:4px;">
                        {stn['total_violations']:,} violations
                    </div>
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
    st.page_link("pages/1_Command_Center.py",
                 label="← Command Center", use_container_width=True)
with nav2:
    st.page_link("pages/3_City_Risk_Map.py",
                 label="🗺️ City Risk Map →", use_container_width=True)
