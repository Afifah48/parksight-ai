# Changelog

## 2026-06-19 — Phase 4 Day 4: Intelligence Detail Pages

### New: `pages/4_Emerging_Hotspot_Alerts.py`
- Emerging hotspot drill-down with drift score and recent vs prior week statistics.
- Station and drift status filtering.
- Visualizations using Plotly bar charts.

### New: `pages/5_Repeat_Offender_Intelligence.py`
- Repeat offender table with specific filtering by station, min violations, and vehicle search.
- Plotly histogram of offender scores.
- Plotly scatter chart for Violations vs Distinct Hotspots.

## 2026-06-19 — Phase 4 Day 3: High Impact Operational Pages

### New: `pages/6_Enforcement_Priority_Rankings.py`
- Full 701-row sortable/filterable priority table.
- Station drill-down with band distribution and top-10 hotspots.
- PCIS component contribution stacked bar chart.
- Leaderboards per component (PCIS, Drift, Repeat Offender Density).

### New: `pages/7_Patrol_Planner.py`
- Interactive Folium map with polyline routes and numbered stop markers.
- Stop sequence table with distance calculation.
- Route summary KPIs and priority band distribution donut chart.
- Expandable table showing all routes for a station.

### New: `pages/8_ROI_Simulator.py`
- Interactive what-if simulation for resource deployment.
- Officer allocation slider and enforcement intensity selector.
- Animated projected output KPIs (PCIS reduction, hotspot reduction, offender contacts).
- Plotly waterfall chart showing baseline to post-enforcement PCIS.
- Bubble chart showing scenario landscape (officers vs impact).

## 2026-06-19 — Phase 4 Day 2: Action Center

### New: `src/recommendation_engine.py`

Presentation-layer rule engine (deterministic, no new ML model). Reads pre-computed
Phase 1–3 scores and applies four rule types per station scope.

**Architecture note:** Engine is a filter+sort layer, not an analytical model. All
heavy computation remains in the batch pipeline. This matches the ARCHITECTURE.md
mandate that Phase 4 intelligence be pre-computed.

Rule types and trigger conditions:

| Type | Trigger | Output |
|---|---|---|
| `URGENT DEPLOY` | drift_score ≥ 70 AND drift_status = Emerging | action card with weekly trend |
| `PRIORITY PATROL` | pcis_score ≥ 80 | action card with PCIS breakdown |
| `OFFENDER SWEEP` | repeat_offender_density_norm ≥ 70 | action card with vehicle targets |
| `ENFORCE` | all Critical/High not matching above | standard action card with rank |

**Public API:**

- `generate_recommendations(station=None)` — returns dict with 6 keys:
  - `top_actions` — top 5 action cards with type, reason, and all scores
  - `emerging_alerts` — drift alerts with weekly trend, pct increase, urgency
  - `patrol_deployments` — per-station officer count, routes, target hotspots
  - `offender_targets` — ranked vehicles with intercept window and peak-hour guidance
  - `expected_impact` — ROI scenario matched by hotspot count
  - `stations_at_risk` — top 5 stations by peak priority score

### New: `pages/2_Action_Center.py`

Operational enforcement command hub — transforms the app from analytics to action.

**Section 1: Today's Enforcement Plan**
- Top 5 action cards with action type banner, band-colour left border
- Each card shows: priority score, PCIS, drift, violations, and a plain-English
  reason sentence explaining why this hotspot is prioritised
- EMERGING badge on cards where drift_score ≥ 70

**Section 2: Emerging Threat Alerts**
- Alert banners for Emerging hotspots with drift_score ≥ 70
- Per-alert: current weekly rate, prior baseline, % change, patrol route reference
- CRITICAL / HIGH / ELEVATED urgency labelling
- Drift score bar chart (Plotly, colour-coded by urgency) beside the alert list

**Section 3: Officer Deployment Suggestions**
- Card grid per station (up to 6): officer count, critical hotspots, route count
- Officers recommended = number of patrol routes (min 1, max 5)
- Top 3 target hotspots with priority score and band colour

**Section 4: Repeat Offender Targets**
- Offender cards with vehicle number, violation count, score badge, location list
- Peak-hour percentage highlighted in orange if ≥ 50%
- Intercept guidance note (time window based on peak-hour concentration)
- Offender score bar chart (Plotly, purple gradient)

**Section 5: Expected Impact**
- 3 KPI cards: projected PCIS reduction, hotspots improved, offender contacts
- ROI scenario detail card (matched by hotspot count)
- PCIS waterfall chart (Plotly): baseline → reduction → post-enforcement

**General:**
- Station scope filter in sidebar — all 5 sections update simultaneously
- Scope KPI strip at top: active actions, threat alerts, deployment plans, targets, critical
- Highest Risk Stations strip at bottom (top 5 by max priority)
- Navigation links to Command Center and City Risk Map

### Modified: `app.py`

- Landing page expanded from 2-card to 3-card grid:
  Command Center (blue) · Action Center (red) · City Risk Map (green)
- Sidebar navigation updated to include Action Center link

## 2026-06-19 — Phase 4 Day 1: Application Foundation


### Deployment blocker fixed

- **`src/config.py`**: Removed hardcoded absolute `DEFAULT_SOURCE_CSV` path
  (`C:\Users\hp\...`). Replaced with portable relative path
  `PROCESSED_DIR / "jan to may police violation_anonymized791b166.csv"`.
  Directory constants (`DATA_DIR`, `PROCESSED_DIR`, `REPORTS_DIR`) moved above
  `DEFAULT_SOURCE_CSV` to resolve import-order dependency. Verified on current
  machine; resolves correctly from any working directory.

### New: `src/data_service.py`

Centralised data access layer for Phase 4 Streamlit application.

- Loads all 7 pre-computed CSVs once at startup via `@st.cache_data`.
- Paths derived from `__file__` — portable on any machine.
- Public query API:
  - `get_hotspots(station, band, hotspot_type)` — enforcement_priorities joined
    with pcis_scores and emerging status.
  - `get_priority_hotspots(top_n, station)` — top-N by priority_score.
  - `get_emerging_hotspots(status)` — drift-filtered emerging hotspots.
  - `get_repeat_offenders(top_n)` — offender-score sorted vehicle list.
  - `get_patrol_routes(station)` — route stops, optionally station-filtered.
  - `get_station_summary()` — aggregated station-level risk table.
  - `get_roi_data()` — 8 ROI simulation scenarios.
  - `city_kpis()` — scalar KPI dict for Command Center header.
  - `list_stations()` / `list_bands()` — dropdown population helpers.

### New: `app.py`

Streamlit multi-page entry point.

- Global dark theme CSS (Inter font, `#0d1117` background, `#58a6ff` accents).
- Sidebar navigation with branding.
- Landing page with quick-launch cards and dataset summary strip.

### New: `pages/1_Command_Center.py`

Citywide situation awareness dashboard.

- 5-metric KPI strip: Total Hotspots, Critical, Emerging, Repeat Offenders,
  Patrol Routes.
- Second KPI row: Total Violations, Highest Risk Station, City #1 Hotspot,
  City #1 Priority Score.
- Top-10 stations horizontal bar chart (Plotly), colour-coded by critical count.
- Priority band donut chart (Plotly) with centre annotation.
- Top-20 critical hotspot table with `st.column_config` formatting.
- Full station risk summary (collapsible expander).
- Quick navigation links.

### New: `pages/3_City_Risk_Map.py`

Interactive Folium enforcement hotspot map.

- All 701 hotspots rendered as circle markers, colour-coded by priority band:
  Critical=`#ff4444` (r=14) | High=`#ff8c00` (r=11) |
  Medium=`#ffd700` (r=8) | Low=`#32cd32` (r=6).
- Dark CartoDB tile layer; satellite layer toggle via LayerControl.
- Sidebar filters: police station, priority band (multi-select), hotspot type
  (multi-select).
- Toggle: heatmap overlay weighted by priority_score.
- Toggle: MarkerCluster for dense areas.
- Rich popup per hotspot: name, type, station, band, city rank, priority score,
  PCIS score, drift score, drift status, violation count.
- Summary KPI strip above map: showing count, critical, high, emerging, violations.
- Click-to-detail panel below map.
- Expandable filtered hotspot table (sortable by priority score).



### New modules

- **`src/enforcement_priority.py`**: Enforcement Priority Engine.
  - Reads `pcis_scores.csv`, `emerging_hotspots.csv`, `repeat_offenders.csv`.
  - Composites four 0–100 normalised signals:
    `0.40·PCIS + 0.25·drift_score + 0.20·severity_norm + 0.15·repeat_density_norm`.
  - Assigns percentile-based priority bands (Critical/High/Medium/Low).
  - Produces city-wide and station-wise rankings.
  - Output: `data/processed/enforcement_priorities.csv` (701 hotspots).

- **`src/patrol_planner.py`**: Patrol Route Planner.
  - Reads `enforcement_priorities.csv`.
  - Groups hotspots by police station (54 stations).
  - Builds greedy nearest-neighbour route per station, starting at the
    highest-priority hotspot.
  - Splits routes exceeding 10 stops into numbered sub-routes.
  - Deduplicates route IDs to prevent abbreviation collisions.
  - Output: `data/processed/patrol_routes.csv` (701 stops / 97 routes).

- **`src/roi_simulator.py`**: ROI Simulator.
  - Reads `enforcement_priorities.csv` and `repeat_offenders.csv`.
  - Runs 8 scenarios over a grid of (additional_officers,
    hotspot_reduction_pct, enforcement_intensity).
  - Estimates: projected PCIS reduction, projected hotspot reduction count,
    estimated repeat offender reduction.
  - All assumptions documented in module docstring and CSV output.
  - Output: `data/processed/roi_simulation.csv` (8 scenarios).

### New runner

- **`run_phase3.py`**: Phase 3 batch entry point.
  - Validates prerequisites before running.
  - Orchestrates all three engines in sequence.
  - Writes `reports/phase3_summary.txt`.

### Phase 3 run results

| Metric | Value |
|---|---|
| Hotspots ranked | 701 |
| Priority score range | 7.56–70.74 |
| Critical band | 106 |
| High band | 245 |
| Medium band | 210 |
| Low band | 140 |
| Patrol routes | 97 across 54 stations |
| ROI scenarios | 8 |

City-wide rank #1: **BTP080 - NR Road, SP Road Junction** (City Market),
priority_score=70.74.



## 2026-06-18 17:20 IST — Phase 2 Quality Review Corrections

Six corrections applied following the Phase 2 quality review. Phase 1 re-run
required by F1. Phase 2 fully re-run to regenerate all three output CSVs.

### F1 — MAIN_ROAD_KEYWORDS contamination fixed (`src/config.py`)
- Removed `"NO PARKING"` and `"WRONG PARKING"` from `MAIN_ROAD_KEYWORDS`.
- These terms matched **every violation** in the dataset, causing
  `main_road_violation_share = 1.0` for all 701 hotspots (a constant, not a
  feature).
- Added explicit obstruction-specific terms: `"PARKING IN A MAIN ROAD"`,
  `"PARKING NEAR ROAD CROSSING"`, `"PARKING ON FOOTPATH"`,
  `"PARKING NEAR BUSTOP"`, `"DOUBLE PARKING"`.
- **Phase 1 re-run** to regenerate `hotspot_summary.csv` with corrected
  `main_road_violation_share` values.
- **Impact:** `pcis_main_road` component now ranges 0–100 (was fixed at 100).
  PCIS floor dropped from 29.91 → 18.29. Mean score 59.89 → 52.79.

### F2 — Percentile-based PCIS band thresholds (`src/pcis_engine.py`, `src/config.py`)
- Replaced fixed absolute band cuts (25/50/75) with percentile-based cuts
  derived from the actual score distribution at runtime.
- New constants: `PCIS_BAND_CRITICAL_PCT=85`, `PCIS_BAND_HIGH_PCT=50`,
  `PCIS_BAND_MEDIUM_PCT=20`.
- Added `pcis_percentile` column to output.
- **Impact:** All four bands now populated. Before: Critical=85, High=470,
  Medium=146, **Low=0**. After: Critical=107, High=245, Medium=211, **Low=138**.

### F3 — Drift score normalised to 0–100 (`src/emerging_hotspots.py`, `src/config.py`)
- Raw drift Z-score capped at `DRIFT_MAX_SCORE = 10.0` (configurable).
- Capped value mapped to 0–100: `drift_score = (capped + 10) / 20 × 100`.
- Raw Z-score preserved as `drift_score_raw` column.
- **Impact:** Drift score now compositable with PCIS for Phase 3. Before:
  unbounded (max 13.81). After: 0–100.

### F4 — Minimum activity gate for emergence (`src/config.py`, `src/emerging_hotspots.py`)
- Added `DRIFT_MIN_RECENT_MEAN = 5.0` threshold.
- Hotspots where `mean_weekly_recent < 5.0` cannot be "Emerging"; classified
  as "Low Activity" instead.
- **Impact:** 8 false-positive zero-prior-baseline sites removed from Emerging.
  New "Low Activity" status introduced. Emerging count: 40 → 25.

### F5 — Repeat offender threshold raised and score normalised (`src/config.py`, `src/repeat_offender.py`)
- `REPEAT_OFFENDER_MIN_VIOLATIONS` raised from 5 to 8.
- `offender_score` now min-max normalised to 0–100 across the flagged
  population; raw value preserved as `offender_score_raw`.
- **Impact:** Flagged vehicles: 1,276 → 287 (−77.5%). Median violations P50:
  6 → 10. Low-signal noise at threshold eliminated.

### F6 — Validation status filter (`src/config.py`, all three Phase 2 engines)
- Added `VALID_STATUSES = {"APPROVED", "PROCESSING", "UNKNOWN"}`.
- `REJECTED` and `DUPLICATE` records excluded from PCIS aggregation, repeat
  offender counting, and drift trend detection.
- **Impact:** ~12% of records (REJECTED) removed from scoring. Top offender
  violation count corrected: FKN00GL17863 41 → 33 (8 rejected violations
  excluded).

### Phase 1 + Phase 2 re-run results

Phase 1 re-run output (corrected `main_road_violation_share`):
- 298,450 records, 303 named hotspots, 398 DBSCAN hotspots — counts unchanged.

Phase 2 re-run output:

| Engine | Before | After |
|---|---|---|
| PCIS hotspots scored | 701 | 701 |
| PCIS score range | 29.91–93.29 | 18.29–92.54 |
| PCIS Low band | 0 | 138 |
| Repeat offenders | 1,276 | 287 |
| Emerging hotspots | 40 | 25 |
| Low Activity (new) | — | 14 |



## 2026-06-16 18:10 IST

- Created mandatory project documentation files:
  - `ARCHITECTURE.md`
  - `PROJECT_HANDOFF.md`
  - `TASKS.md`
  - `CHANGELOG.md`
- Established the MVP phase order.
- Documented the initial architecture and dataset constraints.
- Recorded environment constraints: Python is available, but `pandas` and `scikit-learn` are not installed.
- Selected a dependency-light Phase 1 implementation using standard-library CSV processing and local haversine DBSCAN.

## 2026-06-16 18:25 IST

- Implemented Phase 1 batch pipeline:
  - `src/config.py`
  - `src/data_loader.py`
  - `src/preprocessing.py`
  - `src/hotspot_engine.py`
  - `run_phase1.py`
- Added project setup files:
  - `README.md`
  - `requirements.txt`
  - `src/__init__.py`
- Generated Phase 1 outputs:
  - `data/processed/cleaned_violations_sample.csv`
  - `data/processed/named_hotspots.csv`
  - `data/processed/unknown_hotspots.csv`
  - `data/processed/hotspot_summary.csv`
  - `reports/phase1_summary.txt`
- Full dataset run completed:
  - Raw records scanned: 298,450
  - Clean records retained: 298,450
  - Records dropped: 0
  - Named hotspots generated: 303
  - Unknown DBSCAN hotspots generated: 398
- Verified module imports with `python -B`.
- Noted that direct `py_compile` attempted to write `.pyc` files and hit a local access issue, so import validation was used instead.

## 2026-06-17 21:00 IST — Phase 1 Blocker Fixes

Architecture review identified four blockers before Phase 2 could be implemented. All fixed:

### Blocker 1 — Remove CLEANED_SAMPLE_LIMIT
- Removed `CLEANED_SAMPLE_LIMIT` constant from `src/config.py`.
- Added `write_cleaned_full()` to `run_phase1.py` that writes all cleaned records (no row cap) to `data/processed/cleaned_violations_full.csv`.
- Retained capped inspection sample (`cleaned_violations_sample.csv`) as a separate file with a configurable `--sample-limit` CLI argument (default 5000).

### Blocker 2 — Stabilise Hotspot IDs
- Replaced rank-based sequential IDs (`N-0001`, `U-0005`, …) in `src/hotspot_engine.py` with deterministic SHA-1 hash of `(hotspot_name, police_station)`.
- New format: `<prefix>-<8 hex digits>` (e.g. `N-3fa2c1b0`).
- IDs are now stable across re-runs and data size changes.
- Added `_stable_hotspot_id()` helper to `hotspot_engine.py`; added `import hashlib`.

### Blocker 3 — Phase 2 Configuration
- Added the following constant groups to `src/config.py`:
  - **PCIS weights**: `PCIS_WEIGHT_*` (five features, sum = 1.0)
  - **Drift parameters**: `DRIFT_RECENT_WEEKS`, `DRIFT_PRIOR_WEEKS`, `DRIFT_EPSILON`, `DRIFT_EMERGING_THRESHOLD`, `DRIFT_COOLING_THRESHOLD`
  - **Repeat offender thresholds**: `REPEAT_OFFENDER_MIN_VIOLATIONS`, `REPEAT_OFFENDER_MIN_HOTSPOTS`
  - **Phase 2 output paths**: `PHASE2_PCIS_CSV`, `PHASE2_REPEAT_OFFENDERS_CSV`, `PHASE2_EMERGING_HOTSPOTS_CSV`, `PHASE2_CLEANED_FULL_CSV`

### Blocker 4 — Full Cleaned Dataset
- `run_phase1.py` now writes `data/processed/cleaned_violations_full.csv` containing all 298,450 cleaned records (previously only a 5,000-row sample was persisted).
- Phase 1 re-run completed to produce full cleaned CSV and refreshed hotspot IDs.

## 2026-06-17 21:30 IST — Phase 2 Implementation

### New modules

- **`src/pcis_engine.py`**: PCIS Scoring Engine.
  - Reads `hotspot_summary.csv`.
  - Computes `daily_density = violation_count / active_days`.
  - Computes `repeat_offender_ratio = repeat_vehicle_count / unique_vehicle_count`.
  - Applies the frozen PCIS formula (weighted percentile-rank composite).
  - Adds columns: `daily_density`, `repeat_offender_ratio`, `pcis_daily_density`, `pcis_peak_hour`, `pcis_large_vehicle`, `pcis_main_road`, `pcis_repeat_offender`, `pcis_score`, `pcis_band`.
  - Output: `data/processed/pcis_scores.csv`.

- **`src/repeat_offender.py`**: Repeat Offender Intelligence.
  - Scans `cleaned_violations_full.csv`.
  - Flags vehicles with total violations >= 5 AND distinct hotspots >= 2.
  - Computes `offender_score = violations × log₂(distinct_hotspots + 1)`.
  - Output: `data/processed/repeat_offenders.csv`.

- **`src/emerging_hotspots.py`**: Emerging Hotspot Detection.
  - Scans `cleaned_violations_full.csv` and resolves weekly violation counts per hotspot.
  - Applies drift Z-score formula over configurable recent (4w) and prior (4w) windows.
  - Classifies each hotspot as Emerging / Stable / Cooling / Insufficient Data.
  - Output: `data/processed/emerging_hotspots.csv`.

### New runner

- **`run_phase2.py`**: Phase 2 batch entry point.
  - Validates prerequisites before running.
  - Orchestrates all three engines in sequence.
  - Prints progress and summary to console.
  - Writes `reports/phase2_summary.txt`.
