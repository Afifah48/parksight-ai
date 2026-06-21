import csv
import hashlib
import math
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from .config import DBSCAN_EPS_METERS, DBSCAN_MIN_SAMPLES, NO_JUNCTION_LABEL


EARTH_RADIUS_METERS = 6_371_000.0


def haversine_meters(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    lat1 = math.radians(a_lat)
    lat2 = math.radians(b_lat)
    dlat = math.radians(b_lat - a_lat)
    dlon = math.radians(b_lon - a_lon)
    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METERS * math.asin(math.sqrt(h))


def percentile_score(value: float, values: Sequence[float]) -> float:
    if not values:
        return 0.0
    lower_or_equal = sum(1 for item in values if item <= value)
    return round(100 * lower_or_equal / len(values), 2)


def vehicle_counts(records: Iterable[Dict[str, object]]) -> Counter:
    counts: Counter = Counter()
    for record in records:
        vehicle = record.get("vehicle_number")
        if vehicle:
            counts[str(vehicle)] += 1
    return counts


def _empty_aggregate() -> Dict[str, object]:
    return {
        "violation_count": 0,
        "vehicles": set(),
        "repeat_vehicles": set(),
        "large_vehicle_count": 0,
        "main_road_count": 0,
        "peak_hour_count": 0,
        "active_dates": set(),
        "lat_sum": 0.0,
        "lon_sum": 0.0,
        "latest_datetime": "",
        "violation_type_counts": Counter(),
    }


def _update_aggregate(
    aggregate: Dict[str, object],
    record: Dict[str, object],
    repeat_vehicle_lookup: set[str],
) -> None:
    aggregate["violation_count"] += 1
    aggregate["lat_sum"] += float(record["latitude"])
    aggregate["lon_sum"] += float(record["longitude"])
    aggregate["active_dates"].add(str(record["date"]))

    vehicle = str(record.get("vehicle_number") or "")
    if vehicle:
        aggregate["vehicles"].add(vehicle)
        if vehicle in repeat_vehicle_lookup:
            aggregate["repeat_vehicles"].add(vehicle)

    if record.get("is_large_vehicle"):
        aggregate["large_vehicle_count"] += 1
    if record.get("is_main_road_violation"):
        aggregate["main_road_count"] += 1
    if record.get("is_peak_hour"):
        aggregate["peak_hour_count"] += 1

    created = str(record.get("created_datetime") or "")
    if created > aggregate["latest_datetime"]:
        aggregate["latest_datetime"] = created

    for violation in str(record.get("violation_type") or "").split("; "):
        if violation:
            aggregate["violation_type_counts"][violation] += 1


def _stable_hotspot_id(hotspot_name: str, police_station: str, prefix: str) -> str:
    """Return a deterministic, stable ID derived from a SHA-1 hash of the key fields.

    The ID is stable across re-runs regardless of record ordering or ranking.
    Format: <prefix>-<8 hex digits>  e.g. N-3fa2c1b0
    """
    raw = f"{hotspot_name}|{police_station}".encode("utf-8")
    digest = hashlib.sha1(raw, usedforsecurity=False).hexdigest()[:8]
    return f"{prefix}-{digest}"


def _finalize_aggregates(
    grouped: Dict[Tuple[str, str], Dict[str, object]],
    hotspot_type: str,
    prefix: str,
) -> List[Dict[str, object]]:
    violation_counts = [int(item["violation_count"]) for item in grouped.values()]
    active_day_counts = [len(item["active_dates"]) for item in grouped.values()]
    rows: List[Dict[str, object]] = []

    for (hotspot_name, police_station), aggregate in sorted(
        grouped.items(), key=lambda item: int(item[1]["violation_count"]), reverse=True
    ):
        count = int(aggregate["violation_count"])
        active_days = len(aggregate["active_dates"])
        top_violation = ""
        if aggregate["violation_type_counts"]:
            top_violation = aggregate["violation_type_counts"].most_common(1)[0][0]

        severity = (
            0.35 * percentile_score(count, violation_counts)
            + 0.20 * percentile_score(active_days, active_day_counts)
            + 0.15 * (100 * int(aggregate["peak_hour_count"]) / count)
            + 0.15 * (100 * len(aggregate["repeat_vehicles"]) / max(1, len(aggregate["vehicles"])))
            + 0.15 * (100 * int(aggregate["large_vehicle_count"]) / count)
        )

        rows.append(
            {
                "hotspot_id": _stable_hotspot_id(hotspot_name, police_station, prefix),
                "hotspot_type": hotspot_type,
                "hotspot_name": hotspot_name,
                "police_station": police_station,
                "latitude": round(float(aggregate["lat_sum"]) / count, 7),
                "longitude": round(float(aggregate["lon_sum"]) / count, 7),
                "violation_count": count,
                "unique_vehicle_count": len(aggregate["vehicles"]),
                "repeat_vehicle_count": len(aggregate["repeat_vehicles"]),
                "large_vehicle_share": round(int(aggregate["large_vehicle_count"]) / count, 4),
                "main_road_violation_share": round(int(aggregate["main_road_count"]) / count, 4),
                "peak_hour_share": round(int(aggregate["peak_hour_count"]) / count, 4),
                "active_days": active_days,
                "latest_datetime": aggregate["latest_datetime"],
                "top_violation_type": top_violation,
                "hotspot_severity": round(severity, 2),
            }
        )

    return rows


def build_named_hotspots(
    records: List[Dict[str, object]], repeat_threshold: int = 5
) -> List[Dict[str, object]]:
    counts = vehicle_counts(records)
    repeat_vehicle_lookup = {vehicle for vehicle, count in counts.items() if count >= repeat_threshold}
    grouped: Dict[Tuple[str, str], Dict[str, object]] = defaultdict(_empty_aggregate)

    for record in records:
        if record.get("junction_name") == NO_JUNCTION_LABEL:
            continue
        key = (str(record["junction_name"]), str(record["police_station"]))
        _update_aggregate(grouped[key], record, repeat_vehicle_lookup)

    return _finalize_aggregates(grouped, hotspot_type="Named Junction", prefix="N")


def _cell_for_point(lat: float, lon: float, eps_meters: float) -> Tuple[int, int]:
    lat_size = eps_meters / 111_320.0
    lon_size = eps_meters / (111_320.0 * max(0.1, math.cos(math.radians(lat))))
    return (math.floor(lat / lat_size), math.floor(lon / lon_size))


def _build_spatial_index(
    points: List[Dict[str, object]], eps_meters: float
) -> Dict[Tuple[int, int], List[int]]:
    index: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for point_index, point in enumerate(points):
        index[_cell_for_point(float(point["latitude"]), float(point["longitude"]), eps_meters)].append(
            point_index
        )
    return index


def _neighbor_indices(
    points: List[Dict[str, object]],
    spatial_index: Dict[Tuple[int, int], List[int]],
    point_index: int,
    eps_meters: float,
) -> List[int]:
    point = points[point_index]
    lat = float(point["latitude"])
    lon = float(point["longitude"])
    cell_lat, cell_lon = _cell_for_point(lat, lon, eps_meters)
    neighbors: List[int] = []

    for dlat in range(-2, 3):
        for dlon in range(-2, 3):
            for candidate_index in spatial_index.get((cell_lat + dlat, cell_lon + dlon), []):
                candidate = points[candidate_index]
                distance = haversine_meters(
                    lat,
                    lon,
                    float(candidate["latitude"]),
                    float(candidate["longitude"]),
                )
                if distance <= eps_meters:
                    neighbors.append(candidate_index)

    return neighbors


def dbscan_unknown_records(
    records: List[Dict[str, object]],
    eps_meters: float = DBSCAN_EPS_METERS,
    min_samples: int = DBSCAN_MIN_SAMPLES,
) -> Dict[int, int]:
    points = [record for record in records if record.get("junction_name") == NO_JUNCTION_LABEL]
    spatial_index = _build_spatial_index(points, eps_meters)
    labels = [-99] * len(points)
    cluster_id = 0

    for point_index in range(len(points)):
        if labels[point_index] != -99:
            continue

        neighbors = _neighbor_indices(points, spatial_index, point_index, eps_meters)
        if len(neighbors) < min_samples:
            labels[point_index] = -1
            continue

        labels[point_index] = cluster_id
        queue = deque(neighbors)
        while queue:
            neighbor_index = queue.popleft()
            if labels[neighbor_index] == -1:
                labels[neighbor_index] = cluster_id
            if labels[neighbor_index] != -99:
                continue

            labels[neighbor_index] = cluster_id
            neighbor_neighbors = _neighbor_indices(points, spatial_index, neighbor_index, eps_meters)
            if len(neighbor_neighbors) >= min_samples:
                queue.extend(neighbor_neighbors)

        cluster_id += 1

    unknown_record_indexes = [
        index for index, record in enumerate(records) if record.get("junction_name") == NO_JUNCTION_LABEL
    ]
    return {
        unknown_record_indexes[local_index]: label
        for local_index, label in enumerate(labels)
        if label >= 0
    }


def build_unknown_hotspots(
    records: List[Dict[str, object]],
    eps_meters: float = DBSCAN_EPS_METERS,
    min_samples: int = DBSCAN_MIN_SAMPLES,
    repeat_threshold: int = 5,
) -> List[Dict[str, object]]:
    labels_by_record_index = dbscan_unknown_records(records, eps_meters, min_samples)
    counts = vehicle_counts(records)
    repeat_vehicle_lookup = {vehicle for vehicle, count in counts.items() if count >= repeat_threshold}
    grouped: Dict[Tuple[str, str], Dict[str, object]] = defaultdict(_empty_aggregate)

    cluster_station_counts: Dict[int, Counter] = defaultdict(Counter)
    for record_index, label in labels_by_record_index.items():
        cluster_station_counts[label][str(records[record_index]["police_station"])] += 1

    dominant_station = {
        label: station_counts.most_common(1)[0][0]
        for label, station_counts in cluster_station_counts.items()
    }

    for record_index, label in labels_by_record_index.items():
        name = f"Unknown Hotspot U-{label + 1:04d}"
        station = dominant_station[label]
        key = (name, station)
        _update_aggregate(grouped[key], records[record_index], repeat_vehicle_lookup)

    return _finalize_aggregates(grouped, hotspot_type="Discovered Unknown", prefix="U")


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
