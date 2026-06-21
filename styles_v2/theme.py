"""
styles_v2/theme.py
==================
Central design-token registry and global CSS injection for ParkSight AI V2.

Extracted from the V2 screenshot specifications:
- Deep navy/charcoal backgrounds
- Cyan/blue accent system
- Military/ops-grade dark command-center aesthetic
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Color Palette
# ---------------------------------------------------------------------------
COLORS = {
    # Backgrounds
    "bg_primary": "#0a0e1a",
    "bg_secondary": "#0f172a",
    "bg_tertiary": "#111827",
    # Surfaces
    "surface": "#1e293b",
    "surface_alt": "#162032",
    "surface_hover": "#334155",
    "surface_glass": "rgba(15, 23, 42, 0.75)",
    # Borders
    "border": "#1e293b",
    "border_subtle": "#1a2332",
    "border_hover": "#475569",
    "border_active": "#22d3ee",
    # Text
    "text_primary": "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "text_bright": "#f8fafc",
    # Accents
    "accent_cyan": "#22d3ee",
    "accent_blue": "#3b82f6",
    "accent_indigo": "#6366f1",
    "accent_purple": "#a855f7",
    # Status
    "critical": "#ef4444",
    "critical_bg": "rgba(239, 68, 68, 0.12)",
    "high": "#f97316",
    "high_bg": "rgba(249, 115, 22, 0.12)",
    "elevated": "#f59e0b",
    "elevated_bg": "rgba(245, 158, 11, 0.12)",
    "medium": "#eab308",
    "medium_bg": "rgba(234, 179, 8, 0.12)",
    "low": "#22c55e",
    "low_bg": "rgba(34, 197, 94, 0.12)",
    "success": "#22c55e",
    "info": "#3b82f6",
}

# Priority band → color mapping
BAND_COLORS = {
    "Critical": COLORS["critical"],
    "High": COLORS["high"],
    "Medium": COLORS["medium"],
    "Low": COLORS["low"],
}

BAND_BG_COLORS = {
    "Critical": COLORS["critical_bg"],
    "High": COLORS["high_bg"],
    "Medium": COLORS["medium_bg"],
    "Low": COLORS["low_bg"],
}

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
FONT_FAMILY = "'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Fira Code', 'SF Mono', monospace"

FONT_SIZES = {
    "xs": "0.7rem",
    "sm": "0.8rem",
    "base": "0.88rem",
    "md": "1rem",
    "lg": "1.15rem",
    "xl": "1.4rem",
    "2xl": "1.8rem",
    "3xl": "2.2rem",
    "display": "2.8rem",
}

# ---------------------------------------------------------------------------
# Spacing
# ---------------------------------------------------------------------------
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "24px",
    "2xl": "32px",
    "3xl": "48px",
}

# ---------------------------------------------------------------------------
# Plotly chart theme
# ---------------------------------------------------------------------------
def get_plotly_layout(**overrides):
    """Return a Plotly layout dict with the V2 dark theme applied."""
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.4)",
        font=dict(family=FONT_FAMILY, color=COLORS["text_secondary"], size=11),
        margin=dict(l=40, r=20, t=40, b=40),
        xaxis=dict(
            gridcolor="rgba(30, 41, 59, 0.5)",
            zerolinecolor="rgba(30, 41, 59, 0.5)",
            tickfont=dict(size=10, color=COLORS["text_muted"]),
        ),
        yaxis=dict(
            gridcolor="rgba(30, 41, 59, 0.5)",
            zerolinecolor="rgba(30, 41, 59, 0.5)",
            tickfont=dict(size=10, color=COLORS["text_muted"]),
        ),
        legend=dict(
            font=dict(size=10, color=COLORS["text_secondary"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        hoverlabel=dict(
            bgcolor=COLORS["surface"],
            bordercolor=COLORS["border"],
            font=dict(family=FONT_FAMILY, color=COLORS["text_primary"], size=12),
        ),
    )
    layout.update(overrides)
    return layout


# ---------------------------------------------------------------------------
# Global CSS Injection
# ---------------------------------------------------------------------------
def inject_v2_theme():
    """Inject the full V2 dark theme CSS into the Streamlit app."""
    st.markdown(
        f"""
        <style>
        /* ---- Google Fonts ---- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap');

        /* ---- Root Variables ---- */
        :root {{
            --bg-primary: {COLORS['bg_primary']};
            --bg-secondary: {COLORS['bg_secondary']};
            --surface: {COLORS['surface']};
            --border: {COLORS['border']};
            --text-primary: {COLORS['text_primary']};
            --text-secondary: {COLORS['text_secondary']};
            --accent-cyan: {COLORS['accent_cyan']};
            --accent-blue: {COLORS['accent_blue']};
            --critical: {COLORS['critical']};
            --high: {COLORS['high']};
            --medium: {COLORS['medium']};
            --low: {COLORS['low']};
        }}

        /* ---- Global Reset ---- */
        html, body, [class*="css"] {{
            font-family: {FONT_FAMILY};
        }}

        /* ---- App Background ---- */
        .stApp {{
            background: linear-gradient(145deg, {COLORS['bg_primary']} 0%, {COLORS['bg_secondary']} 50%, {COLORS['bg_tertiary']} 100%);
            color: {COLORS['text_primary']};
        }}

        /* ---- Main content area ---- */
        .main .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }}

        /* ---- Sidebar ---- */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {COLORS['bg_secondary']} 0%, {COLORS['bg_primary']} 100%);
            border-right: 1px solid {COLORS['border']};
        }}

        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] label {{
            color: {COLORS['text_secondary']} !important;
            font-size: 0.82rem;
        }}

        /* ---- KPI Metric Cards ---- */
        [data-testid="stMetric"] {{
            background: {COLORS['surface_glass']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            padding: 14px 16px;
            transition: all 0.25s ease;
        }}
        [data-testid="stMetric"]:hover {{
            border-color: {COLORS['accent_cyan']};
            box-shadow: 0 0 20px rgba(34, 211, 238, 0.08);
        }}
        [data-testid="stMetricLabel"] {{
            color: {COLORS['text_muted']} !important;
            font-size: 0.7rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        [data-testid="stMetricValue"] {{
            color: {COLORS['text_bright']} !important;
            font-size: 1.6rem !important;
            font-weight: 700 !important;
        }}
        [data-testid="stMetricDelta"] > div {{
            font-size: 0.75rem !important;
        }}

        /* ---- Section Dividers ---- */
        hr {{
            border: none;
            border-top: 1px solid {COLORS['border']};
            margin: 16px 0;
        }}

        /* ---- Selectbox & Inputs ---- */
        [data-testid="stSelectbox"] > div > div,
        [data-testid="stMultiSelect"] > div > div,
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {{
            background: {COLORS['surface']} !important;
            border: 1px solid {COLORS['border']} !important;
            border-radius: 8px !important;
            color: {COLORS['text_primary']} !important;
        }}

        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {{
            border-color: {COLORS['accent_cyan']} !important;
            box-shadow: 0 0 0 1px {COLORS['accent_cyan']} !important;
        }}

        /* ---- Slider ---- */
        .stSlider > div > div > div > div {{
            background: {COLORS['accent_blue']} !important;
        }}

        /* ---- Tabs ---- */
        .stTabs [data-baseweb="tab-list"] {{
            background: transparent;
            border-bottom: 1px solid {COLORS['border']};
            gap: 0;
        }}
        .stTabs [data-baseweb="tab"] {{
            color: {COLORS['text_muted']};
            font-size: 0.82rem;
            font-weight: 500;
            padding: 8px 20px;
            border-radius: 6px 6px 0 0;
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLORS['accent_cyan']} !important;
            border-bottom: 2px solid {COLORS['accent_cyan']} !important;
            background: rgba(34, 211, 238, 0.05);
        }}

        /* ---- Dataframes ---- */
        [data-testid="stDataFrame"] {{
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            overflow: hidden;
        }}

        /* ---- Expander ---- */
        .streamlit-expanderHeader {{
            background: {COLORS['surface_glass']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            color: {COLORS['text_primary']} !important;
            font-size: 0.88rem;
            font-weight: 600;
        }}

        /* ---- Plotly charts ---- */
        .js-plotly-plot {{
            border-radius: 8px;
            overflow: hidden;
        }}

        /* ---- Scrollbar ---- */
        ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
        ::-webkit-scrollbar-track {{ background: {COLORS['bg_primary']}; }}
        ::-webkit-scrollbar-thumb {{ background: {COLORS['border']}; border-radius: 3px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: {COLORS['accent_cyan']}; }}

        /* ---- Hide Streamlit defaults ---- */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header {{ visibility: hidden; }}

        /* ---- Button overrides ---- */
        .stButton > button {{
            background: {COLORS['surface']};
            color: {COLORS['text_primary']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
            font-weight: 500;
            font-size: 0.82rem;
            transition: all 0.2s ease;
        }}
        .stButton > button:hover {{
            border-color: {COLORS['accent_cyan']};
            color: {COLORS['accent_cyan']};
            box-shadow: 0 0 12px rgba(34, 211, 238, 0.15);
        }}

        /* ---- Download button ---- */
        .stDownloadButton > button {{
            background: linear-gradient(135deg, {COLORS['accent_blue']}, {COLORS['accent_indigo']});
            color: white;
            border: none;
            border-radius: 8px;
        }}

        /* ---- Alerts ---- */
        .stAlert {{
            border-radius: 8px;
            border: 1px solid {COLORS['border']};
        }}

        /* ---- Toggle ---- */
        [data-testid="stToggle"] label span {{
            color: {COLORS['text_secondary']} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
