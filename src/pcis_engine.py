"""PCIS Scoring Engine — Phase 2.

Computes the Parking-Induced Congestion Impact Score (PCIS) for every hotspot.

PCIS is a weighted percentile-rank composite (0-100):

    PCIS = 0.30 * P(daily_density)
         + 0.25 * P(peak_hour_share)
         + 0.20 * P(large_vehicle_share)
         + 0.15 * P(main_road_violation_share)   [corrected keyword set — F1]
         + 0.10 * P(repeat_offender_ratio)

Where P(x) = percentile rank of x across all hotspots, 0-100.

F2 FIX: Bands are now assigned by percentile rank within the scored population,
not by fixed absolute PCIS thresholds (which produced zero "Low" band hotspots):
    Critical = top 15%  (pcis_score >= 85th percentile of population)
    High     = 50th–85th percentile
    Medium   = 20th–50th percentile
    Low      = bottom 20%

Input:  data/processed/hotspot_summary.csv
Output: data/processed/pcis_scores.csv
"""

import csv
from pathlib import Path
from typing import Dict, List, Sequence

from .config import (
    PCIS_BAND_CRITICAL_PCT,
    PCIS_BAND_HIGH_PCT,
    PCIS_BAND_MEDIUM_PCT,
    PCIS_WEIGHT_DAILY_DENSITY,
    PCIS_WEIGHT_LARGE_VEHICLE_SHARE,
    PCIS_WEIGHT_MAIN_ROAD_SHARE,
    PCIS_WEIGHT_PEAK_HOUR_SHARE,
    PCIS_WEIGHT_REPEAT_OFFENDER_RATIO,
)


def _percentile_rank(value: float, population: Sequence[float]) -> float:
    """Return the percentile rank (0-100) of value within population."""
    if not population:
        return 0.0
    lower_or_equal = sum(1 for v in population if v <= value)
    return round(100.0 * lower_or_equal / len(population), 4)


def _percentile_value(pct: float, sorted_values: List[float]) -> float:
    """Return the value at the given percentile (0-100) of a sorted list."""
    if not sorted_values:
        return 0.0
    idx = max(0, int(pct / 100.0 * len(sorted_values)) - 1)
    return sorted_values[idx]


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (ValueError, TypeError):
        return default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return default


def compute_pcis(hotspot_summary_path: Path) -> List[Dict[str, object]]:
    """Read hotspot_summary.csv and return rows with PCIS added.

    Each output row contains all original hotspot fields plus:
    - daily_density        : violation_count / active_days
    - repeat_offender_ratio: repeat_vehicle_count / unique_vehicle_count
    - pcis_daily_density   : percentile rank of daily_density
    - pcis_peak_hour       : percentile rank of peak_hour_share
    - pcis_large_vehicle   : percentile rank of large_vehicle_share
    - pcis_main_road       : percentile rank of main_road_violation_share
    - pcis_repeat_offender : percentile rank of repeat_offender_ratio
    - pcis_score           : final weighted composite (0-100)
    - pcis_percentile      : percentile rank of pcis_score within the population
    - pcis_band            : Critical / High / Medium / Low (percentile-based)
    """
    rows: List[Dict[str, object]] = []
    with hotspot_summary_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            violation_count = _safe_int(row.get("violation_count"), 0)
            active_days = _safe_int(row.get("active_days"), 1) or 1
            unique_vehicle_count = _safe_int(row.get("unique_vehicle_count"), 1) or 1
            repeat_vehicle_count = _safe_int(row.get("repeat_vehicle_count"), 0)

            daily_density = violation_count / active_days
            repeat_offender_ratio = repeat_vehicle_count / unique_vehicle_count

            rows.append({
                **row,
                "violation_count": violation_count,
                "active_days": active_days,
                "unique_vehicle_count": unique_vehicle_count,
                "repeat_vehicle_count": repeat_vehicle_count,
                "large_vehicle_share": _safe_float(row.get("large_vehicle_share")),
                "main_road_violation_share": _safe_float(row.get("main_road_violation_share")),
                "peak_hour_share": _safe_float(row.get("peak_hour_share")),
                "daily_density": daily_density,
                "repeat_offender_ratio": repeat_offender_ratio,
            })

    if not rows:
        return []

    # Build per-metric populations for percentile ranking.
    daily_densities = [float(r["daily_density"]) for r in rows]
    peak_hour_shares = [float(r["peak_hour_share"]) for r in rows]
    large_vehicle_shares = [float(r["large_vehicle_share"]) for r in rows]
    main_road_shares = [float(r["main_road_violation_share"]) for r in rows]
    repeat_ratios = [float(r["repeat_offender_ratio"]) for r in rows]

    # First pass: compute raw PCIS scores.
    scored: List[Dict[str, object]] = []
    for row in rows:
        p_density = _percentile_rank(float(row["daily_density"]), daily_densities)
        p_peak = _percentile_rank(float(row["peak_hour_share"]), peak_hour_shares)
        p_large = _percentile_rank(float(row["large_vehicle_share"]), large_vehicle_shares)
        p_main = _percentile_rank(float(row["main_road_violation_share"]), main_road_shares)
        p_repeat = _percentile_rank(float(row["repeat_offender_ratio"]), repeat_ratios)

        pcis = (
            PCIS_WEIGHT_DAILY_DENSITY * p_density
            + PCIS_WEIGHT_PEAK_HOUR_SHARE * p_peak
            + PCIS_WEIGHT_LARGE_VEHICLE_SHARE * p_large
            + PCIS_WEIGHT_MAIN_ROAD_SHARE * p_main
            + PCIS_WEIGHT_REPEAT_OFFENDER_RATIO * p_repeat
        )
        pcis = round(pcis, 2)

        scored.append({
            **row,
            "daily_density": round(float(row["daily_density"]), 4),
            "repeat_offender_ratio": round(float(row["repeat_offender_ratio"]), 4),
            "pcis_daily_density": p_density,
            "pcis_peak_hour": p_peak,
            "pcis_large_vehicle": p_large,
            "pcis_main_road": p_main,
            "pcis_repeat_offender": p_repeat,
            "pcis_score": pcis,
        })

    # F2 FIX: Assign bands by percentile rank within the scored population.
    # This guarantees all four bands are always populated regardless of
    # the absolute score range.
    all_pcis = sorted(float(r["pcis_score"]) for r in scored)
    critical_threshold = _percentile_value(PCIS_BAND_CRITICAL_PCT, all_pcis)
    high_threshold = _percentile_value(PCIS_BAND_HIGH_PCT, all_pcis)
    medium_threshold = _percentile_value(PCIS_BAND_MEDIUM_PCT, all_pcis)

    output: List[Dict[str, object]] = []
    for row in scored:
        score = float(row["pcis_score"])
        pct_rank = _percentile_rank(score, all_pcis)

        if score >= critical_threshold:
            band = "Critical"
        elif score >= high_threshold:
            band = "High"
        elif score >= medium_threshold:
            band = "Medium"
        else:
            band = "Low"

        output.append({
            **row,
            "pcis_percentile": round(pct_rank, 2),
            "pcis_band": band,
        })

    # Sort by descending PCIS score.
    output.sort(key=lambda r: float(r["pcis_score"]), reverse=True)
    return output
