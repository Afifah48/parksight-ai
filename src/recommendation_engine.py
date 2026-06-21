"""
src/recommendation_engine.py
=============================
Presentation-layer rule engine for the Action Center.

ARCHITECTURE NOTE (from ARCHITECTURE.md):
    The recommendation engine is a presentation-layer rule engine, NOT a new
    analytical model. All heavy computation is done in the batch pipeline
    (Phases 1-3). This module reads pre-computed scores and applies deterministic
    rules to synthesise them into four recommendation types per station.

Four recommendation types
--------------------------
1. DEPLOY_PATROL
   Triggered when a station has >= 1 Critical hotspot with a patrol route.
   Attaches route_id, stop count, top-3 hotspot targets.

2. EMERGING_THREAT
   Triggered when drift_score >= 70 on an Emerging hotspot.
   Attaches drift delta, weekly violation trend, urgency level.

3. REPEAT_OFFENDER_INTERCEPTION
   Triggered when a station has >= 1 repeat offender with offender_score >= 50.
   Attaches vehicle list, target hotspots, interception window.

4. RESOURCE_ADVISORY
   Triggered for every Critical/High station.
   Attaches ROI scenario that best matches the station's hotspot count.

All outputs are plain dicts — the page renders them, not this module.
"""

from __future__ import annotations

import math
from typing import Optional

import pandas as pd
import streamlit as st

from src.data_service import (
    get_hotspots,
    get_emerging_hotspots,
    get_repeat_offenders,
    get_patrol_routes,
    get_roi_data,
    get_station_summary,
    list_stations,
)

# ---------------------------------------------------------------------------
# Rule thresholds (presentation layer — not analytical)
# ---------------------------------------------------------------------------
_DRIFT_ALERT_THRESHOLD    = 70.0   # drift_score >= this → Emerging alert card
_OFFENDER_SCORE_THRESHOLD = 50.0   # offender_score >= this → interception card
_CRITICAL_PRIORITY_MIN    = 50.0   # priority_score floor for "today's top action"
_MAX_TOP_ACTIONS          = 5      # action cards in "Today's Plan"
_MAX_PATROL_STOPS_SHOWN   = 5      # stops shown in deployment suggestion


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _truncate(text: str, max_len: int = 40) -> str:
    return text[:max_len] + "…" if len(text) > max_len else text


def _band_urgency(band: str) -> int:
    """Numeric urgency for sorting: Critical=4, High=3, Medium=2, Low=1."""
    return {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}.get(band, 0)


def _roi_scenario_for_hotspot_count(roi_df: pd.DataFrame, n_hotspots: int) -> dict:
    """
    Pick the ROI scenario whose hotspots_targeted is closest to n_hotspots.
    Falls back to S03 (10 officers, 30% target) if no match.
    """
    if roi_df.empty:
        return {}
    diffs = (roi_df["hotspots_targeted"] - n_hotspots).abs()
    idx   = diffs.idxmin()
    return roi_df.loc[idx].to_dict()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def generate_recommendations(station: Optional[str] = None) -> dict:
    """
    Generate all recommendation types, optionally scoped to one station.

    Returns
    -------
    dict with keys:
        top_actions         : list[dict]  — Today's Top 5 Actions
        emerging_alerts     : list[dict]  — Emerging Threat Alerts
        patrol_deployments  : list[dict]  — Officer Deployment Suggestions
        offender_targets    : list[dict]  — Repeat Offender Targets
        expected_impact     : dict        — ROI projection for this scope
        station_scope       : str         — 'All Stations' or the station name
        stations_at_risk    : list[dict]  — Highest-risk stations summary
    """
    # ------------------------------------------------------------------
    # Load all pre-computed data
    # ------------------------------------------------------------------
    hotspots_df  = get_hotspots(station=station)
    emerging_df  = get_emerging_hotspots(status="Emerging")
    ro_df        = get_repeat_offenders()
    routes_df    = get_patrol_routes(station=station)
    roi_df       = get_roi_data()
    station_df   = get_station_summary()

    if station:
        emerging_df = emerging_df[emerging_df["police_station"] == station].copy()
        ro_df = ro_df[
            ro_df["police_stations"].str.contains(station, na=False)
        ].copy()

    # ------------------------------------------------------------------
    # 1. TODAY'S TOP ACTIONS
    #    Rule: top Critical/High hotspots by priority_score,
    #    each with an action verb + reason sentence.
    # ------------------------------------------------------------------
    top_actions: list[dict] = []
    top_candidates = (
        hotspots_df[hotspots_df["priority_band"].isin(["Critical", "High"])]
        .sort_values("priority_score", ascending=False)
        .head(10)
    )

    for _, row in top_candidates.iterrows():
        drift_val   = float(row.get("drift_score", 0) or 0)
        drift_st    = str(row.get("drift_status", "Unknown"))
        pcis_val    = float(row.get("pcis_score", 0) or 0)
        band        = str(row.get("priority_band", ""))
        violations  = int(row.get("violation_count", 0) or 0)

        # Build reason sentence from dominant signal
        if drift_val >= _DRIFT_ALERT_THRESHOLD and drift_st == "Emerging":
            action_type = "🚨 URGENT DEPLOY"
            reason = (
                f"Violation rate accelerating — drift score {drift_val:.0f}/100. "
                f"Now averaging {float(row.get('mean_weekly_recent', 0) or 0):.1f} "
                f"violations/week vs prior baseline. "
                f"Immediate patrol deployment recommended."
            )
        elif pcis_val >= 80:
            action_type = "🔴 PRIORITY PATROL"
            reason = (
                f"High congestion impact (PCIS {pcis_val:.1f}/100). "
                f"{violations:,} violations recorded at this location. "
                f"Peak-hour enforcement will have highest effect."
            )
        elif float(row.get("repeat_offender_density_norm", 0) or 0) >= 70:
            action_type = "👤 OFFENDER SWEEP"
            reason = (
                f"High repeat offender density at this hotspot. "
                f"Station has disproportionate share of persistent violators. "
                f"Targeted vehicle interception recommended."
            )
        else:
            action_type = "🟠 ENFORCE"
            reason = (
                f"Ranked #{int(row.get('rank_city', 0) or 0)} city-wide "
                f"(priority score {float(row.get('priority_score', 0) or 0):.2f}). "
                f"Regular patrol coverage required."
            )

        top_actions.append({
            "hotspot_name":    str(row["hotspot_name"]),
            "police_station":  str(row["police_station"]),
            "priority_score":  float(row.get("priority_score", 0) or 0),
            "priority_band":   band,
            "pcis_score":      pcis_val,
            "drift_score":     drift_val,
            "drift_status":    drift_st,
            "violation_count": violations,
            "rank_city":       int(row.get("rank_city", 0) or 0),
            "action_type":     action_type,
            "reason":          reason,
        })
        if len(top_actions) >= _MAX_TOP_ACTIONS:
            break

    # ------------------------------------------------------------------
    # 2. EMERGING THREAT ALERTS
    #    Rule: Emerging hotspots with drift_score >= threshold.
    # ------------------------------------------------------------------
    emerging_alerts: list[dict] = []
    alert_candidates = emerging_df[
        emerging_df["drift_score"] >= _DRIFT_ALERT_THRESHOLD
    ].head(10)

    for _, row in alert_candidates.iterrows():
        drift_raw  = float(row.get("drift_score_raw", 0) or 0)
        recent_wk  = float(row.get("mean_weekly_recent", 0) or 0)
        prior_wk   = float(row.get("mean_weekly_prior", 0) or 0)
        drift_norm = float(row.get("drift_score", 0) or 0)

        pct_increase = (
            ((recent_wk - prior_wk) / prior_wk * 100) if prior_wk > 0 else 0
        )

        urgency = "CRITICAL" if drift_norm >= 95 else "HIGH" if drift_norm >= 80 else "ELEVATED"

        recommended_action = (
            "Deploy patrol immediately — violation rate is "
            f"{pct_increase:+.0f}% above prior 4-week baseline. "
            f"Focus on peak hours (08–10, 17–20). "
            f"Current rate: {recent_wk:.1f} violations/week."
        )

        # Find matching patrol route for this hotspot's station
        station_name = str(row.get("police_station", ""))
        station_routes = routes_df[
            routes_df["police_station"] == station_name
        ]["route_id"].unique().tolist()
        route_ref = station_routes[0] if station_routes else "No route assigned"

        emerging_alerts.append({
            "hotspot_name":         str(row["hotspot_name"]),
            "police_station":       station_name,
            "drift_score":          drift_norm,
            "drift_score_raw":      drift_raw,
            "mean_weekly_recent":   recent_wk,
            "mean_weekly_prior":    prior_wk,
            "pct_increase":         pct_increase,
            "urgency":              urgency,
            "recommended_action":   recommended_action,
            "patrol_route":         route_ref,
            "total_violations":     int(row.get("total_violations", 0) or 0),
        })

    # ------------------------------------------------------------------
    # 3. OFFICER DEPLOYMENT SUGGESTIONS
    #    Rule: Per station, group Critical hotspots and attach patrol route.
    # ------------------------------------------------------------------
    patrol_deployments: list[dict] = []

    station_scope_df = station_df.copy()
    if station:
        station_scope_df = station_scope_df[
            station_scope_df["police_station"] == station
        ]

    top_stations = station_scope_df[
        station_scope_df["critical_count"] > 0
    ].sort_values("max_priority", ascending=False).head(10)

    for _, srow in top_stations.iterrows():
        sname = str(srow["police_station"])
        critical_n = int(srow.get("critical_count", 0) or 0)
        total_n    = int(srow.get("total_hotspots", 0) or 0)

        # Patrol routes for this station
        stn_routes = routes_df[routes_df["police_station"] == sname]
        route_ids  = stn_routes["route_id"].unique().tolist()
        n_routes   = len(route_ids)

        # Officers recommended: 1 per route, min 1, max 5
        officers_rec = max(1, min(n_routes, 5))

        # Top 3 target hotspots from this station
        stn_hotspots = (
            hotspots_df[hotspots_df["police_station"] == sname]
            .sort_values("priority_score", ascending=False)
            .head(3)
        )
        targets = [
            {
                "name":     _truncate(str(h["hotspot_name"]), 35),
                "score":    float(h.get("priority_score", 0) or 0),
                "band":     str(h.get("priority_band", "")),
            }
            for _, h in stn_hotspots.iterrows()
        ]

        patrol_deployments.append({
            "police_station":    sname,
            "critical_hotspots": critical_n,
            "total_hotspots":    total_n,
            "patrol_routes":     route_ids[:3],  # show max 3 route IDs
            "n_routes":          n_routes,
            "officers_recommended": officers_rec,
            "target_hotspots":   targets,
            "max_priority":      float(srow.get("max_priority", 0) or 0),
            "deployment_note": (
                f"Assign {officers_rec} officer(s) across {n_routes} route(s). "
                f"Start at highest-priority hotspot in each route."
            ),
        })

    # ------------------------------------------------------------------
    # 4. REPEAT OFFENDER TARGETS
    #    Rule: Top offenders by score, with their hotspot locations.
    # ------------------------------------------------------------------
    offender_targets: list[dict] = []
    top_offenders = ro_df[
        ro_df["offender_score"] >= _OFFENDER_SCORE_THRESHOLD
    ].head(10)

    for _, row in top_offenders.iterrows():
        hotspot_list = [
            h.strip()
            for h in str(row.get("hotspot_names", "")).split("|")
            if h.strip()
        ]
        station_list = [
            s.strip()
            for s in str(row.get("police_stations", "")).split("|")
            if s.strip()
        ]
        last_seen = str(row.get("last_violation_date", "Unknown"))
        viol_count = int(row.get("total_violations", 0) or 0)
        span_days  = int(row.get("active_span_days", 0) or 0)
        peak_hr    = int(row.get("peak_hour_violations", 0) or 0)

        peak_pct = (peak_hr / viol_count * 100) if viol_count > 0 else 0

        intercept_note = (
            f"Last active {last_seen}. "
            f"Active across {len(hotspot_list)} location(s). "
        )
        if peak_pct >= 50:
            intercept_note += f"{peak_pct:.0f}% of violations during peak hours — deploy 08–10 or 17–20."
        else:
            intercept_note += "Violations spread across day — random patrol effective."

        offender_targets.append({
            "vehicle_number":       str(row["vehicle_number"]),
            "total_violations":     viol_count,
            "offender_score":       float(row.get("offender_score", 0) or 0),
            "distinct_hotspot_count": int(row.get("distinct_hotspot_count", 0) or 0),
            "hotspot_names":        hotspot_list,
            "police_stations":      station_list,
            "last_violation_date":  last_seen,
            "active_span_days":     span_days,
            "peak_hour_violations": peak_hr,
            "peak_pct":             peak_pct,
            "top_violation_type":   str(row.get("top_violation_type", "Unknown")),
            "intercept_note":       intercept_note,
        })

    # ------------------------------------------------------------------
    # 5. EXPECTED IMPACT
    #    Rule: pick ROI scenario whose hotspot count matches scope.
    # ------------------------------------------------------------------
    n_critical = int(hotspots_df[hotspots_df["priority_band"] == "Critical"].shape[0])
    roi_match  = _roi_scenario_for_hotspot_count(roi_df, n_critical)

    expected_impact = {
        "n_critical_in_scope":     n_critical,
        "n_hotspots_in_scope":     len(hotspots_df),
        "roi_scenario":            roi_match,
        "projected_pcis_reduction":
            float(roi_match.get("projected_pcis_reduction", 0) or 0),
        "projected_hotspot_reduction":
            int(roi_match.get("projected_hotspot_reduction_count", 0) or 0),
        "estimated_ro_reduction":
            int(roi_match.get("estimated_repeat_offender_reduction", 0) or 0),
        "officers_needed":
            int(roi_match.get("additional_officers", 0) or 0),
    }

    # ------------------------------------------------------------------
    # 6. STATIONS AT RISK (top 5 by max_priority)
    # ------------------------------------------------------------------
    stations_at_risk = []
    for _, srow in station_df.head(5).iterrows():
        stations_at_risk.append({
            "police_station":    str(srow["police_station"]),
            "max_priority":      float(srow.get("max_priority", 0) or 0),
            "critical_count":    int(srow.get("critical_count", 0) or 0),
            "emerging_count":    int(srow.get("emerging_count", 0) or 0),
            "total_violations":  int(srow.get("total_violations", 0) or 0),
            "repeat_offender_count": int(srow.get("repeat_offender_count", 0) or 0),
        })

    return {
        "top_actions":        top_actions,
        "emerging_alerts":    emerging_alerts,
        "patrol_deployments": patrol_deployments,
        "offender_targets":   offender_targets,
        "expected_impact":    expected_impact,
        "station_scope":      station if station else "All Stations",
        "stations_at_risk":   stations_at_risk,
    }
