"""Phase 2 batch entry point.

Runs the three Phase 2 intelligence engines in sequence:
    1. PCIS scoring engine       -> data/processed/pcis_scores.csv
    2. Repeat offender engine    -> data/processed/repeat_offenders.csv
    3. Emerging hotspot engine   -> data/processed/emerging_hotspots.csv

Prerequisites:
    - Phase 1 must have been run first to produce:
        data/processed/hotspot_summary.csv
        data/processed/cleaned_violations_full.csv

Usage:
    python run_phase2.py [--hotspot-summary PATH] [--cleaned-full PATH]
"""

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Dict, List

from src.config import (
    DRIFT_MIN_RECENT_MEAN,
    PHASE2_CLEANED_FULL_CSV,
    PHASE2_EMERGING_HOTSPOTS_CSV,
    PHASE2_PCIS_CSV,
    PHASE2_REPEAT_OFFENDERS_CSV,
    PROCESSED_DIR,
    REPEAT_OFFENDER_MIN_VIOLATIONS,
    REPORTS_DIR,
)
from src.emerging_hotspots import compute_emerging_hotspots
from src.pcis_engine import compute_pcis
from src.repeat_offender import compute_repeat_offenders


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    """Write a list of dicts to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 2 intelligence engines.")
    parser.add_argument(
        "--hotspot-summary",
        type=Path,
        default=PROCESSED_DIR / "hotspot_summary.csv",
        help="Path to Phase 1 hotspot_summary.csv.",
    )
    parser.add_argument(
        "--cleaned-full",
        type=Path,
        default=PHASE2_CLEANED_FULL_CSV,
        help="Path to Phase 1 cleaned_violations_full.csv.",
    )
    args = parser.parse_args()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Validate prerequisites
    # ------------------------------------------------------------------
    if not args.hotspot_summary.exists():
        raise FileNotFoundError(
            f"hotspot_summary.csv not found at: {args.hotspot_summary}\n"
            "Run Phase 1 first: python run_phase1.py --input <csv_path>"
        )
    if not args.cleaned_full.exists():
        raise FileNotFoundError(
            f"cleaned_violations_full.csv not found at: {args.cleaned_full}\n"
            "Run Phase 1 first: python run_phase1.py --input <csv_path>"
        )

    # ------------------------------------------------------------------
    # 1. PCIS Scoring Engine
    # ------------------------------------------------------------------
    print("Phase 2 — Step 1/3: Computing PCIS scores...")
    pcis_rows = compute_pcis(args.hotspot_summary)
    write_csv(PHASE2_PCIS_CSV, pcis_rows)
    print(f"  PCIS scores computed: {len(pcis_rows)} hotspots")
    if pcis_rows:
        band_counts = Counter(str(r["pcis_band"]) for r in pcis_rows)
        print(f"  Band breakdown — Critical: {band_counts['Critical']} | "
              f"High: {band_counts['High']} | "
              f"Medium: {band_counts['Medium']} | "
              f"Low: {band_counts['Low']}")
        scores = [float(r["pcis_score"]) for r in pcis_rows]
        print(f"  Score range: min={min(scores):.2f} max={max(scores):.2f} "
              f"mean={sum(scores)/len(scores):.2f}")

    # ------------------------------------------------------------------
    # 2. Repeat Offender Intelligence
    # ------------------------------------------------------------------
    print(f"Phase 2 — Step 2/3: Identifying repeat offenders (min {REPEAT_OFFENDER_MIN_VIOLATIONS} violations)...")
    repeat_rows = compute_repeat_offenders(args.cleaned_full, args.hotspot_summary)
    write_csv(PHASE2_REPEAT_OFFENDERS_CSV, repeat_rows)
    print(f"  Repeat offenders identified: {len(repeat_rows)} vehicles")

    # ------------------------------------------------------------------
    # 3. Emerging Hotspot Detection
    # ------------------------------------------------------------------
    print(f"Phase 2 — Step 3/3: Detecting emerging hotspots (min weekly mean >= {DRIFT_MIN_RECENT_MEAN})...")
    emerging_rows, unknown_excluded = compute_emerging_hotspots(
        args.cleaned_full, args.hotspot_summary
    )
    write_csv(PHASE2_EMERGING_HOTSPOTS_CSV, emerging_rows)

    print(f"\n  NOTE: {unknown_excluded} DBSCAN unknown hotspots excluded from drift analysis.")
    print("  Reason: cluster label is not stored in cleaned records.")
    print("  Only named junction hotspots are analysed for trend detection.")
    print()

    status_counts = Counter(str(r["drift_status"]) for r in emerging_rows)
    emerging_count = status_counts["Emerging"]
    cooling_count = status_counts["Cooling"]
    low_activity_count = status_counts["Low Activity"]
    stable_count = status_counts["Stable"]
    insufficient = status_counts["Insufficient Data"]
    print(f"  Hotspots analysed: {len(emerging_rows)}")
    print(f"  Emerging: {emerging_count} | Low Activity: {low_activity_count} | "
          f"Stable: {stable_count} | Cooling: {cooling_count} | "
          f"Insufficient Data: {insufficient}")

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------
    summary_lines = [
        "Phase 2 Summary (Post-Correction)",
        "==================================",
        "Corrections applied: F1 F2 F3 F4 F5 F6",
        f"Hotspot summary input: {args.hotspot_summary}",
        f"Cleaned full dataset input: {args.cleaned_full}",
        "",
        "PCIS Scoring Engine",
        "-------------------",
        f"Hotspots scored: {len(pcis_rows)}",
    ]
    if pcis_rows:
        scores = [float(r["pcis_score"]) for r in pcis_rows]
        sorted_s = sorted(scores)
        n = len(sorted_s)
        summary_lines += [
            f"Score range: min={min(scores):.2f}  max={max(scores):.2f}  "
            f"mean={sum(scores)/len(scores):.2f}",
            f"P25={sorted_s[n//4]:.2f}  P50={sorted_s[n//2]:.2f}  "
            f"P75={sorted_s[3*n//4]:.2f}",
            f"Band breakdown (percentile-based):",
            f"  Critical (top 15%):     {band_counts['Critical']}",
            f"  High    (50th-85th%):   {band_counts['High']}",
            f"  Medium  (20th-50th%):   {band_counts['Medium']}",
            f"  Low     (bottom 20%):   {band_counts['Low']}",
            "",
            "Top 10 hotspots by PCIS score:",
        ]
        for rank, row in enumerate(pcis_rows[:10], start=1):
            summary_lines.append(
                f"  {rank}. {row['hotspot_name']} | {row['police_station']} | "
                f"PCIS={row['pcis_score']} | Band={row['pcis_band']}"
            )

    summary_lines += [
        "",
        "Repeat Offender Intelligence",
        "----------------------------",
        f"Threshold: >= {REPEAT_OFFENDER_MIN_VIOLATIONS} violations AND >= 2 distinct hotspots",
        f"Filter: REJECTED and DUPLICATE violations excluded (F6)",
        f"Repeat offenders identified: {len(repeat_rows)}",
    ]
    if repeat_rows:
        violations_list = [int(r["total_violations"]) for r in repeat_rows]
        sv = sorted(violations_list)
        nn = len(sv)
        summary_lines += [
            f"Violations per offender: min={min(violations_list)} "
            f"P50={sv[nn//2]} max={max(violations_list)}",
            "Top 10 repeat offenders by offender_score (normalised 0-100):",
        ]
        for rank, row in enumerate(repeat_rows[:10], start=1):
            summary_lines.append(
                f"  {rank}. {row['vehicle_number']} | violations={row['total_violations']} | "
                f"hotspots={row['distinct_hotspot_count']} | "
                f"score={row['offender_score']} (raw={row['offender_score_raw']})"
            )

    summary_lines += [
        "",
        "Emerging Hotspot Detection",
        "--------------------------",
        f"WARNING: {unknown_excluded} DBSCAN unknown hotspots excluded (cluster label "
        f"not in cleaned records).",
        f"Named hotspots analysed: {len(emerging_rows)}",
        f"Min weekly recent mean gate: {DRIFT_MIN_RECENT_MEAN} violations/week",
        f"Emerging:          {emerging_count}",
        f"Low Activity:      {low_activity_count}  (drift triggered but below activity gate)",
        f"Stable:            {stable_count}",
        f"Cooling:           {cooling_count}",
        f"Insufficient Data: {insufficient}",
    ]
    if emerging_count > 0:
        summary_lines.append("Top emerging hotspots by drift_score (normalised 0-100):")
        emerging_sorted = [r for r in emerging_rows if r["drift_status"] == "Emerging"]
        for rank, row in enumerate(emerging_sorted[:10], start=1):
            summary_lines.append(
                f"  {rank}. {row['hotspot_name']} | {row['police_station']} | "
                f"drift={row['drift_score']} (raw={row['drift_score_raw']}) | "
                f"recent_mean={row['mean_weekly_recent']}"
            )

    summary_lines += [
        "",
        "Outputs",
        "-------",
        f"PCIS scores:        {PHASE2_PCIS_CSV}",
        f"Repeat offenders:   {PHASE2_REPEAT_OFFENDERS_CSV}",
        f"Emerging hotspots:  {PHASE2_EMERGING_HOTSPOTS_CSV}",
    ]

    report_text = "\n".join(summary_lines)
    (REPORTS_DIR / "phase2_summary.txt").write_text(report_text, encoding="utf-8")
    print()
    print(report_text)


if __name__ == "__main__":
    main()
