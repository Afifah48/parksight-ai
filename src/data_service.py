"""
data_service.py
===============
Centralised data access layer for the Phase 4 Streamlit application.

All pre-computed CSVs are loaded once at startup via @st.cache_data and held
in memory for the lifetime of the Streamlit session.  Pages call the query
functions below — they do NOT load CSVs themselves.

CSV sources (all in data/processed/):
    enforcement_priorities.csv   — 701 hotspots, priority scores + bands
    pcis_scores.csv              — 701 hotspots, PCIS components
    emerging_hotspots.csv        — 302 named hotspots, drift status
    repeat_offenders.csv         — 287 vehicles, offender scores
    patrol_routes.csv            — 97 routes / 701 stops
    roi_simulation.csv           — 8 ROI scenarios
    hotspot_summary.csv          — 701 hotspots, raw violation counts
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Paths — derived from this file's location so they work on any machine.
# ---------------------------------------------------------------------------
_SRC_DIR      = Path(__file__).resolve().parent
_PROJECT_ROOT = _SRC_DIR.parent
_PROCESSED    = _PROJECT_ROOT / "data" / "processed"

_ENFORCEMENT_PRIORITIES_CSV = _PROCESSED / "enforcement_priorities.csv"
_PCIS_SCORES_CSV            = _PROCESSED / "pcis_scores.csv"
_EMERGING_HOTSPOTS_CSV      = _PROCESSED / "emerging_hotspots.csv"
_REPEAT_OFFENDERS_CSV       = _PROCESSED / "repeat_offenders.csv"
_PATROL_ROUTES_CSV          = _PROCESSED / "patrol_routes.csv"
_ROI_SIMULATION_CSV         = _PROCESSED / "roi_simulation.csv"
_HOTSPOT_SUMMARY_CSV        = _PROCESSED / "hotspot_summary.csv"


# ---------------------------------------------------------------------------
# Internal loaders — cached at the Streamlit session level.
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _load_enforcement_priorities() -> pd.DataFrame:
    df = pd.read_csv(_ENFORCEMENT_PRIORITIES_CSV)
    for col in ["latitude", "longitude", "priority_score", "pcis_score",
                "drift_score", "rank_city", "rank_station",
                "severity_norm", "repeat_offender_density_norm"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def _load_pcis_scores() -> pd.DataFrame:
    df = pd.read_csv(_PCIS_SCORES_CSV)
    numeric_cols = [
        "violation_count", "unique_vehicle_count", "repeat_vehicle_count",
        "large_vehicle_share", "main_road_violation_share", "peak_hour_share",
        "active_days", "daily_density", "repeat_offender_ratio",
        "pcis_daily_density", "pcis_peak_hour", "pcis_large_vehicle",
        "pcis_main_road", "pcis_repeat_offender", "pcis_score",
        "pcis_percentile", "hotspot_severity", "latitude", "longitude",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def _load_emerging_hotspots() -> pd.DataFrame:
    df = pd.read_csv(_EMERGING_HOTSPOTS_CSV)
    for col in ["drift_score", "drift_score_raw", "mean_weekly_recent",
                "mean_weekly_prior", "stdev_weekly_prior", "hotspot_severity",
                "total_violations", "latitude", "longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def _load_repeat_offenders() -> pd.DataFrame:
    df = pd.read_csv(_REPEAT_OFFENDERS_CSV)
    for col in ["total_violations", "distinct_hotspot_count",
                "active_span_days", "peak_hour_violations",
                "offender_score_raw", "offender_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["large_vehicle"] = (
        df["large_vehicle"].astype(str).str.lower()
        .map({"true": True, "false": False})
        .fillna(False)
    )
    return df


@st.cache_data(show_spinner=False)
def _load_patrol_routes() -> pd.DataFrame:
    df = pd.read_csv(_PATROL_ROUTES_CSV)
    for col in ["stop_order", "priority_score", "distance_from_prev_km",
                "latitude", "longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def _load_roi_simulation() -> pd.DataFrame:
    df = pd.read_csv(_ROI_SIMULATION_CSV)
    for col in ["additional_officers", "hotspot_reduction_pct",
                "enforcement_intensity", "hotspots_targeted",
                "patrol_visits_added_per_month", "effective_reduction_pct",
                "projected_pcis_reduction", "projected_hotspot_reduction_count",
                "estimated_repeat_offender_reduction"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def _load_hotspot_summary() -> pd.DataFrame:
    df = pd.read_csv(_HOTSPOT_SUMMARY_CSV)
    for col in ["violation_count", "unique_vehicle_count", "repeat_vehicle_count",
                "large_vehicle_share", "main_road_violation_share",
                "peak_hour_share", "active_days", "hotspot_severity",
                "latitude", "longitude"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Public query API
# ---------------------------------------------------------------------------

def get_hotspots(
    station: Optional[str] = None,
    band: Optional[str] = None,
    hotspot_type: Optional[str] = None,
) -> pd.DataFrame:
    """
    Return enforcement_priorities joined with pcis_scores and emerging status.

    Parameters
    ----------
    station      : Filter to a single police_station (None = all).
    band         : Filter to a priority_band ('Critical'/'High'/'Medium'/'Low').
    hotspot_type : Filter to hotspot_type ('Named Junction'/'Discovered Unknown').
    """
    priorities = _load_enforcement_priorities().copy()
    pcis = _load_pcis_scores()[
        ["hotspot_id", "hotspot_type", "violation_count", "unique_vehicle_count",
         "repeat_vehicle_count", "large_vehicle_share", "main_road_violation_share",
         "peak_hour_share", "active_days", "hotspot_severity",
         "top_violation_type", "pcis_band"]
    ]
    emerging = _load_emerging_hotspots()[
        ["hotspot_id", "drift_status", "mean_weekly_recent", "mean_weekly_prior"]
    ]

    df = priorities.merge(pcis, on="hotspot_id", how="left")
    df = df.merge(emerging, on="hotspot_id", how="left")
    df["drift_status"] = df["drift_status"].fillna("Unknown")
    df["hotspot_type"] = df["hotspot_type"].fillna("Discovered Unknown")

    if station:
        df = df[df["police_station"] == station]
    if band:
        df = df[df["priority_band"] == band]
    if hotspot_type:
        df = df[df["hotspot_type"] == hotspot_type]

    return df.reset_index(drop=True)


def get_priority_hotspots(
    top_n: int = 20,
    station: Optional[str] = None,
) -> pd.DataFrame:
    """Return the top-N hotspots by priority_score, optionally scoped to a station."""
    df = get_hotspots(station=station)
    return df.sort_values("priority_score", ascending=False).head(top_n).reset_index(drop=True)


def get_emerging_hotspots(status: str = "Emerging") -> pd.DataFrame:
    """
    Return emerging hotspot records filtered by drift_status.
    Values: 'Emerging', 'Cooling', 'Stable', 'Low Activity', 'Insufficient Data'.
    """
    df = _load_emerging_hotspots().copy()
    return (
        df[df["drift_status"] == status]
        .sort_values("drift_score", ascending=False)
        .reset_index(drop=True)
    )


def get_repeat_offenders(top_n: Optional[int] = None) -> pd.DataFrame:
    """Return repeat offenders sorted by offender_score descending."""
    df = _load_repeat_offenders().sort_values("offender_score", ascending=False)
    if top_n:
        df = df.head(top_n)
    return df.reset_index(drop=True)


def get_patrol_routes(station: Optional[str] = None) -> pd.DataFrame:
    """Return patrol route stops, optionally filtered to a station."""
    df = _load_patrol_routes().copy()
    if station:
        df = df[df["police_station"] == station]
    return df.sort_values(["route_id", "stop_order"]).reset_index(drop=True)


def get_station_summary() -> pd.DataFrame:
    """
    Aggregate enforcement priority data by police_station.

    Returns one row per station with:
        total_hotspots, critical_count, high_count, medium_count, low_count,
        emerging_count, avg_priority, max_priority, total_violations,
        repeat_offender_count
    """
    df = get_hotspots()
    emerging_df = _load_emerging_hotspots()

    emerging_counts = (
        emerging_df[emerging_df["drift_status"] == "Emerging"]
        .groupby("police_station")
        .size()
        .reset_index(name="emerging_count")
    )

    agg = df.groupby("police_station").agg(
        total_hotspots   =("hotspot_id",      "count"),
        critical_count   =("priority_band",   lambda x: (x == "Critical").sum()),
        high_count       =("priority_band",   lambda x: (x == "High").sum()),
        medium_count     =("priority_band",   lambda x: (x == "Medium").sum()),
        low_count        =("priority_band",   lambda x: (x == "Low").sum()),
        avg_priority     =("priority_score",  "mean"),
        max_priority     =("priority_score",  "max"),
        total_violations =("violation_count", "sum"),
    ).reset_index()

    agg = agg.merge(emerging_counts, on="police_station", how="left")
    agg["emerging_count"] = agg["emerging_count"].fillna(0).astype(int)
    agg["avg_priority"]   = agg["avg_priority"].round(2)
    agg["max_priority"]   = agg["max_priority"].round(2)

    # Repeat offender count per station
    ro = _load_repeat_offenders()
    if "police_stations" in ro.columns:
        ro_counts: dict[str, int] = {}
        for _, row in ro.iterrows():
            for s in str(row["police_stations"]).split("|"):
                s = s.strip()
                if s:
                    ro_counts[s] = ro_counts.get(s, 0) + 1
        ro_df = pd.DataFrame(
            list(ro_counts.items()), columns=["police_station", "repeat_offender_count"]
        )
        agg = agg.merge(ro_df, on="police_station", how="left")
        agg["repeat_offender_count"] = agg["repeat_offender_count"].fillna(0).astype(int)
    else:
        agg["repeat_offender_count"] = 0

    return agg.sort_values("max_priority", ascending=False).reset_index(drop=True)


def get_roi_data() -> pd.DataFrame:
    """Return all ROI simulation scenarios."""
    return _load_roi_simulation().copy()


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def list_stations() -> list:
    """Return sorted list of all police stations."""
    df = _load_enforcement_priorities()
    return sorted(df["police_station"].dropna().unique().tolist())


def list_bands() -> list:
    """Return priority bands in severity order."""
    return ["Critical", "High", "Medium", "Low"]


def city_kpis() -> dict:
    """
    Return a dict of top-level KPI values for the Command Center.

    Keys: total_hotspots, critical_hotspots, emerging_hotspots,
          repeat_offenders, patrol_routes, total_violations,
          top_station, top_hotspot_name, top_priority_score
    """
    priorities = _load_enforcement_priorities()
    emerging   = _load_emerging_hotspots()
    ro         = _load_repeat_offenders()
    routes     = _load_patrol_routes()

    emerging_count = int((emerging["drift_status"] == "Emerging").sum())
    route_count    = int(routes["route_id"].nunique()) if "route_id" in routes.columns else 0

    top_row = priorities.sort_values("priority_score", ascending=False).iloc[0]

    station_risk = (
        priorities.groupby("police_station")["priority_score"]
        .mean()
        .idxmax()
    )

    total_violations = int(_load_pcis_scores()["violation_count"].sum())

    return {
        "total_hotspots":     int(len(priorities)),
        "critical_hotspots":  int((priorities["priority_band"] == "Critical").sum()),
        "emerging_hotspots":  emerging_count,
        "repeat_offenders":   int(len(ro)),
        "patrol_routes":      route_count,
        "total_violations":   total_violations,
        "top_station":        str(station_risk),
        "top_hotspot_name":   str(top_row["hotspot_name"]),
        "top_priority_score": float(round(top_row["priority_score"], 2)),
    }
