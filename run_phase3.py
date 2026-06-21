"""
Phase 3 Batch Entry Point
=========================
Orchestrates:
  1. Enforcement Priority Engine  -> data/processed/enforcement_priorities.csv
  2. Patrol Route Planner         -> data/processed/patrol_routes.csv
  3. ROI Simulator                -> data/processed/roi_simulation.csv
  4. Phase 3 summary report       -> reports/phase3_summary.txt

Prerequisites (must exist before running):
  - data/processed/pcis_scores.csv
  - data/processed/emerging_hotspots.csv
  - data/processed/repeat_offenders.csv
  - data/processed/hotspot_summary.csv

Usage:
  python run_phase3.py
"""

import csv
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import PROCESSED_DIR, REPORTS_DIR
from src import enforcement_priority, patrol_planner, roi_simulator

# ---------------------------------------------------------------------------
# Expected prerequisites
# ---------------------------------------------------------------------------
PREREQUISITES = [
    PROCESSED_DIR / "pcis_scores.csv",
    PROCESSED_DIR / "emerging_hotspots.csv",
    PROCESSED_DIR / "repeat_offenders.csv",
    PROCESSED_DIR / "hotspot_summary.csv",
]

PHASE3_SUMMARY_TXT = REPORTS_DIR / "phase3_summary.txt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_prerequisites():
    missing = [str(p) for p in PREREQUISITES if not p.exists()]
    if missing:
        print("ERROR: The following required files are missing:")
        for m in missing:
            print(f"  {m}")
        print("Run run_phase1.py and run_phase2.py first.")
        sys.exit(1)
    print("Prerequisites check passed.")


def _read_csv_rows(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def build_report(priority_rows, patrol_rows, roi_rows):
    lines = []

    lines.append("Phase 3 Summary")
    lines.append("=" * 60)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}")
    lines.append("")

    # ------------------------------------------------------------------
    # Section 1 — Top 20 Enforcement Priorities (city-wide)
    # ------------------------------------------------------------------
    lines.append("TOP 20 ENFORCEMENT PRIORITIES (City-Wide)")
    lines.append("-" * 60)
    lines.append(
        f"{'Rank':<5} {'Hotspot':<42} {'Station':<20} "
        f"{'Score':>6} {'Band':<10}"
    )
    lines.append("-" * 60)

    sorted_prio = sorted(priority_rows, key=lambda r: _float(r.get("rank_city", 9999)))
    for r in sorted_prio[:20]:
        name  = r["hotspot_name"][:40]
        stn   = r["police_station"][:18]
        score = _float(r["priority_score"])
        band  = r["priority_band"]
        rank  = r["rank_city"]
        lines.append(f"{rank:<5} {name:<42} {stn:<20} {score:>6.2f} {band:<10}")
    lines.append("")

    # Band summary
    band_counts = {}
    for r in priority_rows:
        b = r["priority_band"]
        band_counts[b] = band_counts.get(b, 0) + 1
    lines.append(f"Total hotspots ranked: {len(priority_rows)}")
    for band in ("Critical", "High", "Medium", "Low"):
        lines.append(f"  {band:10s}: {band_counts.get(band, 0)}")
    lines.append("")

    # ------------------------------------------------------------------
    # Section 2 — Top Patrol Routes
    # ------------------------------------------------------------------
    lines.append("TOP PATROL ROUTES (by station, highest-priority first)")
    lines.append("-" * 60)

    # Group patrol stops by route_id
    route_groups = {}
    for stop in patrol_rows:
        rid = stop["route_id"]
        route_groups.setdefault(rid, []).append(stop)

    # Compute mean priority per route for sorting
    route_means = {}
    for rid, stops in route_groups.items():
        scores = [_float(s["priority_score"]) for s in stops]
        route_means[rid] = sum(scores) / len(scores) if scores else 0.0

    top_routes = sorted(route_means.items(), key=lambda x: -x[1])[:15]

    for rid, mean_score in top_routes:
        stops = route_groups[rid]
        station = stops[0]["police_station"]
        lines.append(f"\nRoute: {rid}  |  Station: {station}  |  "
                     f"Stops: {len(stops)}  |  Mean Priority: {mean_score:.2f}")
        lines.append(f"  {'Stop':<5} {'Hotspot':<42} {'Priority':>8} {'Band':<10} {'Dist km':>8}")
        for s in stops:
            lines.append(
                f"  {s['stop_order']:<5} {s['hotspot_name'][:40]:<42} "
                f"{_float(s['priority_score']):>8.2f} {s['priority_band']:<10} "
                f"{_float(s['distance_from_prev_km']):>8.3f}"
            )
    lines.append("")

    # ------------------------------------------------------------------
    # Section 3 — ROI Simulation
    # ------------------------------------------------------------------
    lines.append("ROI SIMULATION RESULTS")
    lines.append("-" * 60)
    lines.append(
        f"{'Scenario':<10} {'Officers':>8} {'Target%':>8} {'Intensity':>10} "
        f"{'Hotspots':>9} {'DPCIS':>8} {'DOffenders':>12}"
    )
    lines.append("-" * 60)
    for r in roi_rows:
        lines.append(
            f"{r['scenario_id']:<10} "
            f"{r['additional_officers']:>8} "
            f"{r['hotspot_reduction_pct']:>7}% "
            f"{r['enforcement_intensity']:>10} "
            f"{r['hotspots_targeted']:>9} "
            f"{'-'+str(r['projected_pcis_reduction']):>8} "
            f"{'-'+str(r['estimated_repeat_offender_reduction']):>12}"
        )
    lines.append("")
    lines.append("Model assumptions (all scenarios):")
    if roi_rows:
        for note in roi_rows[0]["assumption_notes"].split(";"):
            lines.append(f"  {note.strip()}")
    lines.append("")

    # ------------------------------------------------------------------
    # Section 4 — Outputs
    # ------------------------------------------------------------------
    lines.append("OUTPUTS GENERATED")
    lines.append("-" * 60)
    outputs = [
        ("Enforcement priorities", str(PROCESSED_DIR / "enforcement_priorities.csv")),
        ("Patrol routes",          str(PROCESSED_DIR / "patrol_routes.csv")),
        ("ROI simulation",         str(PROCESSED_DIR / "roi_simulation.csv")),
        ("Phase 3 summary",        str(PHASE3_SUMMARY_TXT)),
    ]
    for label, path in outputs:
        lines.append(f"  {label:<25}: {path}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Phase 3 — Enforcement Planning")
    print("=" * 60)

    # 1. Check prerequisites
    _check_prerequisites()
    print()

    # 2. Enforcement Priority Engine
    print("--- Module 1: Enforcement Priority Engine ---")
    priority_rows = enforcement_priority.run(verbose=True)
    print()

    # 3. Patrol Planner
    print("--- Module 2: Patrol Route Planner ---")
    patrol_stops = patrol_planner.run(verbose=True)
    print()

    # 4. ROI Simulator
    print("--- Module 3: ROI Simulator ---")
    roi_results = roi_simulator.run(verbose=True)
    print()

    # 5. Generate Phase 3 report
    print("--- Generating Phase 3 Summary Report ---")
    priority_rows_csv  = _read_csv_rows(PROCESSED_DIR / "enforcement_priorities.csv")
    patrol_rows_csv    = _read_csv_rows(PROCESSED_DIR / "patrol_routes.csv")
    roi_rows_csv       = _read_csv_rows(PROCESSED_DIR / "roi_simulation.csv")

    report_text = build_report(priority_rows_csv, patrol_rows_csv, roi_rows_csv)

    os.makedirs(str(REPORTS_DIR), exist_ok=True)
    with open(PHASE3_SUMMARY_TXT, "w", encoding="utf-8") as fh:
        fh.write(report_text)

    print(f"Phase 3 report written -> {PHASE3_SUMMARY_TXT}")
    print()
    print("Phase 3 complete.")


if __name__ == "__main__":
    main()
