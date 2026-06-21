"""
Enforcement Priority Engine
============================
Ranks hotspots for enforcement action by compositing four normalised signals:

    Priority Score = 0.40 * PCIS_score
                   + 0.25 * drift_score
                   + 0.20 * hotspot_severity_norm
                   + 0.15 * repeat_offender_density_norm

Weight rationale
----------------
- PCIS (0.40): The primary congestion-impact signal.  Already 0-100 and
  percentile-ranked, so it carries the most weight.
- Drift (0.25): Emerging hotspots require proactive enforcement before they
  become entrenched.  Stable / Cooling hotspots receive low drift scores.
- Hotspot severity (0.20): Captures raw violation volume and vehicle-mix
  effects not fully captured by PCIS.
- Repeat offender density (0.15): Concentrations of known repeat offenders
  at a hotspot indicate persistent non-compliance and higher enforcement
  payoff per patrol visit.

Inputs
------
- data/processed/pcis_scores.csv          (701 hotspots, all columns)
- data/processed/emerging_hotspots.csv    (302 named hotspots, drift_score)
- data/processed/repeat_offenders.csv     (287 vehicles, police_stations)
- data/processed/hotspot_summary.csv      (701 hotspots, hotspot_severity)

Output
------
- data/processed/enforcement_priorities.csv
"""

import csv
import math
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    PROCESSED_DIR,
    PHASE2_PCIS_CSV,
    PHASE2_EMERGING_HOTSPOTS_CSV,
    PHASE2_REPEAT_OFFENDERS_CSV,
)

HOTSPOT_SUMMARY_CSV = PROCESSED_DIR / "hotspot_summary.csv"
OUTPUT_CSV = PROCESSED_DIR / "enforcement_priorities.csv"

# ---------------------------------------------------------------------------
# Priority Score weights (must sum to 1.0)
# ---------------------------------------------------------------------------
EP_WEIGHT_PCIS           = 0.40
EP_WEIGHT_DRIFT          = 0.25
EP_WEIGHT_SEVERITY       = 0.20
EP_WEIGHT_REPEAT_DENSITY = 0.15

# Priority band thresholds (applied to priority_score 0-100)
# Top 15% -> Critical | 15-50th pct -> High | 50-80th pct -> Medium | bottom 20% -> Low
EP_BAND_CRITICAL_PCT = 85.0
EP_BAND_HIGH_PCT     = 50.0
EP_BAND_MEDIUM_PCT   = 20.0


def _safe_float(val, default=0.0):
    try:
        v = float(val)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def _percentile_threshold(values, pct):
    """Return the value at the given percentile (0-100) of a sorted list."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    idx = (pct / 100.0) * (len(sorted_vals) - 1)
    lo = int(idx)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def _min_max_norm(values):
    """Return a dict {key: normalised_0_to_100} using min-max normalisation."""
    if not values:
        return {}
    mn = min(values.values())
    mx = max(values.values())
    span = mx - mn
    if span == 0:
        return {k: 50.0 for k in values}
    return {k: (v - mn) / span * 100.0 for k, v in values.items()}


def load_pcis(path):
    """Load pcis_scores.csv -> dict keyed by hotspot_id."""
    hotspots = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            hid = row["hotspot_id"]
            hotspots[hid] = {
                "hotspot_id":     hid,
                "hotspot_type":   row["hotspot_type"],
                "hotspot_name":   row["hotspot_name"],
                "police_station": row["police_station"],
                "latitude":       _safe_float(row.get("latitude")),
                "longitude":      _safe_float(row.get("longitude")),
                "pcis_score":     _safe_float(row.get("pcis_score")),
                "pcis_band":      row.get("pcis_band", ""),
                "hotspot_severity": _safe_float(row.get("hotspot_severity")),
                # drift will be joined in below
                "drift_score":    0.0,
            }
    return hotspots


def load_drift(path):
    """Load emerging_hotspots.csv -> dict {hotspot_id: drift_score}."""
    drift = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            hid = row["hotspot_id"]
            # Only Emerging hotspots have positive drift; Stable/Cooling/etc = 0
            status = row.get("drift_status", "")
            raw_drift = _safe_float(row.get("drift_score"), 0.0)
            drift[hid] = raw_drift if status == "Emerging" else 0.0
    return drift


def load_repeat_offender_density(path):
    """
    Build repeat offender count per police_station from repeat_offenders.csv.
    Returns dict {police_station: offender_count}.
    A vehicle may appear under multiple stations (pipe-separated).
    """
    station_counts = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            for s in row.get("police_stations", "").split("|"):
                s = s.strip()
                if s:
                    station_counts[s] = station_counts.get(s, 0) + 1
    return station_counts


def compute_repeat_density_per_hotspot(hotspots, station_counts):
    """
    Assign each hotspot a repeat_offender_density value =
        offenders_in_station / hotspots_in_station
    This gives a per-hotspot share of repeat offender pressure.
    """
    # Count hotspots per station
    station_hotspot_count = {}
    for h in hotspots.values():
        s = h["police_station"]
        station_hotspot_count[s] = station_hotspot_count.get(s, 0) + 1

    density = {}
    for hid, h in hotspots.items():
        s = h["police_station"]
        n_offenders = station_counts.get(s, 0)
        n_hotspots  = station_hotspot_count.get(s, 1)
        density[hid] = n_offenders / n_hotspots
    return density


def assign_priority_band(score, thresholds):
    """Assign priority band label based on pre-computed score thresholds."""
    critical_t, high_t, medium_t = thresholds
    if score >= critical_t:
        return "Critical"
    elif score >= high_t:
        return "High"
    elif score >= medium_t:
        return "Medium"
    else:
        return "Low"


def run(pcis_path=None, drift_path=None, ro_path=None, output_path=None, verbose=True):
    """
    Main entry point for the enforcement priority engine.

    Returns a list of priority-ranked dicts (sorted descending by priority_score).
    """
    pcis_path   = pcis_path   or PHASE2_PCIS_CSV
    drift_path  = drift_path  or PHASE2_EMERGING_HOTSPOTS_CSV
    ro_path     = ro_path     or PHASE2_REPEAT_OFFENDERS_CSV
    output_path = output_path or OUTPUT_CSV

    # ------------------------------------------------------------------
    # 1. Load all inputs
    # ------------------------------------------------------------------
    if verbose:
        print("[EnforcementPriority] Loading PCIS scores …")
    hotspots = load_pcis(pcis_path)

    if verbose:
        print("[EnforcementPriority] Loading drift scores …")
    drift_map = load_drift(drift_path)
    for hid, ds in drift_map.items():
        if hid in hotspots:
            hotspots[hid]["drift_score"] = ds

    if verbose:
        print("[EnforcementPriority] Loading repeat offender counts …")
    station_ro_counts = load_repeat_offender_density(ro_path)

    # ------------------------------------------------------------------
    # 2. Compute per-hotspot repeat offender density (raw)
    # ------------------------------------------------------------------
    ro_density_raw = compute_repeat_density_per_hotspot(hotspots, station_ro_counts)

    # ------------------------------------------------------------------
    # 3. Normalise hotspot_severity to 0-100 across the full population
    # ------------------------------------------------------------------
    severity_raw  = {hid: h["hotspot_severity"] for hid, h in hotspots.items()}
    severity_norm = _min_max_norm(severity_raw)

    # ------------------------------------------------------------------
    # 4. Normalise repeat offender density to 0-100
    # ------------------------------------------------------------------
    ro_density_norm = _min_max_norm(ro_density_raw)

    # ------------------------------------------------------------------
    # 5. Compute composite Priority Score for each hotspot
    #    All inputs are already 0-100 at this stage.
    # ------------------------------------------------------------------
    for hid, h in hotspots.items():
        pcis_n     = h["pcis_score"]                   # already 0-100
        drift_n    = h["drift_score"]                  # already 0-100 (from emerging engine)
        severity_n = severity_norm.get(hid, 0.0)
        ro_n       = ro_density_norm.get(hid, 0.0)

        priority = (
            EP_WEIGHT_PCIS           * pcis_n +
            EP_WEIGHT_DRIFT          * drift_n +
            EP_WEIGHT_SEVERITY       * severity_n +
            EP_WEIGHT_REPEAT_DENSITY * ro_n
        )
        h["priority_score"]          = round(priority, 4)
        h["severity_norm"]           = round(severity_n, 4)
        h["repeat_offender_density_norm"] = round(ro_n, 4)

    # ------------------------------------------------------------------
    # 6. Compute priority band thresholds from score distribution
    # ------------------------------------------------------------------
    all_scores = [h["priority_score"] for h in hotspots.values()]
    critical_t = _percentile_threshold(all_scores, EP_BAND_CRITICAL_PCT)
    high_t     = _percentile_threshold(all_scores, EP_BAND_HIGH_PCT)
    medium_t   = _percentile_threshold(all_scores, EP_BAND_MEDIUM_PCT)
    thresholds = (critical_t, high_t, medium_t)

    for h in hotspots.values():
        h["priority_band"] = assign_priority_band(h["priority_score"], thresholds)

    # ------------------------------------------------------------------
    # 7. City-wide ranking (descending priority_score)
    # ------------------------------------------------------------------
    ranked_all = sorted(hotspots.values(), key=lambda x: -x["priority_score"])
    for city_rank, h in enumerate(ranked_all, start=1):
        h["rank_city"] = city_rank

    # ------------------------------------------------------------------
    # 8. Station-wise ranking
    # ------------------------------------------------------------------
    station_groups = {}
    for h in hotspots.values():
        s = h["police_station"]
        station_groups.setdefault(s, []).append(h)

    for station_list in station_groups.values():
        station_list.sort(key=lambda x: -x["priority_score"])
        for stn_rank, h in enumerate(station_list, start=1):
            h["rank_station"] = stn_rank

    # ------------------------------------------------------------------
    # 9. Write output CSV
    # ------------------------------------------------------------------
    fieldnames = [
        "hotspot_id",
        "hotspot_name",
        "police_station",
        "latitude",
        "longitude",
        "pcis_score",
        "drift_score",
        "severity_norm",
        "repeat_offender_density_norm",
        "priority_score",
        "priority_band",
        "rank_city",
        "rank_station",
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for h in ranked_all:
            writer.writerow(h)

    if verbose:
        band_counts = {}
        for h in ranked_all:
            b = h["priority_band"]
            band_counts[b] = band_counts.get(b, 0) + 1
        print(f"[EnforcementPriority] Scored {len(ranked_all)} hotspots.")
        print(f"[EnforcementPriority] Band breakdown:")
        for band in ("Critical", "High", "Medium", "Low"):
            print(f"    {band:10s}: {band_counts.get(band, 0)}")
        print(f"[EnforcementPriority] Score range: "
              f"min={min(all_scores):.2f}  max={max(all_scores):.2f}  "
              f"mean={sum(all_scores)/len(all_scores):.2f}")
        print(f"[EnforcementPriority] Output -> {output_path}")

    return ranked_all
