"""
Patrol Route Planner
====================
Generates recommended officer patrol sequences per police station.

Method
------
For each police station's hotspots:
  1. Sort by priority_score descending to identify the starting hotspot.
  2. Apply a nearest-neighbour greedy algorithm:
       - Start at the highest-priority hotspot.
       - At each step, move to the closest unvisited hotspot (haversine distance).
     This produces a short route while still honouring high-priority anchoring.
  3. Assign stop_order 1, 2, 3, … within the route.

Route naming: "<STATION>-R01", "<STATION>-R02", ... (one route per station for
the base plan; stations with ≥ 10 hotspots are split into ≤ 10-stop sub-routes).

Input
-----
- data/processed/enforcement_priorities.csv

Output
------
- data/processed/patrol_routes.csv

Fields
------
  police_station, route_id, stop_order, hotspot_id, hotspot_name,
  latitude, longitude, priority_score, priority_band,
  distance_from_prev_km
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
OUTPUT_CSV = PROCESSED_DIR / "patrol_routes.csv"

# Maximum stops per patrol route (split into sub-routes above this)
MAX_STOPS_PER_ROUTE = 10


def _haversine_km(lat1, lon1, lat2, lon2):
    """Return geodesic distance in kilometres between two coordinate pairs."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _safe_float(val, default=0.0):
    try:
        v = float(val)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def load_priorities(path):
    """Load enforcement_priorities.csv -> list of hotspot dicts."""
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append({
                "hotspot_id":     row["hotspot_id"],
                "hotspot_name":   row["hotspot_name"],
                "police_station": row["police_station"],
                "latitude":       _safe_float(row.get("latitude")),
                "longitude":      _safe_float(row.get("longitude")),
                "priority_score": _safe_float(row.get("priority_score")),
                "priority_band":  row.get("priority_band", ""),
            })
    return rows


def nearest_neighbour_route(hotspots):
    """
    Build a greedy nearest-neighbour route starting from the highest-priority
    hotspot.  Returns the ordered list of hotspot dicts.
    """
    if not hotspots:
        return []

    # Sort by priority descending; start from highest-priority
    remaining = sorted(hotspots, key=lambda h: -h["priority_score"])
    route = [remaining.pop(0)]

    while remaining:
        last = route[-1]
        best_idx  = None
        best_dist = float("inf")
        for i, h in enumerate(remaining):
            d = _haversine_km(last["latitude"], last["longitude"],
                              h["latitude"],   h["longitude"])
            if d < best_dist:
                best_dist = d
                best_idx  = i
        route.append(remaining.pop(best_idx))

    return route


def split_into_subroutes(ordered_hotspots, max_stops):
    """
    Split a long route into sub-routes of at most max_stops each.
    Returns a list of lists.
    """
    return [
        ordered_hotspots[i : i + max_stops]
        for i in range(0, len(ordered_hotspots), max_stops)
    ]


def _station_abbreviation(station_name, used_abbrs=None):
    """
    Create a unique short safe abbreviation for use in route_id.
    Uses the full sanitised station name (up to 12 chars) to minimise
    collisions; if a collision still occurs, appends a numeric suffix.
    """
    clean = "".join(c for c in station_name.upper() if c.isalnum())
    abbr  = clean[:12] or "STN"
    if used_abbrs is None:
        return abbr
    # Deduplicate
    candidate = abbr
    idx = 2
    while candidate in used_abbrs:
        candidate = abbr[:10] + str(idx)
        idx += 1
    used_abbrs.add(candidate)
    return candidate


def run(priorities_path=None, output_path=None, verbose=True):
    """
    Main entry point for the patrol planner.

    Returns a list of patrol stop dicts.
    """
    priorities_path = priorities_path or ENFORCEMENT_PRIORITIES_CSV
    output_path     = output_path     or OUTPUT_CSV

    if verbose:
        print("[PatrolPlanner] Loading enforcement priorities …")
    all_hotspots = load_priorities(priorities_path)

    if not all_hotspots:
        raise ValueError("No hotspots found in enforcement priorities CSV.")

    # ------------------------------------------------------------------
    # Group by police station
    # ------------------------------------------------------------------
    station_groups = {}
    for h in all_hotspots:
        station_groups.setdefault(h["police_station"], []).append(h)

    # ------------------------------------------------------------------
    # Build patrol routes
    # ------------------------------------------------------------------
    patrol_stops = []
    total_routes = 0

    used_abbrs = set()
    for station in sorted(station_groups.keys()):
        hotspots = station_groups[station]
        abbr     = _station_abbreviation(station, used_abbrs)

        # Build full nearest-neighbour route
        ordered = nearest_neighbour_route(hotspots)

        # Split into sub-routes if too long
        sub_routes = split_into_subroutes(ordered, MAX_STOPS_PER_ROUTE)

        for route_seq, sub in enumerate(sub_routes, start=1):
            route_id = f"{abbr}-R{route_seq:02d}"
            total_routes += 1
            prev = None
            for stop_order, h in enumerate(sub, start=1):
                if prev is None:
                    dist_km = 0.0
                else:
                    dist_km = _haversine_km(prev["latitude"], prev["longitude"],
                                            h["latitude"],    h["longitude"])
                patrol_stops.append({
                    "police_station":       station,
                    "route_id":             route_id,
                    "stop_order":           stop_order,
                    "hotspot_id":           h["hotspot_id"],
                    "hotspot_name":         h["hotspot_name"],
                    "latitude":             h["latitude"],
                    "longitude":            h["longitude"],
                    "priority_score":       round(h["priority_score"], 4),
                    "priority_band":        h["priority_band"],
                    "distance_from_prev_km": round(dist_km, 4),
                })
                prev = h

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------
    fieldnames = [
        "police_station",
        "route_id",
        "stop_order",
        "hotspot_id",
        "hotspot_name",
        "latitude",
        "longitude",
        "priority_score",
        "priority_band",
        "distance_from_prev_km",
    ]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(patrol_stops)

    if verbose:
        print(f"[PatrolPlanner] {len(station_groups)} stations processed.")
        print(f"[PatrolPlanner] {total_routes} patrol routes generated.")
        print(f"[PatrolPlanner] {len(patrol_stops)} total patrol stops.")
        print(f"[PatrolPlanner] Output -> {output_path}")

    return patrol_stops
