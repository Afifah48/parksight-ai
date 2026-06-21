import argparse
import csv
from pathlib import Path
from typing import Dict, List

from src.config import (
    DBSCAN_EPS_METERS,
    DBSCAN_MIN_SAMPLES,
    DEFAULT_SOURCE_CSV,
    PHASE2_CLEANED_FULL_CSV,
    PROCESSED_DIR,
    REPORTS_DIR,
)
from src.data_loader import iter_raw_records, read_header, validate_schema
from src.hotspot_engine import build_named_hotspots, build_unknown_hotspots, write_csv
from src.preprocessing import clean_record


def write_cleaned_full(path: Path, rows: List[Dict[str, object]]) -> None:
    """Write the complete cleaned dataset (all records, no cap)."""
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_cleaned_sample(path: Path, rows: List[Dict[str, object]], limit: int = 5000) -> None:
    """Write a capped sample for quick inspection. Does not affect Phase 2 processing."""
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows[:limit])


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 1 hotspot intelligence pipeline.")
    parser.add_argument("--input", type=Path, default=DEFAULT_SOURCE_CSV, help="Path to violation CSV.")
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional limit for quick local smoke tests.",
    )
    parser.add_argument("--eps-meters", type=float, default=DBSCAN_EPS_METERS)
    parser.add_argument("--min-samples", type=int, default=DBSCAN_MIN_SAMPLES)
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=5000,
        help="Row cap for the inspection sample CSV (default 5000). Does not affect Phase 2.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise FileNotFoundError(f"Input CSV not found: {args.input}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    header = read_header(args.input)
    ok, missing = validate_schema(header)
    if not ok:
        raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

    cleaned_records: List[Dict[str, object]] = []
    raw_count = 0
    dropped_count = 0

    for row in iter_raw_records(args.input):
        raw_count += 1
        cleaned = clean_record(row)
        if cleaned is None:
            dropped_count += 1
        else:
            cleaned_records.append(cleaned)

        if args.max_records and raw_count >= args.max_records:
            break

    named_hotspots = build_named_hotspots(cleaned_records)
    unknown_hotspots = build_unknown_hotspots(
        cleaned_records,
        eps_meters=args.eps_meters,
        min_samples=args.min_samples,
    )
    hotspot_summary = sorted(
        named_hotspots + unknown_hotspots,
        key=lambda row: (float(row["hotspot_severity"]), int(row["violation_count"])),
        reverse=True,
    )

    # Write full cleaned dataset — required by Phase 2 engines.
    write_cleaned_full(PHASE2_CLEANED_FULL_CSV, cleaned_records)
    # Write capped inspection sample.
    write_cleaned_sample(
        PROCESSED_DIR / "cleaned_violations_sample.csv",
        cleaned_records,
        limit=args.sample_limit,
    )
    write_csv(PROCESSED_DIR / "named_hotspots.csv", named_hotspots)
    write_csv(PROCESSED_DIR / "unknown_hotspots.csv", unknown_hotspots)
    write_csv(PROCESSED_DIR / "hotspot_summary.csv", hotspot_summary)

    named_count = sum(1 for record in cleaned_records if record["is_named_junction"])
    unknown_count = len(cleaned_records) - named_count
    summary = [
        "Phase 1 Summary",
        "===============",
        f"Input CSV: {args.input}",
        f"Raw records scanned: {raw_count}",
        f"Clean records retained: {len(cleaned_records)}",
        f"Records dropped: {dropped_count}",
        f"Named junction records: {named_count}",
        f"No Junction records: {unknown_count}",
        f"Named hotspots generated: {len(named_hotspots)}",
        f"Unknown DBSCAN hotspots generated: {len(unknown_hotspots)}",
        f"DBSCAN eps meters: {args.eps_meters}",
        f"DBSCAN min samples: {args.min_samples}",
        f"Full cleaned dataset: {PHASE2_CLEANED_FULL_CSV}",
        "",
        "Top 10 hotspots by severity:",
    ]

    for rank, hotspot in enumerate(hotspot_summary[:10], start=1):
        summary.append(
            f"{rank}. {hotspot['hotspot_name']} | {hotspot['police_station']} | "
            f"severity={hotspot['hotspot_severity']} | violations={hotspot['violation_count']}"
        )

    (REPORTS_DIR / "phase1_summary.txt").write_text("\n".join(summary), encoding="utf-8")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
