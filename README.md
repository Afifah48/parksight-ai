# AI Parking Intelligence & Enforcement Planning System

Hackathon prototype for PS1: Poor Visibility on Parking-Induced Congestion.

The system converts parking violation history into hotspot intelligence, emerging hotspot alerts, congestion-impact proxies, repeat offender intelligence, enforcement priorities, patrol planning, and intervention simulation.

## Current Status

Phase 1 is implemented as a local batch pipeline:

- data loading
- data cleaning
- feature engineering
- named hotspot aggregation
- DBSCAN discovery for `No Junction` records

## Run Phase 1

```powershell
python run_phase1.py
```

Optional custom CSV path:

```powershell
python run_phase1.py --input "C:\path\to\violations.csv"
```

Outputs are written to:

```text
data/processed/
reports/
```

