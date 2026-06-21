from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR     = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR  = PROJECT_ROOT / "reports"

# Default source CSV — relative to project root, works on any machine.
DEFAULT_SOURCE_CSV = (
    PROCESSED_DIR / "jan to may police violation_anonymized791b166.csv"
)


# ---------------------------------------------------------------------------
# Phase 1 — DBSCAN clustering
# ---------------------------------------------------------------------------

DBSCAN_EPS_METERS = 75.0
DBSCAN_MIN_SAMPLES = 20

NO_JUNCTION_LABEL = "No Junction"

PEAK_HOUR_RANGES = (
    range(8, 11),
    range(17, 21),
)

# F1 FIX: Removed "NO PARKING" and "WRONG PARKING" — these generic terms
# matched every violation in the dataset, making main_road_violation_share=1.0
# for all 701 hotspots and rendering the feature useless for discrimination.
# Only genuinely obstruction-specific violation types are retained.
MAIN_ROAD_KEYWORDS = (
    "MAIN ROAD",
    "ROAD CROSSING",
    "OBSTRUCTION",
    "FOOTPATH",
    "BUS STOP",
    "JUNCTION",
    "TRAFFIC",
    "PARKING IN A MAIN ROAD",
    "PARKING NEAR ROAD CROSSING",
    "PARKING ON FOOTPATH",
    "PARKING NEAR BUSTOP",
    "DOUBLE PARKING",
)

LARGE_VEHICLE_KEYWORDS = (
    "BUS",
    "TRUCK",
    "LORRY",
    "GOODS",
    "TEMPO",
    "VAN",
    "MAXI",
    "HEAVY",
    "TRACTOR",
)

REQUIRED_COLUMNS = {
    "latitude",
    "longitude",
    "location",
    "vehicle_number",
    "vehicle_type",
    "violation_type",
    "created_datetime",
    "police_station",
    "junction_name",
    "validation_status",
    "center_code",
}

# ---------------------------------------------------------------------------
# F6 FIX: Validation status filter
# Records with these statuses are counted for scoring; REJECTED and DUPLICATE
# are excluded from all Phase 2 scoring engines.
# ---------------------------------------------------------------------------

VALID_STATUSES = {"APPROVED", "PROCESSING", "UNKNOWN"}

# ---------------------------------------------------------------------------
# Phase 2 — PCIS scoring
# PCIS = Parking-Induced Congestion Impact Score (0-100)
# Weights must sum to 1.0
# ---------------------------------------------------------------------------

PCIS_WEIGHT_DAILY_DENSITY = 0.30         # violation_count / active_days
PCIS_WEIGHT_PEAK_HOUR_SHARE = 0.25       # peak_hour_share
PCIS_WEIGHT_LARGE_VEHICLE_SHARE = 0.20   # large_vehicle_share
PCIS_WEIGHT_MAIN_ROAD_SHARE = 0.15       # main_road_violation_share (corrected)
PCIS_WEIGHT_REPEAT_OFFENDER_RATIO = 0.10 # repeat_vehicle_count / unique_vehicle_count

# F2 FIX: Percentile-based band thresholds (applied to rank position within
# the scored population, not to raw PCIS value).
# Critical = top 15% | High = 15-50th pct | Medium = 50-80th pct | Low = bottom 20%
PCIS_BAND_CRITICAL_PCT = 85.0  # hotspots at or above this percentile = Critical
PCIS_BAND_HIGH_PCT = 50.0      # hotspots at or above this percentile = High
PCIS_BAND_MEDIUM_PCT = 20.0    # hotspots at or above this percentile = Medium
                               # below = Low

# ---------------------------------------------------------------------------
# Phase 2 — Repeat offender intelligence
# F5 FIX: Raised minimum violations from 5 to 8 to reduce low-signal noise.
# ---------------------------------------------------------------------------

REPEAT_OFFENDER_MIN_VIOLATIONS = 8     # minimum total violations to be flagged
REPEAT_OFFENDER_MIN_HOTSPOTS = 2       # minimum distinct hotspots visited

# ---------------------------------------------------------------------------
# Phase 2 — Emerging hotspot drift detection
# Drift = (mean recent 4w - mean prior 4w) / (stdev prior 4w + epsilon)
# F3 FIX: Added DRIFT_MAX_SCORE cap and DRIFT_MIN_RECENT_MEAN gate.
# ---------------------------------------------------------------------------

DRIFT_RECENT_WEEKS = 4                  # weeks in the "recent" window
DRIFT_PRIOR_WEEKS = 4                   # weeks in the "prior" baseline window
DRIFT_EPSILON = 1.0                     # zero-division guard
DRIFT_EMERGING_THRESHOLD = 1.5          # Z-score threshold to flag as emerging
DRIFT_COOLING_THRESHOLD = -1.5          # Z-score threshold to flag as cooling
DRIFT_MAX_SCORE = 10.0                  # F3: raw drift is capped here before normalising to 0-100
DRIFT_MIN_RECENT_MEAN = 5.0             # F4: minimum weekly mean to qualify as Emerging

# ---------------------------------------------------------------------------
# Phase 2 — Output paths
# ---------------------------------------------------------------------------

PHASE2_PCIS_CSV = PROCESSED_DIR / "pcis_scores.csv"
PHASE2_REPEAT_OFFENDERS_CSV = PROCESSED_DIR / "repeat_offenders.csv"
PHASE2_EMERGING_HOTSPOTS_CSV = PROCESSED_DIR / "emerging_hotspots.csv"
PHASE2_CLEANED_FULL_CSV = PROCESSED_DIR / "cleaned_violations_full.csv"
