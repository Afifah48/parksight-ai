import sys
import os
import math
from typing import Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np

# Allow importing from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_service import (
    city_kpis,
    get_hotspots,
    get_emerging_hotspots,
    get_repeat_offenders,
    get_patrol_routes,
    get_roi_data,
)
from src.recommendation_engine import generate_recommendations

app = FastAPI(title="ParkSight AI V3 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _df_to_records(df):

    df = df.copy()

    # Replace infinities
    df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # Convert ALL NaNs to None
    records = []

    for row in df.to_dict(orient="records"):

        cleaned = {}

        for k, v in row.items():

            if pd.isna(v):
                cleaned[k] = None
            else:
                cleaned[k] = v

        records.append(cleaned)

    return records

@app.get("/api/kpis")
def api_kpis():
    return city_kpis()

@app.get("/api/hotspots")
def api_hotspots(station: Optional[str] = None, band: Optional[str] = None):

    if station == "All Stations":
        station = None

    df = get_hotspots(station=station, band=band)

    df["mean_weekly_recent"] = df["mean_weekly_recent"].fillna(0)
    df["mean_weekly_prior"] = df["mean_weekly_prior"].fillna(0)

    return _df_to_records(df)

@app.get("/api/emerging")
def api_emerging(status: str = "Emerging"):
    df = get_emerging_hotspots(status=status)
    return _df_to_records(df)

@app.get("/api/offenders")
def api_offenders(top_n: Optional[int] = 20):
    df = get_repeat_offenders(top_n=top_n)
    return _df_to_records(df)

@app.get("/api/recommendations")
def api_recommendations(station: Optional[str] = None):
    if station == 'All Stations':
        station = None
    # Fix potential NaN inside dict
    recs = generate_recommendations(station=station)
    
    # Quick fix to sanitize NaNs in expected_impact
    if "expected_impact" in recs:
        for k, v in recs["expected_impact"].items():
            if isinstance(v, float) and math.isnan(v):
                recs["expected_impact"][k] = None
    return recs

@app.get("/api/routes")
def api_routes(station: Optional[str] = None):
    if station == 'All Stations':
        station = None
    df = get_patrol_routes(station=station)
    return _df_to_records(df)

@app.get("/api/roi")
def api_roi():
    df = get_roi_data()
    return _df_to_records(df)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
