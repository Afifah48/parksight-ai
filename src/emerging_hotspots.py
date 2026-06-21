"""Emerging Hotspot Detection — Phase 2.

Detects hotspots where violation frequency is accelerating or decelerating
by comparing recent vs prior weekly violation counts using a drift Z-score.

Formula (per hotspot):
    drift_score_raw = (mean_recent - mean_prior) / (stdev_prior + epsilon)

F3 FIX: Raw drift is capped at ±DRIFT_MAX_SCORE and then normalised to 0-100:
    drift_score = ((capped_raw + DRIFT_MAX_SCORE) / (2 * DRIFT_MAX_SCORE)) * 100
    drift_score_raw is preserved as a separate column for diagnostics.

F4 FIX: A hotspot with mean_weekly_recent < DRIFT_MIN_RECENT_MEAN cannot be
classified "Emerging" regardless of drift score — it becomes "Low Activity"
to prevent false alarms from dormant sites.

Classification (applied after F3/F4 guards):
    drift_score_raw >  DRIFT_EMERGING_THRESHOLD AND recent_mean >= MIN_RECENT_MEAN
        => status = "Emerging"
    drift_score_raw <  DRIFT_COOLING_THRESHOLD
        => status = "Cooling"
    mean_weekly_recent < DRIFT_MIN_RECENT_MEAN (and not Cooling)
        => status = "Low Activity"
    Otherwise
        => status = "Stable"

Hotspots with fewer than (DRIFT_RECENT_WEEKS + DRIFT_PRIOR_WEEKS) weeks of
history are classified as "Insufficient Data".

NOTE: DBSCAN unknown hotspots (398 clusters) are excluded from this analysis
because the cluster label is not stored in the cleaned record. Only 303 named
junction hotspots are analysed.

Input:  data/processed/cleaned_violations_full.csv
        data/processed/hotspot_summary.csv
Output: data/processed/emerging_hotspots.csv
"""

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import (
    DRIFT_COOLING_THRESHOLD,
    DRIFT_EMERGING_THRESHOLD,
    DRIFT_EPSILON,
    DRIFT_MAX_SCORE,
    DRIFT_MIN_RECENT_MEAN,
    DRIFT_PRIOR_WEEKS,
    DRIFT_RECENT_WEEKS,
    NO_JUNCTION_LABEL,
    VALID_STATUSES,
)

_MIN_WEEKS_REQUIRED = DRIFT_RECENT_WEEKS + DRIFT_PRIOR_WEEKS


def _safe_bool(value: object) -> bool:
    return str(value).strip().upper() in {"TRUE", "1", "YES"}


def _stdev_population(values: List[float]) -> float:
    """Population standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def _normalise_drift(raw: float) -> float:
    """Map raw drift from [-DRIFT_MAX_SCORE, +DRIFT_MAX_SCORE] to [0, 100].

    Values outside the cap are clipped before normalisation.
    Neutral (raw=0) maps to 50. Emerging maps toward 100, Cooling toward 0.
    """
    capped = max(-DRIFT_MAX_SCORE, min(DRIFT_MAX_SCORE, raw))
    return round((capped + DRIFT_MAX_SCORE) / (2.0 * DRIFT_MAX_SCORE) * 100.0, 2)


def _load_hotspot_index(hotspot_summary_path: Path) -> Dict[str, Dict[str, object]]:
    """Return a dict keyed by hotspot_id with all hotspot metadata."""
    index: Dict[str, Dict[str, object]] = {}
    if not hotspot_summary_path.exists():
        return index
    with hotspot_summary_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            index[str(row["hotspot_id"])] = dict(row)
    return index


def _resolve_hotspot_id(
    junction: str, station: str, name_to_id: Dict[Tuple[str, str], str]
) -> Optional[str]:
    """Map a cleaned record to a hotspot_id.

    Named records: key = (junction_name, police_station).
    Unknown records: not resolvable without the cluster label, so excluded.
    """
    if junction == NO_JUNCTION_LABEL:
        return None
    return name_to_id.get((junction, station))


def _load_name_to_id(hotspot_summary_path: Path) -> Dict[Tuple[str, str], str]:
    """Build (hotspot_name, police_station) -> hotspot_id mapping from summary."""
    mapping: Dict[Tuple[str, str], str] = {}
    if not hotspot_summary_path.exists():
        return mapping
    with hotspot_summary_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = (str(row.get("hotspot_name", "")), str(row.get("police_station", "")))
            mapping[key] = str(row.get("hotspot_id", ""))
    return mapping


def _sorted_weeks(week_counts: Dict[str, int]) -> List[Tuple[str, int]]:
    """Return (week_label, count) pairs sorted chronologically."""
    return sorted(week_counts.items(), key=lambda x: x[0])


def compute_emerging_hotspots(
    cleaned_full_path: Path,
    hotspot_summary_path: Path,
) -> List[Dict[str, object]]:
    """Compute per-hotspot drift scores and return classified output rows."""

    name_to_id = _load_name_to_id(hotspot_summary_path)
    hotspot_index = _load_hotspot_index(hotspot_summary_path)

    # weekly_counts[hotspot_id][week_label] = violation count
    weekly_counts: Dict[str, Counter] = defaultdict(Counter)
    all_weeks: List[str] = []

    # F6 FIX: Only count violations with valid statuses.
    valid_statuses_upper = {s.upper() for s in VALID_STATUSES}

    with cleaned_full_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            # F6: skip rejected / duplicate records
            status = str(row.get("validation_status", "")).strip().upper()
            if status not in valid_statuses_upper:
                continue

            junction = str(row.get("junction_name", "")).strip()
            station = str(row.get("police_station", "")).strip()
            week = str(row.get("week", "")).strip()

            if not week:
                continue

            all_weeks.append(week)

            hotspot_id = _resolve_hotspot_id(junction, station, name_to_id)
            if hotspot_id is None:
                continue

            weekly_counts[hotspot_id][week] += 1

    if not all_weeks:
        return []

    global_weeks_sorted = sorted(set(all_weeks))
    unknown_excluded = sum(
        1 for hid in hotspot_index if hid.startswith("U-")
    )

    output: List[Dict[str, object]] = []

    for hotspot_id, week_counter in weekly_counts.items():
        sorted_weeks_list = _sorted_weeks(week_counter)
        hotspot_weeks = [w for w, _ in sorted_weeks_list]

        # Build full week sequence for this hotspot across its active span.
        first_week = hotspot_weeks[0]
        last_week = hotspot_weeks[-1]
        active_global = [w for w in global_weeks_sorted if first_week <= w <= last_week]
        full_series = [(w, week_counter.get(w, 0)) for w in active_global]
        counts_series = [c for _, c in full_series]

        total_weeks_active = len(full_series)

        if total_weeks_active < _MIN_WEEKS_REQUIRED:
            drift_score_raw = 0.0
            drift_score = 50.0  # neutral normalised value for insufficient data
            status = "Insufficient Data"
            mean_recent = 0.0
            mean_prior = 0.0
            stdev_prior = 0.0
        else:
            # Most recent DRIFT_RECENT_WEEKS.
            recent_counts = [float(c) for c in counts_series[-DRIFT_RECENT_WEEKS:]]
            # Prior DRIFT_PRIOR_WEEKS immediately before the recent window.
            prior_start = -(DRIFT_RECENT_WEEKS + DRIFT_PRIOR_WEEKS)
            prior_end = -DRIFT_RECENT_WEEKS
            prior_counts = [float(c) for c in counts_series[prior_start:prior_end]]

            mean_recent = sum(recent_counts) / len(recent_counts) if recent_counts else 0.0
            mean_prior = sum(prior_counts) / len(prior_counts) if prior_counts else 0.0
            stdev_prior = _stdev_population(prior_counts)

            drift_score_raw = round(
                (mean_recent - mean_prior) / (stdev_prior + DRIFT_EPSILON), 4
            )
            # F3: normalise to 0-100
            drift_score = _normalise_drift(drift_score_raw)

            # Classify using raw Z-score thresholds.
            if drift_score_raw > DRIFT_EMERGING_THRESHOLD:
                # F4: gate on minimum absolute activity
                if mean_recent >= DRIFT_MIN_RECENT_MEAN:
                    status = "Emerging"
                else:
                    status = "Low Activity"
            elif drift_score_raw < DRIFT_COOLING_THRESHOLD:
                status = "Cooling"
            else:
                status = "Stable"

        meta = hotspot_index.get(hotspot_id, {})
        total_violations = sum(week_counter.values())
        week_labels = [w for w, _ in sorted_weeks_list]

        output.append({
            "hotspot_id": hotspot_id,
            "hotspot_name": meta.get("hotspot_name", ""),
            "hotspot_type": meta.get("hotspot_type", ""),
            "police_station": meta.get("police_station", ""),
            "latitude": meta.get("latitude", ""),
            "longitude": meta.get("longitude", ""),
            "total_violations": total_violations,
            "total_weeks_active": total_weeks_active,
            "first_active_week": week_labels[0] if week_labels else "",
            "last_active_week": week_labels[-1] if week_labels else "",
            "mean_weekly_recent": round(mean_recent, 4),
            "mean_weekly_prior": round(mean_prior, 4),
            "stdev_weekly_prior": round(stdev_prior, 4),
            "drift_score_raw": drift_score_raw,      # F3: raw unbounded Z-score (diagnostic)
            "drift_score": drift_score,               # F3: normalised 0-100
            "drift_status": status,
            "hotspot_severity": meta.get("hotspot_severity", ""),
            "pcis_score": "",  # joined by run_phase2.py if needed
        })

    # Sort: Emerging first (highest drift), Low Activity, Stable, Cooling, Insufficient.
    _STATUS_ORDER = {
        "Emerging": 0,
        "Low Activity": 1,
        "Stable": 2,
        "Cooling": 3,
        "Insufficient Data": 4,
    }

    def _sort_key(r: Dict[str, object]) -> Tuple[int, float]:
        s = str(r["drift_status"])
        raw = float(r["drift_score_raw"]) if r["drift_score_raw"] != "" else 0.0
        order = _STATUS_ORDER.get(s, 5)
        # Within each status sort by descending raw drift (most extreme first)
        return (order, -raw)

    output.sort(key=_sort_key)
    return output, unknown_excluded
