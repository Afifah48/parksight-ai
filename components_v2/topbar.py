"""
components_v2/topbar.py
=======================
Top navigation bar for ParkSight AI V2.
Renders logo, module context, search bar, system status, and action icons.
"""

import streamlit as st
from styles_v2.theme import COLORS


def render_topbar(module_name="", search_placeholder="Search operational data..."):
    """Render the V2 top bar.

    Parameters
    ----------
    module_name : str
        Context label shown next to the logo (e.g., "PATROL PLANNER").
    search_placeholder : str
        Placeholder text for the search input.
    """
    module_html = ""
    if module_name:
        module_html = f"""
            <span class="v2-topbar-module">{module_name}</span>
        """

    st.markdown(
        f"""
        <div class="v2-topbar">
            <div class="v2-topbar-brand">
                <span class="v2-topbar-logo">ParkSight AI</span>
                {module_html}
                <div style="display:flex; align-items:center; background:{COLORS['surface']};
                            border:1px solid {COLORS['border']}; border-radius:8px;
                            padding:5px 14px; min-width:220px; gap:8px;">
                    <span style="color:{COLORS['text_muted']}; font-size:0.82rem;">🔍</span>
                    <span style="color:{COLORS['text_muted']}; font-size:0.78rem;">{search_placeholder}</span>
                </div>
            </div>
            <div class="v2-topbar-right">
                <div class="v2-system-live">
                    <span class="v2-status-dot v2-dot-live"></span>
                    System Live
                </div>
                <span class="v2-emergency-btn">⚠ Emergency</span>
                <span class="v2-topbar-icon">🔔</span>
                <span class="v2-topbar-icon">⚙️</span>
                <span class="v2-topbar-icon">❓</span>
                <div style="width:30px; height:30px; border-radius:50%;
                            background: linear-gradient(135deg, {COLORS['accent_blue']}, {COLORS['accent_indigo']});
                            display:flex; align-items:center; justify-content:center;
                            font-size:0.72rem; color:white; font-weight:600;">U</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
