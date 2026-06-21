import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_service import get_repeat_offenders, list_stations

st.set_page_config(page_title="Repeat Offender Intelligence", page_icon="🚘", layout="wide")
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
st.title("🚘 Repeat Offender Intelligence")
st.markdown("Identify and profile chronic violators operating across multiple hotspots.")

# Filters
col1, col2, col3 = st.columns(3)
with col1:
    stations = ["All Stations"] + list_stations()
    station_filter = st.selectbox("Filter by Police Station", stations)
with col2:
    search_query = st.text_input("Search Vehicle Number")
with col3:
    min_violations = st.number_input("Minimum Violations", min_value=1, value=8)

df = get_repeat_offenders()

# Apply filters
if station_filter != "All Stations":
    # police_stations is a pipe-separated string
    df = df[df["police_stations"].astype(str).str.contains(station_filter, na=False)]

if search_query:
    df = df[df["vehicle_number"].astype(str).str.contains(search_query.upper(), na=False)]

df = df[df["total_violations"] >= min_violations]

if df.empty:
    st.info("No offenders match the current filters.")
else:
    st.metric("Total Flagged Offenders in View", len(df))

    # Format for display
    display_df = df[[
        "vehicle_number", "total_violations", "distinct_hotspot_count", 
        "offender_score", "active_span_days", "top_violation_type", "police_stations"
    ]].copy()
    
    display_df = display_df.rename(columns={
        "vehicle_number": "Vehicle",
        "total_violations": "Violations",
        "distinct_hotspot_count": "Hotspots Visited",
        "offender_score": "Offender Score (0-100)",
        "active_span_days": "Active Days",
        "top_violation_type": "Top Violation",
        "police_stations": "Stations Active In"
    })
    
    st.dataframe(
        display_df.style.format({
            "Offender Score (0-100)": "{:.1f}",
        }),
        use_container_width=True
    )
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Offender Score Distribution")
        fig = px.histogram(
            df, 
            x="offender_score", 
            nbins=20,
            title="Distribution of Offender Scores",
            color_discrete_sequence=['#9b59b6']
        )
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Violations vs Distinct Hotspots")
        fig2 = px.scatter(
            df,
            x="distinct_hotspot_count",
            y="total_violations",
            color="offender_score",
            size="total_violations",
            hover_data=["vehicle_number"],
            title="Violations vs Hotspots Visited",
            color_continuous_scale="Purples"
        )
        st.plotly_chart(fig2, use_container_width=True)
