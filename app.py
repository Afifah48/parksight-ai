"""
app.py
======
Streamlit entry point for the AI Parking Intelligence & Enforcement Planning System.

Run with:
    streamlit run app.py

Multi-page structure is handled automatically by Streamlit via the pages/ directory.
This file renders the home / landing screen and configures global app settings.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be the first Streamlit call in the entry point.
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Parking Intelligence & Enforcement Planning",
    page_icon="🚔",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "AI Parking Intelligence & Enforcement Planning System\n\n"
            "Hackathon prototype — PS1: Poor Visibility on Parking-Induced Congestion.\n\n"
            "Powered by 298,450 violation records across Bengaluru."
        )
    },
)

# ---------------------------------------------------------------------------
# Global CSS — consistent dark theme, typography, KPI card styles.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* ---- Google Font ---- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ---- App background ---- */
    .stApp {
        background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
        color: #e6edf3;
    }

    /* ---- Sidebar ---- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
        border-right: 1px solid #30363d;
    }

    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label {
        color: #8b949e !important;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    /* ---- KPI metric cards ---- */
    [data-testid="stMetric"] {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 18px 20px;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #58a6ff;
        box-shadow: 0 0 20px rgba(88, 166, 255, 0.12);
    }
    [data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 0.78rem !important;
        font-weight: 500 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    [data-testid="stMetricValue"] {
        color: #f0f6fc !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }

    /* ---- Section headers ---- */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #58a6ff;
        border-bottom: 1px solid #30363d;
        padding-bottom: 8px;
        margin-bottom: 16px;
        margin-top: 8px;
    }

    /* ---- Priority band badges ---- */
    .band-critical { color: #ff6b6b; font-weight: 700; }
    .band-high     { color: #ffa94d; font-weight: 600; }
    .band-medium   { color: #ffd43b; font-weight: 600; }
    .band-low      { color: #69db7c; font-weight: 500; }

    /* ---- Dataframe ---- */
    [data-testid="stDataFrame"] {
        border: 1px solid #30363d;
        border-radius: 8px;
    }

    /* ---- Selectbox / multiselect ---- */
    [data-testid="stSelectbox"] > div,
    [data-testid="stMultiSelect"] > div {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
    }

    /* ---- Tabs ---- */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent;
        border-bottom: 1px solid #30363d;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8b949e;
        font-size: 0.88rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        color: #58a6ff !important;
        border-bottom-color: #58a6ff !important;
    }

    /* ---- Plotly chart container ---- */
    .js-plotly-plot {
        border-radius: 10px;
        overflow: hidden;
    }

    /* ---- Alert / info boxes ---- */
    .stAlert {
        border-radius: 8px;
    }

    /* ---- Scrollbar ---- */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0d1117; }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #58a6ff; }

    /* ---- Hide Streamlit default header ---- */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — application branding + navigation guide
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 12px 0 20px;">
            <div style="font-size:2.2rem;">🚔</div>
            <div style="font-size:1.05rem; font-weight:700; color:#f0f6fc;
                        line-height:1.3; margin-top:6px;">
                AI Parking<br>Intelligence
            </div>
            <div style="font-size:0.72rem; color:#58a6ff; margin-top:4px;
                        letter-spacing:0.1em; text-transform:uppercase;">
                Enforcement Planning System
            </div>
        </div>
        <hr style="border:none; border-top:1px solid #30363d; margin:0 0 16px;">
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**NAVIGATION**")
    st.page_link("app.py",                          label="🏠 Home")
    st.page_link("pages/1_Command_Center.py",        label="📊 Command Center")
    st.page_link("pages/2_Action_Center.py",         label="⚡ Action Center")
    st.page_link("pages/3_City_Risk_Map.py",         label="🗺️ City Risk Map")

    st.markdown("<hr style='border:none;border-top:1px solid #30363d;margin:8px 0;'>",
                unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.7rem;color:#444d56;text-align:center;"
        "padding-top:8px;'>Bengaluru BTP · 298,450 Records<br>"
        "Nov 2023 – Apr 2024</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Home landing page
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div style="text-align:center; padding: 48px 0 32px;">
        <div style="font-size:3.5rem; margin-bottom:12px;">🚔</div>
        <h1 style="font-size:2.4rem; font-weight:700; color:#f0f6fc; margin:0;">
            AI Parking Intelligence &
        </h1>
        <h1 style="font-size:2.4rem; font-weight:700;
                   background: linear-gradient(90deg, #58a6ff, #79c0ff);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                   margin:0 0 16px;">
            Enforcement Planning System
        </h1>
        <p style="color:#8b949e; font-size:1.05rem; max-width:640px; margin:0 auto 32px;">
            Converts 298,450 Bengaluru parking violation records into actionable
            enforcement intelligence — hotspot maps, patrol routes, emerging threat
            alerts, and repeat offender profiling.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Quick-launch cards
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown(
        """
        <a href="/Command_Center" target="_self" style="text-decoration:none;">
        <div style="background:rgba(22,27,34,0.9);border:1px solid #30363d;
                    border-radius:14px;padding:24px;cursor:pointer;
                    transition:border-color 0.2s;"
             onmouseover="this.style.borderColor='#58a6ff'"
             onmouseout="this.style.borderColor='#30363d'">
            <div style="font-size:2rem;margin-bottom:10px;">📊</div>
            <div style="font-size:1rem;font-weight:600;color:#f0f6fc;
                        margin-bottom:6px;">Command Center</div>
            <div style="font-size:0.82rem;color:#8b949e;">
                Citywide KPIs, station leaderboard, and critical hotspot overview.
                Start here for the situation picture.
            </div>
        </div>
        </a>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <a href="/Action_Center" target="_self" style="text-decoration:none;">
        <div style="background:rgba(22,27,34,0.9);border:1px solid #30363d;
                    border-radius:14px;padding:24px;cursor:pointer;
                    transition:border-color 0.2s;"
             onmouseover="this.style.borderColor='#f85149'"
             onmouseout="this.style.borderColor='#30363d'">
            <div style="font-size:2rem;margin-bottom:10px;">⚡</div>
            <div style="font-size:1rem;font-weight:600;color:#f0f6fc;
                        margin-bottom:6px;">Action Center</div>
            <div style="font-size:0.82rem;color:#8b949e;">
                Today's top enforcement actions, emerging threats, patrol
                deployments, and offender targets — operational command.
            </div>
        </div>
        </a>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <a href="/City_Risk_Map" target="_self" style="text-decoration:none;">
        <div style="background:rgba(22,27,34,0.9);border:1px solid #30363d;
                    border-radius:14px;padding:24px;cursor:pointer;"
             onmouseover="this.style.borderColor='#69db7c'"
             onmouseout="this.style.borderColor='#30363d'">
            <div style="font-size:2rem;margin-bottom:10px;">🗺️</div>
            <div style="font-size:1rem;font-weight:600;color:#f0f6fc;
                        margin-bottom:6px;">City Risk Map</div>
            <div style="font-size:0.82rem;color:#8b949e;">
                Interactive map of all 701 enforcement hotspots across Bengaluru,
                colour-coded by priority band.
            </div>
        </div>
        </a>
        """,
        unsafe_allow_html=True,
    )


st.markdown("<br>", unsafe_allow_html=True)

# Dataset summary strip
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Records", "298,450")
with c2:
    st.metric("Total Hotspots", "701")
with c3:
    st.metric("Police Stations", "54")
with c4:
    st.metric("Data Period", "Nov 23 – Apr 24")
