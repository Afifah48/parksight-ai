import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_service import get_emerging_hotspots, get_hotspots, list_stations

st.set_page_config(page_title="Emerging Hotspot Alerts", page_icon="📈", layout="wide")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0d1117 0%, #161b22 100%); color: #e6edf3; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#161b22 0%,#0d1117 100%);
                                  border-right:1px solid #30363d; }
    [data-testid="stMetric"] { background:rgba(22,27,34,0.85); border:1px solid #30363d;
                                 border-radius:12px; padding:18px 20px; }
    [data-testid="stMetricLabel"] { color:#8b949e !important; font-size:0.76rem !important;
                                     font-weight:500 !important; text-transform:uppercase;
                                     letter-spacing:0.06em; }
    [data-testid="stMetricValue"] { color:#f0f6fc !important; font-size:1.9rem !important;
                                     font-weight:700 !important; }
    .section-header { font-size:1.05rem; font-weight:600; color:#58a6ff;
                       border-bottom:1px solid #30363d; padding-bottom:8px;
                       margin:20px 0 14px; }
    .kpi-critical [data-testid="stMetricValue"] { color:#ff6b6b !important; }
    .kpi-emerging [data-testid="stMetricValue"] { color:#ffa94d !important; }
    .kpi-offender [data-testid="stMetricValue"] { color:#da77f2 !important; }
    #MainMenu { visibility:hidden; } footer { visibility:hidden; } header { visibility:hidden; }
    ::-webkit-scrollbar { width:6px; } ::-webkit-scrollbar-thumb { background:#30363d; border-radius:3px; }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("📈 Emerging Hotspot Alerts")
st.markdown("Identify hotspots where violation rates are accelerating.")

col1, col2 = st.columns(2)
with col1:
    status_filter = st.selectbox("Drift Status", ["Emerging", "Stable", "Cooling", "Low Activity", "Insufficient Data"])
with col2:
    stations = ["All Stations"] + list_stations()
    station_filter = st.selectbox("Police Station Filter", stations)

# Load data
merged_df = get_emerging_hotspots(status_filter)

if station_filter != "All Stations":
    merged_df = merged_df[merged_df["police_station"] == station_filter]

if merged_df.empty:
    st.info(f"No hotspots found matching status '{status_filter}' and station '{station_filter}'.")
else:
    # Calculate % change
    merged_df["pct_change"] = ((merged_df["mean_weekly_recent"] - merged_df["mean_weekly_prior"]) / merged_df["mean_weekly_prior"].replace(0, 1)) * 100
    
    st.metric("Total Hotspots in View", len(merged_df))
    
    # Format for display
    display_df = merged_df[["hotspot_name", "police_station", "drift_score", "mean_weekly_recent", "mean_weekly_prior", "pct_change", "total_violations"]].copy()
    display_df = display_df.rename(columns={
        "hotspot_name": "Hotspot",
        "police_station": "Station",
        "drift_score": "Drift Score (0-100)",
        "mean_weekly_recent": "Recent Mean (per wk)",
        "mean_weekly_prior": "Prior Mean (per wk)",
        "pct_change": "% Change",
        "total_violations": "Total Violations"
    })
    
    st.dataframe(
        display_df.style.format({
            "Drift Score (0-100)": "{:.1f}",
            "Recent Mean (per wk)": "{:.1f}",
            "Prior Mean (per wk)": "{:.1f}",
            "% Change": "{:+.1f}%"
        }),
        use_container_width=True
    )
    
    if status_filter in ["Emerging", "Cooling"]:
        fig = px.bar(
            merged_df.head(20),
            x="drift_score",
            y="hotspot_name",
            orientation="h",
            title=f"Top 20 {status_filter} Hotspots by Drift Score",
            color="drift_score",
            color_continuous_scale="Reds" if status_filter == "Emerging" else "Greens"
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
