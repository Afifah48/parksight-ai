"""
app_v2.py
=========
ParkSight AI V2 — Streamlit entry point.

Run with:
    streamlit run app_v2.py

This is a completely separate frontend from the original app.py.
It reuses all existing backend logic from src/ but presents
a redesigned ops-grade command-center UI.

The original app.py and pages/ directory remain fully functional.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Page config — must be the first Streamlit call.
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ParkSight AI — Command Center V2",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "ParkSight AI — Operational Intelligence V2\n\n"
            "Bengaluru Traffic Police Command Center\n\n"
            "Powered by 298,450 violation records."
        )
    },
)

# ---------------------------------------------------------------------------
# Imports — V2 design system
# ---------------------------------------------------------------------------
from styles_v2.theme import inject_v2_theme, COLORS
from styles_v2.components import inject_component_css
from components_v2.sidebar import render_sidebar

# ---------------------------------------------------------------------------
# Inject global styles
# ---------------------------------------------------------------------------
inject_v2_theme()
st.markdown(inject_component_css(), unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Navigation — use st.navigation to explicitly define pages
# (this disables automatic pages/ directory discovery)
# ---------------------------------------------------------------------------
pages = [
    st.Page("pages_v2/executive.py", title="Executive", icon="📊", default=True),
    st.Page("pages_v2/intelligence.py", title="Intelligence", icon="🔍"),
    st.Page("pages_v2/emerging_threats.py", title="Emerging Threats", icon="⚠️"),
    st.Page("pages_v2/repeat_offenders.py", title="Repeat Offenders", icon="🎯"),
    st.Page("pages_v2/operations.py", title="Operations", icon="⚙️"),
    st.Page("pages_v2/analytics.py", title="Analytics", icon="📈"),
    st.Page("pages_v2/planning.py", title="Planning", icon="📋"),
    st.Page("pages_v2/simulator.py", title="Simulator", icon="🧮"),
]

pg = st.navigation(pages, position="hidden")  # hidden = we render our own sidebar

# ---------------------------------------------------------------------------
# Render the selected page
# ---------------------------------------------------------------------------
pg.run()
