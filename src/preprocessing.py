import json
from datetime import datetime
from typing import Dict, List, Optional

from .config import (
    LARGE_VEHICLE_KEYWORDS,
    MAIN_ROAD_KEYWORDS,
    NO_JUNCTION_LABEL,
    PEAK_HOUR_RANGES,
)


NULL_VALUES = {"", "NULL", "NONE", "NAN", "NA"}


def is_nullish(value: object) -> bool:
    return value is None or str(value).strip().upper() in NULL_VALUES


def clean_text(value: object, default: str = "") -> str:
    if is_nullish(value):
        return default
    return " ".join(str(value).strip().split())


def clean_upper(value: object, default: str = "") -> str:
    return clean_text(value, default=default).upper()


def parse_float(value: object) -> Optional[float]:
    if is_nullish(value):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def parse_datetime(value: object) -> Optional[datetime]:
    if is_nullish(value):
        return None
    raw = str(value).strip()
    if raw.endswith("+00"):
        raw = raw[:-3] + "+00:00"
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def parse_violation_types(value: object) -> List[str]:
    if is_nullish(value):
        return []
    raw = str(value).strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [clean_upper(item) for item in parsed if not is_nullish(item)]
    except json.JSONDecodeError:
        pass
    return [clean_upper(part) for part in raw.replace("[", "").replace("]", "").split(",")]


def normalize_junction(value: object) -> str:
    name = clean_text(value, default=NO_JUNCTION_LABEL)
    if not name or name.upper() in {"NO JUNCTION", "NOJUNCTION"}:
        return NO_JUNCTION_LABEL
    return name


def is_peak_hour(hour: int) -> bool:
    return any(hour in hour_range for hour_range in PEAK_HOUR_RANGES)


def has_keyword(values: List[str], keywords: tuple[str, ...]) -> bool:
    joined = " | ".join(values)
    return any(keyword in joined for keyword in keywords)


def clean_record(row: Dict[str, str]) -> Optional[Dict[str, object]]:
    latitude = parse_float(row.get("latitude"))
    longitude = parse_float(row.get("longitude"))
    created_at = parse_datetime(row.get("created_datetime"))

    if latitude is None or longitude is None or created_at is None:
        return None
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return None

    violation_types = parse_violation_types(row.get("violation_type"))
    vehicle_number = clean_upper(row.get("updated_vehicle_number")) or clean_upper(
        row.get("vehicle_number")
    )
    vehicle_type = clean_upper(row.get("updated_vehicle_type")) or clean_upper(
        row.get("vehicle_type"), default="UNKNOWN"
    )
    junction_name = normalize_junction(row.get("junction_name"))
    police_station = clean_text(row.get("police_station"), default="Unknown")

    return {
        "id": clean_text(row.get("id")),
        "latitude": latitude,
        "longitude": longitude,
        "location": clean_text(row.get("location")),
        "vehicle_number": vehicle_number,
        "vehicle_type": vehicle_type,
        "violation_type": "; ".join(violation_types),
        "created_datetime": created_at.isoformat(),
        "date": created_at.date().isoformat(),
        "hour": created_at.hour,
        "day_of_week": created_at.strftime("%A"),
        "month": created_at.strftime("%Y-%m"),
        "week": f"{created_at.isocalendar().year}-W{created_at.isocalendar().week:02d}",
        "police_station": police_station,
        "junction_name": junction_name,
        "validation_status": clean_upper(row.get("validation_status"), default="UNKNOWN"),
        "center_code": clean_text(row.get("center_code")),
        "is_named_junction": junction_name != NO_JUNCTION_LABEL,
        "is_peak_hour": is_peak_hour(created_at.hour),
        "is_main_road_violation": has_keyword(violation_types, MAIN_ROAD_KEYWORDS),
        "is_large_vehicle": has_keyword([vehicle_type], LARGE_VEHICLE_KEYWORDS),
    }
