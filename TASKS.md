# Tasks

## Phase 1: Data Foundation And Hotspot Intelligence

- [x] Confirm source dataset path.
- [x] Inspect available columns.
- [x] Establish mandatory documentation files.
- [x] Implement CSV data loader.
- [x] Implement schema validation.
- [x] Implement data cleaning.
- [x] Implement feature engineering.
- [x] Implement named junction hotspot aggregation.
- [x] Implement DBSCAN hotspot discovery for `No Junction` records.
- [x] Export processed Phase 1 datasets.
- [x] Generate Phase 1 summary report.
- [x] Validate Phase 1 pipeline on the supplied dataset.

## Phase 1 — Blocker Fixes (pre-Phase 2)

- [x] Remove `CLEANED_SAMPLE_LIMIT` — `write_cleaned_full()` writes all records to `cleaned_violations_full.csv`.
- [x] Stabilise hotspot IDs — SHA-1 hash of `(hotspot_name, police_station)`, format `<prefix>-<8 hex digits>`.
- [x] Add Phase 2 configuration constants to `src/config.py`.
- [x] Ensure full cleaned dataset is available via Phase 1 re-run.

## Phase 2: Intelligence Engines

- [x] Check architecture consistency for Phase 2.
- [x] Implement PCIS scoring engine (`src/pcis_engine.py`).
- [x] Implement repeat offender intelligence (`src/repeat_offender.py`).
- [x] Implement emerging hotspot detection (`src/emerging_hotspots.py`).
- [x] Implement Phase 2 batch runner (`run_phase2.py`).
- [x] Export Phase 2 outputs (initial run).
- [x] Generate Phase 2 summary report.

## Phase 2 — Quality Review Corrections

- [x] **F1** — Fix `MAIN_ROAD_KEYWORDS` contamination: removed `"NO PARKING"` and `"WRONG PARKING"` from `src/config.py`; re-ran Phase 1 to regenerate `hotspot_summary.csv` with corrected `main_road_violation_share`.
- [x] **F2** — Replace static PCIS band thresholds (25/50/75) with percentile-based cuts in `src/pcis_engine.py` (Critical=top 15%, High=50–85th, Medium=20–50th, Low=bottom 20%).
- [x] **F3** — Normalise drift score to 0–100 in `src/emerging_hotspots.py`; preserve raw Z-score as `drift_score_raw`; cap raw at `DRIFT_MAX_SCORE = 10.0`.
- [x] **F4** — Add `DRIFT_MIN_RECENT_MEAN = 5.0` gate: hotspots below threshold classified "Low Activity" not "Emerging".
- [x] **F5** — Raise `REPEAT_OFFENDER_MIN_VIOLATIONS` from 5 to 8 in `src/config.py`; normalise `offender_score` to 0–100 in `src/repeat_offender.py`; preserve raw as `offender_score_raw`.
- [x] **F6** — Add `VALID_STATUSES` filter in `src/config.py`; exclude `REJECTED` and `DUPLICATE` records in all three Phase 2 engines.
- [x] Re-run Phase 1 with corrected `MAIN_ROAD_KEYWORDS`.
- [x] Re-run Phase 2 — regenerate `pcis_scores.csv`, `repeat_offenders.csv`, `emerging_hotspots.csv`.
- [x] Produce Before vs After comparison report.
- [x] Update `PROJECT_HANDOFF.md`, `TASKS.md`, `CHANGELOG.md`.

## Phase 3: Enforcement Planning

- [x] Implement enforcement priority engine (`src/enforcement_priority.py`).
- [x] Implement patrol planner (`src/patrol_planner.py`).
- [x] Implement ROI simulator (`src/roi_simulator.py`).
- [x] Implement Phase 3 batch runner (`run_phase3.py`).
- [x] Export Phase 3 outputs (`enforcement_priorities.csv`, `patrol_routes.csv`, `roi_simulation.csv`).
- [x] Generate Phase 3 summary report (`reports/phase3_summary.txt`).
- [x] Update `PROJECT_HANDOFF.md`, `TASKS.md`, `CHANGELOG.md`.

## Phase 4: Streamlit Dashboard

- [x] Fix deployment blocker — `src/config.py` hardcoded path removed.
- [x] Build `src/data_service.py` — centralised CSV loading with `@st.cache_data`.
- [x] Build `app.py` — entry point, global theme, sidebar, landing page.
- [x] Build `pages/1_Command_Center.py` — KPIs, station leaderboard, donut, top-20 table.
- [x] Build `pages/3_City_Risk_Map.py` — Folium map, 701 hotspots, band colours, filters, popups.
- [x] Build `src/recommendation_engine.py` — 4 recommendation types, explainable, rule-based.
- [x] Build `pages/2_Action_Center.py` — 5-section operational command hub.
- [x] Build `pages/6_Enforcement_Priority_Rankings.py` — full sortable priority table, score decomposition, station drill-down.
- [x] Build `pages/7_Patrol_Planner.py` — Folium route map, sequence table, priority band profile.
- [x] Build `pages/8_ROI_Simulator.py` — what-if modeling, 8 scenarios, officer slider, PCIS waterfall chart.
- [x] Build `pages/4_Emerging_Hotspot_Alerts.py`.
- [x] Build `pages/5_Repeat_Offender_Intelligence.py`.

## Documentation

- [x] Create `ARCHITECTURE.md`.
- [x] Create `PROJECT_HANDOFF.md`.
- [x] Create `TASKS.md`.
- [x] Create `CHANGELOG.md`.
- [x] Keep documentation updated after Phase 1 milestone.
- [x] Keep documentation updated after Phase 2 milestone.
- [x] Keep documentation updated after Phase 2 corrections.
- [x] Keep documentation updated after Phase 3 milestone.

