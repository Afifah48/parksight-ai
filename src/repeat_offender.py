"""Repeat Offender Intelligence — Phase 2.

Identifies vehicles that appear repeatedly across multiple hotspots, suggesting
habitual parking violations that defeat one-off enforcement.

A vehicle is flagged as a repeat offender when it meets ALL of:
- Total violations >= REPEAT_OFFENDER_MIN_VIOLATIONS (F5: raised from 5 to 8)
- Distinct hotspots visited >= REPEAT_OFFENDER_MIN_HOTSPOTS (default 2)

F5 FIX: offender_score_raw is normalised to 0-100 as offender_score using
min-max normalisation across the flagged population. Raw value is preserved
as offender_score_raw for diagnostics.

F6 FIX: Records with validation_status in {REJECTED, DUPLICATE} are excluded
from all counting. Only APPROVED, PROCESSING, and UNKNOWN statuses contribute.

For each flagged vehicle the output records:
- vehicle_number
- total_violations       : count of valid-status violations
- distinct_hotspot_count : number of distinct named/unknown hotspots visited
- hotspot_names          : pipe-separated list of hotspot names
- police_stations        : pipe-separated list of police stations
- first_violation_date   : earliest date string
- last_violation_date    : latest date string
- active_span_days       : last - first in calendar days
- peak_hour_violations   : count of violations during peak hours
- large_vehicle          : True if vehicle_type triggered large-vehicle flag
- top_violation_type     : most common violation type for this vehicle
- offender_score_raw     : violations * log2(distinct_hotspots + 1)
- offender_score         : min-max normalised to 0-100

Input:  data/processed/cleaned_violations_full.csv
        data/processed/hotspot_summary.csv
Output: data/processed/repeat_offenders.csv
"""

import csv
import math
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .config import (
    NO_JUNCTION_LABEL,
    REPEAT_OFFENDER_MIN_HOTSPOTS,
    REPEAT_OFFENDER_MIN_VIOLATIONS,
    VALID_STATUSES,
)


def _parse_date(value: str) -> Optional[date]:
    raw = value.strip()[:10]  # take YYYY-MM-DD portion
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def _safe_bool(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "1", "YES"}


def _minmax_normalise(values: List[float]) -> List[float]:
    """Min-max normalise a list to [0, 100]. Handles all-equal case."""
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi == lo:
        return [100.0] * len(values)
    return [round((v - lo) / (hi - lo) * 100.0, 2) for v in values]


def compute_repeat_offenders(
    cleaned_full_path: Path,
    hotspot_summary_path: Path,
) -> List[Dict[str, object]]:
    """Scan cleaned_violations_full.csv and return repeat offender records."""

    valid_statuses_upper = {s.upper() for s in VALID_STATUSES}

    # ------------------------------------------------------------------
    # Aggregation structure per vehicle
    # ------------------------------------------------------------------
    vehicle_total: Counter = Counter()
    vehicle_hotspot_ids: Dict[str, Set[str]] = defaultdict(set)
    vehicle_hotspot_names: Dict[str, Set[str]] = defaultdict(set)
    vehicle_stations: Dict[str, Set[str]] = defaultdict(set)
    vehicle_dates: Dict[str, List[date]] = defaultdict(list)
    vehicle_peak: Counter = Counter()
    vehicle_large: Dict[str, bool] = {}
    vehicle_violation_types: Dict[str, Counter] = defaultdict(Counter)

    with cleaned_full_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            # F6: exclude REJECTED and DUPLICATE records.
            status = str(row.get("validation_status", "")).strip().upper()
            if status not in valid_statuses_upper:
                continue

            vehicle = str(row.get("vehicle_number", "")).strip()
            if not vehicle or vehicle.upper() in {"", "UNKNOWN"}:
                continue

            junction = str(row.get("junction_name", "")).strip()
            station = str(row.get("police_station", "")).strip()
            dt_str = str(row.get("date", "")).strip()
            is_peak = _safe_bool(row.get("is_peak_hour"))
            is_large = _safe_bool(row.get("is_large_vehicle"))
            violation_type = str(row.get("violation_type", "")).strip()

            vehicle_total[vehicle] += 1

            # Resolve hotspot reference.
            # Named junctions matched directly by junction_name + station.
            # Unknown (No Junction) records grouped by station as a proxy.
            if junction != NO_JUNCTION_LABEL:
                vehicle_hotspot_names[vehicle].add(junction)
                vehicle_hotspot_ids[vehicle].add(f"N:{junction}:{station}")
            else:
                vehicle_hotspot_names[vehicle].add(f"[Unknown]:{station}")
                vehicle_hotspot_ids[vehicle].add(f"U:{station}")

            vehicle_stations[vehicle].add(station)

            d = _parse_date(dt_str)
            if d:
                vehicle_dates[vehicle].append(d)

            if is_peak:
                vehicle_peak[vehicle] += 1

            if vehicle not in vehicle_large:
                vehicle_large[vehicle] = False
            if is_large:
                vehicle_large[vehicle] = True

            if violation_type:
                for vt in violation_type.split("; "):
                    vt = vt.strip()
                    if vt:
                        vehicle_violation_types[vehicle][vt] += 1

    # ------------------------------------------------------------------
    # Filter and build raw output rows
    # ------------------------------------------------------------------
    raw_output: List[Dict[str, object]] = []

    for vehicle, total in vehicle_total.items():
        # F5: raised threshold
        if total < REPEAT_OFFENDER_MIN_VIOLATIONS:
            continue
        distinct_hotspots = len(vehicle_hotspot_ids[vehicle])
        if distinct_hotspots < REPEAT_OFFENDER_MIN_HOTSPOTS:
            continue

        dates = sorted(vehicle_dates[vehicle])
        first_date = dates[0].isoformat() if dates else ""
        last_date = dates[-1].isoformat() if dates else ""
        span_days = (dates[-1] - dates[0]).days if len(dates) >= 2 else 0

        top_vt = ""
        if vehicle_violation_types[vehicle]:
            top_vt = vehicle_violation_types[vehicle].most_common(1)[0][0]

        # Raw score: violations * log2(distinct_hotspots + 1)
        offender_score_raw = round(total * math.log2(distinct_hotspots + 1), 4)

        raw_output.append({
            "vehicle_number": vehicle,
            "total_violations": total,
            "distinct_hotspot_count": distinct_hotspots,
            "hotspot_names": " | ".join(sorted(vehicle_hotspot_names[vehicle])),
            "police_stations": " | ".join(sorted(vehicle_stations[vehicle])),
            "first_violation_date": first_date,
            "last_violation_date": last_date,
            "active_span_days": span_days,
            "peak_hour_violations": vehicle_peak[vehicle],
            "large_vehicle": vehicle_large.get(vehicle, False),
            "top_violation_type": top_vt,
            "offender_score_raw": offender_score_raw,
        })

    if not raw_output:
        return []

    # F5: Normalise offender_score to 0-100 via min-max across the flagged population.
    raw_scores = [float(r["offender_score_raw"]) for r in raw_output]
    normalised = _minmax_normalise(raw_scores)

    output: List[Dict[str, object]] = []
    for row, norm_score in zip(raw_output, normalised):
        output.append({
            **row,
            "offender_score": norm_score,
        })

    # Sort by descending normalised offender_score.
    output.sort(key=lambda r: float(r["offender_score"]), reverse=True)
    return output
