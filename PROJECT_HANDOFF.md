# Project Handoff

## Current Status

Phase 4 implementation complete. All 8 screens are fully implemented and functional.
Application now functions as a Traffic Enforcement Command Center.
The project has reached its final MVP state and is ready for production deployment.

### Phase 4 Day 4 Completion (2026-06-19)

Intelligence detail pages built:
- `pages/4_Emerging_Hotspot_Alerts.py` — drill-down into drift-detected acceleration, status filtering.
- `pages/5_Repeat_Offender_Intelligence.py` — vehicle-level search, profiling, and distribution charts.

### Phase 4 Day 3 Completion (2026-06-19)

High Impact Operational Pages built:

Files created:
- `pages/6_Enforcement_Priority_Rankings.py` — full sortable/filterable ranking table, score decomposition, component leaderboards.
- `pages/7_Patrol_Planner.py` — Folium route visualization, stop sequencing, priority profiling.
- `pages/8_ROI_Simulator.py` — interactive what-if resource deployment modelling, PCIS waterfall.

### Phase 4 Day 2 Completion (2026-06-19)

Action Center and recommendation engine built.

Files created:
- `src/recommendation_engine.py` — deterministic rule engine, 4 recommendation types
- `pages/2_Action_Center.py` — 5-section operational decision hub

Files modified:
- `app.py` — 3-card landing (Command Center, Action Center, City Risk Map)

Application identity shift:
- Command Center = situational awareness (what is happening)
- Action Center = operational decisions (what to do right now)
- City Risk Map = spatial context (where it is happening)

### Phase 4 Day 1 Completion (2026-06-19)

Deployment blocker fixed. Application foundation created. Two screens built.

Files created:
- `src/data_service.py` — centralised CSV loading layer with `@st.cache_data`
- `app.py` — Streamlit entry point with global dark theme and sidebar navigation
- `pages/1_Command_Center.py` — KPI strip, station leaderboard, priority donut, top-20 table
- `pages/3_City_Risk_Map.py` — interactive Folium map of all 701 hotspots with filters and popups

Deployment blocker resolved:
- `src/config.py` `DEFAULT_SOURCE_CSV` converted from hardcoded absolute path to
  portable relative path derived from `PROCESSED_DIR`. Verified on this machine;
  works on any machine without modification.


### Architecture Update (2026-06-18)

The application architecture has been redesigned with a key structural
change: introduction of the **Action Center** as a central hub that
synthesises all intelligence signals (PCIS, drift, repeat offenders, patrol
routes) into per-station actionable recommendations.

Screen hierarchy updated from 7 to 8 screens:

```
Command Center --> ACTION CENTER --> Detail / Execution screens
```

New serving-layer components defined:
- `src/data_service.py` — in-process CSV data service with caching.
- `src/recommendation_engine.py` — presentation-layer rule engine generating
  four recommendation types: Deploy Patrol, Emerging Threat Alert, Repeat
  Offender Interception, Resource Allocation Advisory.

### Phase 3 Run Results

| Module | Output | Records |
|---|---|---|
| Enforcement Priority Engine | `enforcement_priorities.csv` | 701 hotspots ranked |
| Patrol Route Planner | `patrol_routes.csv` | 701 stops across 97 routes / 54 stations |
| ROI Simulator | `roi_simulation.csv` | 8 scenarios |

Priority band breakdown:

| Band | Count |
|---|---|
| Critical (top 15%) | 106 |
| High (50-85th pct) | 245 |
| Medium (20-50th pct) | 210 |
| Low (bottom 20%) | 140 |

Top enforcement priority (city-wide rank #1):
**BTP080 - NR Road, SP Road Junction** | City Market | priority_score=70.74

## Completed Milestone: Phase 3

### Phase 3 Outputs Generated

| File | Description |
|---|---|
| `data/processed/enforcement_priorities.csv` | 701 hotspots with priority_score, priority_band, rank_city, rank_station |
| `data/processed/patrol_routes.csv` | 97 patrol routes (nearest-neighbour, anchored at highest-priority hotspot) |
| `data/processed/roi_simulation.csv` | 8 ROI scenarios: officers x reduction% x intensity |
| `reports/phase3_summary.txt` | Top 20 priorities, top patrol routes, ROI table |

### Phase 3 Modules

| Module | Input | Output |
|---|---|---|
| `src/enforcement_priority.py` | `pcis_scores.csv`, `emerging_hotspots.csv`, `repeat_offenders.csv` | `enforcement_priorities.csv` |
| `src/patrol_planner.py` | `enforcement_priorities.csv` | `patrol_routes.csv` |
| `src/roi_simulator.py` | `enforcement_priorities.csv`, `repeat_offenders.csv` | `roi_simulation.csv` |
| `run_phase3.py` | All of the above | All three CSVs + `phase3_summary.txt` |

### Priority Score Formula

```
priority_score = 0.40 x pcis_score
              + 0.25 x drift_score
              + 0.20 x hotspot_severity_norm
              + 0.15 x repeat_offender_density_norm
```

All inputs are normalised to 0-100 before compositing. Bands assigned by
percentile cut (same method as PCIS bands): Critical=top 15%, High=50-85th,
Medium=20-50th, Low=bottom 20%.

## Completed Milestone: Phase 2

### Phase 1 Blocker Fixes

The following blockers were resolved before Phase 2 was built:

| Blocker | Fix |
|---|---|
| `CLEANED_SAMPLE_LIMIT` capped output at 5,000 rows | Removed constant; `run_phase1.py` now calls `write_cleaned_full()` with no row cap, writing `cleaned_violations_full.csv` |
| Rank-based hotspot IDs shuffled on re-runs | Replaced with SHA-1 hash of `(hotspot_name, police_station)`, format `<prefix>-<8 hex digits>` |
| No Phase 2 config constants | Added PCIS weights, drift thresholds, repeat-offender thresholds, Phase 2 output paths to `src/config.py` |
| Full cleaned dataset not persisted | Phase 1 now writes `data/processed/cleaned_violations_full.csv` (all records) |

### Phase 2 Modules

| Module | Input | Output |
|---|---|---|
| `src/pcis_engine.py` | `hotspot_summary.csv` | `pcis_scores.csv` |
| `src/repeat_offender.py` | `cleaned_violations_full.csv` | `repeat_offenders.csv` |
| `src/emerging_hotspots.py` | `cleaned_violations_full.csv` + `hotspot_summary.csv` | `emerging_hotspots.csv` |
| `run_phase2.py` | Both above | All three CSVs + `phase2_summary.txt` |

## Completed Milestone: Phase 1

Phase 1 generated the following outputs (regenerated with stable IDs):

- `data/processed/cleaned_violations_full.csv` -- full 298,450 records
- `data/processed/cleaned_violations_sample.csv` -- inspection sample (5,000 rows)
- `data/processed/named_hotspots.csv`
- `data/processed/unknown_hotspots.csv`
- `data/processed/hotspot_summary.csv`
- `reports/phase1_summary.txt`

Full run metrics:

- Raw records scanned: 298,450
- Clean records retained: 298,450
- Records dropped: 0
- Named junction records: 150,565
- `No Junction` records: 147,885
- Named hotspots generated: 303
- Unknown DBSCAN hotspots generated: 398
- DBSCAN radius: 75 metres
- DBSCAN minimum samples: 20

## Dataset

Source CSV (local copy):

`data/processed/jan to may police violation_anonymized791b166.csv`

Note: Despite the filename, actual `created_datetime` values span November 2023
to April 2024. Drift detection derives its date windows from actual data, not
the filename.

Observed columns used:

- `latitude`, `longitude`, `location`
- `vehicle_number`, `updated_vehicle_number`
- `vehicle_type`, `updated_vehicle_type`
- `violation_type`
- `created_datetime`
- `police_station`
- `junction_name`
- `validation_status`
- `center_code`

## Environment Notes

- Python 3.12.0.
- `pandas` is not installed. All processing uses standard library only.
- `scikit-learn` is not installed. DBSCAN implemented locally using haversine distance.
- Phases 1-3 continue the dependency-light approach.
- Phase 4 (Streamlit app) will require: `streamlit`, `pandas`, `plotly`,
  `folium`, `streamlit-folium`.

## Decisions Frozen

See conversation history for the full architecture review output. Key decisions:

- PCIS formula: `0.30*P(daily_density) + 0.25*P(peak_hour_share) + 0.20*P(large_vehicle_share) + 0.15*P(main_road_share) + 0.10*P(repeat_offender_ratio)` where P = percentile rank.
- Drift formula: `(mean_recent_4w - mean_prior_4w) / (stdev_prior_4w + 1)`, threshold +/-1.5 sigma.
- Repeat offender: min 8 total violations AND min 2 distinct hotspots.
- Hotspot ID format: `<prefix>-<8 hex SHA-1 digits>` derived from `(hotspot_name, police_station)`.
- Architecture: Streamlit-only (Option A). No FastAPI. No React.
- Screen count: 8 (Command Center + Action Center + 6 detail/execution screens).
- Action Center is the operational hub; all other screens are context or drill-down.
- Recommendation engine is a presentation-layer rule engine, not a new analytical model.

## Phase 4 Application Screens

| # | Screen | Purpose | Primary User |
|---|---|---|---|
| 1 | Command Center | Citywide KPIs, station leaderboard, critical hotspot mini-map | Commissioner |
| 2 | **Action Center** | Per-station actionable recommendations (deploy patrol, emerging alerts, offender interception, resource advisory) | Inspector |
| 3 | City Risk Map | Interactive map of 701 hotspots with priority-band colouring | Commissioner, Inspector |
| 4 | Emerging Hotspot Alerts | Drift-detected acceleration drill-down | Inspector |
| 5 | Repeat Offender Intelligence | Vehicle-level search and profiling | Inspector, Patrol Officer |
| 6 | Enforcement Priority Rankings | Full sortable priority table with score decomposition | Inspector, Commissioner |
| 7 | Patrol Planner | Route map with polyline and stop-by-stop table | Patrol Officer, Inspector |
| 8 | ROI Simulator | Interactive what-if resource deployment modelling | Commissioner |

## Next Recommended Task

**Project Complete.** 

The Streamlit Enforcement Command Center is fully implemented and ready for deployment to the target environment. You can run the application with:
`streamlit run app.py`

