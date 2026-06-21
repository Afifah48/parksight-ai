"""
pages_v2/operations.py
======================
Operations Center — Redesigned Action Center.
Recommendation cards grouped by type with station filtering.
"""

import streamlit as st
from styles_v2.theme import COLORS, inject_v2_theme
from styles_v2.components import inject_component_css
from components_v2.sidebar import render_sidebar
from components_v2.topbar import render_topbar
from components_v2.kpi_card import render_kpi_strip
from components_v2.action_card import (
    render_action_card, render_enforcement_card, render_station_status_card,
)

# ---------------------------------------------------------------------------
# Theme + sidebar
# ---------------------------------------------------------------------------
inject_v2_theme()
st.markdown(inject_component_css(), unsafe_allow_html=True)
render_sidebar(active_page="Operations")

# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
render_topbar(module_name="Operations Center")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
try:
    from src.data_service import list_stations
    from src.recommendation_engine import generate_recommendations

    stations = list_stations()
except Exception as e:
    st.error(f"Data loading error: {e}")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar — Station filter
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f"<div style='margin-top:16px; font-size:0.72rem; font-weight:600; "
        f"color:{COLORS['text_muted']}; text-transform:uppercase; letter-spacing:0.08em;'>"
        f"Station Filter</div>",
        unsafe_allow_html=True,
    )
    selected_station = st.selectbox(
        "Police Station",
        ["All Stations"] + stations,
        key="ops_station",
        label_visibility="collapsed",
    )

# Generate recommendations
station_param = None if selected_station == "All Stations" else selected_station
recs = generate_recommendations(station=station_param)

top_actions = recs.get("top_actions", [])
emerging_alerts = recs.get("emerging_alerts", [])
deployments = recs.get("patrol_deployments", [])
offender_targets = recs.get("offender_targets", [])
expected = recs.get("expected_impact", {})

# ---------------------------------------------------------------------------
# KPI Strip
# ---------------------------------------------------------------------------
render_kpi_strip([
    {"label": "Active Actions", "value": len(top_actions)},
    {"label": "Emerging Alerts", "value": len(emerging_alerts)},
    {"label": "Deployments", "value": len(deployments)},
    {"label": "Offender Targets", "value": len(offender_targets)},
    {"label": "Critical In Scope", "value": expected.get("n_critical_in_scope", 0)},
])

st.markdown(f"<div style='height:12px;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabbed interface
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡ Priority Actions",
    "🔥 Emerging Alerts",
    "🚔 Deployments",
    "🎯 Offender Targets",
])

# ---- Tab 1: Priority Actions ----
with tab1:
    if top_actions:
        for action in top_actions:
            render_action_card(
                title=action.get("hotspot_name", ""),
                description=action.get("reason", ""),
                priority_band=action.get("priority_band", "High"),
                action_type=action.get("action_type", ""),
                metrics={
                    "Score": f"{action.get('priority_score', 0):.1f}",
                    "PCIS": f"{action.get('pcis_score', 0):.1f}",
                    "Rank": f"#{action.get('rank_city', 'N/A')}",
                },
            )
    else:
        st.info("No priority actions for the selected scope.")

# ---- Tab 2: Emerging Alerts ----
with tab2:
    if emerging_alerts:
        for alert in emerging_alerts:
            urgency = alert.get("urgency", "ELEVATED")
            band = "Critical" if urgency == "CRITICAL" else "High" if urgency == "HIGH" else "Medium"

            pct = alert.get("pct_increase", 0)
            recent = alert.get("mean_weekly_recent", 0)
            prior = alert.get("mean_weekly_prior", 0)

            render_action_card(
                title=alert.get("hotspot_name", ""),
                description=alert.get("recommended_action", ""),
                priority_band=band,
                action_type=f"🔥 {urgency} — Drift: {alert.get('drift_score', 0):.1f}",
                metrics={
                    "Drift Score": f"{alert.get('drift_score', 0):.1f}",
                    "Weekly Recent": f"{recent:.0f}",
                    "Weekly Prior": f"{prior:.0f}",
                    "Increase": f"+{pct:.0f}%" if pct > 0 else f"{pct:.0f}%",
                },
            )
    else:
        st.info("No emerging threat alerts for the selected scope.")

# ---- Tab 3: Deployments ----
with tab3:
    if deployments:
        dep_cols = st.columns(min(len(deployments), 3))
        for i, dep in enumerate(deployments):
            with dep_cols[i % len(dep_cols)]:
                crit = dep.get("critical_hotspots", 0)
                render_station_status_card(
                    station_name=dep.get("police_station", "Unknown"),
                    status="Critical Load" if crit > 2 else "Elevated" if crit > 0 else "Normal",
                    active_units=dep.get("officers_recommended", 1),
                    total_units=dep.get("total_hotspots", 10),
                )
                # Additional deployment info
                st.markdown(
                    f"""
                    <div style="font-size:0.72rem; color:{COLORS['text_secondary']};
                                padding:6px 0; line-height:1.5;">
                        {dep.get('deployment_note', '')}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        st.info("No deployment suggestions for the selected scope.")

# ---- Tab 4: Offender Targets ----
with tab4:
    if offender_targets:
        for offender in offender_targets[:5]:
            render_enforcement_card(
                vehicle_number=offender.get("vehicle_number", "N/A"),
                violation_count=int(offender.get("total_violations", 0)),
                confidence=offender.get("offender_score", 0),
                description=offender.get("intercept_note", ""),
                primary_offense=offender.get("top_violation_type", ""),
            )
    else:
        st.info("No offender targets for the selected scope.")

# ---------------------------------------------------------------------------
# Expected Impact Section
# ---------------------------------------------------------------------------
st.markdown(f"<div style='height:18px;'></div>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div class="v2-section-header">
        <span class="icon">📊</span>
        <span>Expected Impact</span>
    </div>
    """,
    unsafe_allow_html=True,
)

roi = expected.get("roi_scenario", {})
impact_cols = st.columns(4)

with impact_cols[0]:
    st.metric(
        "PCIS Reduction",
        f"{expected.get('projected_pcis_reduction', 0):.1f}",
    )
with impact_cols[1]:
    st.metric(
        "Hotspots Improved",
        f"{expected.get('projected_hotspot_reduction', 0)}",
    )
with impact_cols[2]:
    st.metric(
        "Offender Contacts",
        f"{expected.get('estimated_ro_reduction', 0)}",
    )
with impact_cols[3]:
    st.metric(
        "Officers Needed",
        f"{expected.get('officers_needed', roi.get('additional_officers', 'N/A'))}",
    )
