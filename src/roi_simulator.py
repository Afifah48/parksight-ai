"""
ROI Simulator
=============
Estimates the enforcement impact of deploying additional officers to the
top-priority hotspots.

Transparent assumptions
-----------------------
A1. Baseline patrol visits per hotspot per month = 4 (1/week).
B1. Each additional officer adds 20 patrol visits per month across their
    assigned hotspots (5 visits/week × 4 weeks).
B2. Each officer patrols the N highest-priority hotspots in their station,
    where N = ceil(20 visits / visits_per_hotspot) with visits_per_hotspot = 4.
C1. Hotspot reduction rate per patrol visit = enforcement_intensity × 0.5%.
    enforcement_intensity is a 0-1 scalar supplied by the caller.
C2. Hotspot reduction is capped at 70% (a single station can never eliminate
    all violations; displacement and re-offending limits maximum impact).
C3. Repeat offender capture rate = 8% of repeat offenders per visited hotspot
    per patrol visit (literature-informed estimate for high-density urban
    enforcement; conservative).
D1. PCIS reduction is modelled as:
    DPCIS ≈ pcis_score × hotspot_reduction_pct × enforcement_intensity × 0.40
    (The 0.40 factor reflects that PCIS encodes multiple features; enforcement
    directly suppresses daily density but has partial effect on peak hour share,
    large vehicle share, etc.)
D2. Repeat offender reduction at city level is estimated as:
    captured = repeat_offenders_total × hotspot_reduction_pct × 0.08 × num_officers
    capped at repeat_offenders_total.

Scenario inputs (all normalised to [0, 1] or absolute counts)
--------------------------------------------------------------
- additional_officers   : int     number of extra officers deployed
- hotspot_reduction_pct : float   target reduction % (0.0–1.0), e.g. 0.20 = 20%
- enforcement_intensity : float   0.0 (low) to 1.0 (maximum) intensity

Output CSV columns
------------------
  scenario_id, additional_officers, hotspot_reduction_pct, enforcement_intensity,
  hotspots_targeted, projected_pcis_reduction, projected_hotspot_reduction_count,
  estimated_repeat_offender_reduction, patrol_visits_added_per_month,
  assumption_notes
"""

import csv
import math
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DIR

ENFORCEMENT_PRIORITIES_CSV = PROCESSED_DIR / "enforcement_priorities.csv"
REPEAT_OFFENDERS_CSV       = PROCESSED_DIR / "repeat_offenders.csv"
OUTPUT_CSV                 = PROCESSED_DIR / "roi_simulation.csv"

# ---------------------------------------------------------------------------
# Model constants (see module docstring for rationale)
# ---------------------------------------------------------------------------
BASELINE_VISITS_PER_HOTSPOT_PER_MONTH = 4   # A1
OFFICER_VISITS_PER_MONTH              = 20  # B1
REDUCTION_PER_VISIT_PER_INTENSITY     = 0.005  # C1: 0.5% per visit at intensity=1
MAX_HOTSPOT_REDUCTION_CAP             = 0.70   # C2
RO_CAPTURE_RATE_PER_HOTSPOT_PER_VISIT = 0.08  # C3
PCIS_ENFORCEMENT_FACTOR               = 0.40  # D1


def _safe_float(val, default=0.0):
    try:
        v = float(val)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def load_priorities(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append({
                "hotspot_id":     row["hotspot_id"],
                "hotspot_name":   row["hotspot_name"],
                "police_station": row["police_station"],
                "pcis_score":     _safe_float(row.get("pcis_score")),
                "priority_score": _safe_float(row.get("priority_score")),
            })
    return rows


def load_repeat_offender_count(path):
    count = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for _ in csv.DictReader(fh):
            count += 1
    return count


def simulate_scenario(
    priorities,
    repeat_offender_count,
    additional_officers,
    hotspot_reduction_pct,
    enforcement_intensity,
    scenario_id,
):
    """
    Run one ROI scenario.

    Parameters
    ----------
    priorities              : list of hotspot dicts (sorted desc by priority_score)
    repeat_offender_count   : int  total repeat offenders in the dataset
    additional_officers     : int
    hotspot_reduction_pct   : float  0.0–1.0
    enforcement_intensity   : float  0.0–1.0
    scenario_id             : str or int

    Returns a dict with all output fields.
    """
    # Clamp inputs
    enforcement_intensity = max(0.0, min(1.0, enforcement_intensity))
    hotspot_reduction_pct = max(0.0, min(MAX_HOTSPOT_REDUCTION_CAP, hotspot_reduction_pct))
    additional_officers   = max(0, int(additional_officers))

    total_hotspots = len(priorities)

    # --- B: Patrol visits added per month ---
    patrol_visits_added = additional_officers * OFFICER_VISITS_PER_MONTH

    # --- B2: Hotspots targeted ---
    # Each officer covers N hotspots at BASELINE_VISITS_PER_HOTSPOT_PER_MONTH rate
    hotspots_per_officer = math.ceil(
        OFFICER_VISITS_PER_MONTH / BASELINE_VISITS_PER_HOTSPOT_PER_MONTH
    )
    hotspots_targeted = min(
        additional_officers * hotspots_per_officer,
        total_hotspots,
    )

    # --- C: Effective hotspot reduction ---
    # Actual per-hotspot reduction from visits:
    visits_per_hotspot = patrol_visits_added / max(hotspots_targeted, 1)
    reduction_from_visits = (
        visits_per_hotspot
        * REDUCTION_PER_VISIT_PER_INTENSITY
        * enforcement_intensity
    )
    # Combined with caller-supplied target rate (take higher of the two)
    effective_reduction = max(reduction_from_visits, hotspot_reduction_pct)
    effective_reduction = min(effective_reduction, MAX_HOTSPOT_REDUCTION_CAP)

    # Projected hotspot reduction COUNT = targeted hotspots × effective_reduction
    projected_hotspot_reduction_count = round(hotspots_targeted * effective_reduction)

    # --- D1: Projected PCIS reduction ---
    # Average PCIS of targeted (top) hotspots
    targeted_hotspots = priorities[:hotspots_targeted]
    if targeted_hotspots:
        mean_pcis = sum(h["pcis_score"] for h in targeted_hotspots) / len(targeted_hotspots)
    else:
        mean_pcis = 0.0
    projected_pcis_reduction = round(
        mean_pcis * effective_reduction * enforcement_intensity * PCIS_ENFORCEMENT_FACTOR,
        2,
    )

    # --- D2: Repeat offender reduction ---
    ro_reduction = (
        repeat_offender_count
        * effective_reduction
        * RO_CAPTURE_RATE_PER_HOTSPOT_PER_VISIT
        * additional_officers
    )
    estimated_ro_reduction = min(round(ro_reduction), repeat_offender_count)

    assumption_notes = (
        f"A1:baseline={BASELINE_VISITS_PER_HOTSPOT_PER_MONTH}v/hotspot/mo; "
        f"B1:{OFFICER_VISITS_PER_MONTH}v/officer/mo; "
        f"C1:{REDUCTION_PER_VISIT_PER_INTENSITY*100:.1f}%/visit@intensity=1; "
        f"C2:cap={MAX_HOTSPOT_REDUCTION_CAP*100:.0f}%; "
        f"C3:RO_capture={RO_CAPTURE_RATE_PER_HOTSPOT_PER_VISIT*100:.0f}%/hotspot/visit; "
        f"D1:PCIS_factor={PCIS_ENFORCEMENT_FACTOR}"
    )

    return {
        "scenario_id":                        scenario_id,
        "additional_officers":                additional_officers,
        "hotspot_reduction_pct":              round(hotspot_reduction_pct * 100, 1),
        "enforcement_intensity":              round(enforcement_intensity, 2),
        "hotspots_targeted":                  hotspots_targeted,
        "patrol_visits_added_per_month":      patrol_visits_added,
        "effective_reduction_pct":            round(effective_reduction * 100, 1),
        "projected_pcis_reduction":           projected_pcis_reduction,
        "projected_hotspot_reduction_count":  projected_hotspot_reduction_count,
        "estimated_repeat_offender_reduction": estimated_ro_reduction,
        "assumption_notes":                   assumption_notes,
    }


# ---------------------------------------------------------------------------
# Default scenario grid
# ---------------------------------------------------------------------------
DEFAULT_SCENARIOS = [
    # (additional_officers, hotspot_reduction_pct, enforcement_intensity)
    (2,  0.10, 0.5),   # Light: 2 extra officers, 10% target, medium intensity
    (5,  0.20, 0.7),   # Moderate: 5 officers, 20% target, high intensity
    (10, 0.30, 0.8),   # Heavy: 10 officers, 30% target, high intensity
    (15, 0.40, 1.0),   # Aggressive: 15 officers, 40% target, full intensity
    (20, 0.50, 1.0),   # Maximum: 20 officers, 50% target, full intensity
    (3,  0.15, 0.6),   # Balanced: 3 officers, 15% target, moderate intensity
    (7,  0.25, 0.8),   # Targeted: 7 officers, 25% target, high intensity
    (10, 0.20, 0.5),   # Volume: 10 officers, 20% target, medium intensity
]


def run(
    priorities_path=None,
    ro_path=None,
    output_path=None,
    scenarios=None,
    verbose=True,
):
    """
    Main entry point for the ROI simulator.

    Parameters
    ----------
    scenarios : list of (additional_officers, hotspot_reduction_pct, enforcement_intensity)
                If None, uses DEFAULT_SCENARIOS.

    Returns list of scenario result dicts.
    """
    priorities_path = priorities_path or ENFORCEMENT_PRIORITIES_CSV
    ro_path         = ro_path         or REPEAT_OFFENDERS_CSV
    output_path     = output_path     or OUTPUT_CSV
    scenarios       = scenarios       or DEFAULT_SCENARIOS

    if verbose:
        print("[ROISimulator] Loading enforcement priorities …")
    priorities = load_priorities(priorities_path)

    if verbose:
        print("[ROISimulator] Loading repeat offender count …")
    ro_count = load_repeat_offender_count(ro_path)

    if verbose:
        print(f"[ROISimulator] Total hotspots: {len(priorities)}, repeat offenders: {ro_count}")
        print(f"[ROISimulator] Running {len(scenarios)} scenarios …")

    results = []
    for i, (officers, red_pct, intensity) in enumerate(scenarios, start=1):
        result = simulate_scenario(
            priorities            = priorities,
            repeat_offender_count = ro_count,
            additional_officers   = officers,
            hotspot_reduction_pct = red_pct,
            enforcement_intensity = intensity,
            scenario_id           = f"S{i:02d}",
        )
        results.append(result)

    # ------------------------------------------------------------------
    # Write CSV
    # ------------------------------------------------------------------
    fieldnames = [
        "scenario_id",
        "additional_officers",
        "hotspot_reduction_pct",
        "enforcement_intensity",
        "hotspots_targeted",
        "patrol_visits_added_per_month",
        "effective_reduction_pct",
        "projected_pcis_reduction",
        "projected_hotspot_reduction_count",
        "estimated_repeat_offender_reduction",
        "assumption_notes",
    ]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    if verbose:
        print(f"[ROISimulator] {len(results)} scenarios written -> {output_path}")
        print()
        print("  {:<6} {:>8} {:>12} {:>12} {:>12} {:>14} {:>14}".format(
            "ID", "Officers", "Target%", "Intensity", "Hotspots", "DPCIS", "DOffenders"
        ))
        print("  " + "-" * 84)
        for r in results:
            print("  {:<6} {:>8} {:>12} {:>12} {:>12} {:>14} {:>14}".format(
                r["scenario_id"],
                r["additional_officers"],
                f"{r['hotspot_reduction_pct']}%",
                r["enforcement_intensity"],
                r["hotspots_targeted"],
                f"-{r['projected_pcis_reduction']}",
                f"-{r['estimated_repeat_offender_reduction']}",
            ))

    return results
