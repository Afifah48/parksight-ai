import csv
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .config import REQUIRED_COLUMNS


def validate_schema(fieldnames: List[str] | None) -> Tuple[bool, List[str]]:
    """Return whether the CSV has the required MVP columns."""
    fields = set(fieldnames or [])
    missing = sorted(REQUIRED_COLUMNS - fields)
    return not missing, missing


def iter_raw_records(csv_path: Path) -> Iterable[Dict[str, str]]:
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        ok, missing = validate_schema(reader.fieldnames)
        if not ok:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
        for row in reader:
            yield row


def read_header(csv_path: Path) -> List[str]:
    with csv_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        return next(reader)
