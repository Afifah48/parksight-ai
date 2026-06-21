"""
components_v2/sidebar.py
========================
Left navigation sidebar for ParkSight AI V2.
Renders BTP Command branding, navigation items, and footer links.
"""

import streamlit as st
from styles_v2.theme import COLORS


def render_sidebar(active_page="Executive"):
    """Render the V2 sidebar navigation.

    Parameters
    ----------
    active_page : str
        Name of the currently active page to highlight.
    """
    with st.sidebar:
        # ---- BTP Command Branding ----
        st.markdown(
            f"""
            <div style="text-align:center; padding: 10px 0 18px;">
                <div style="display:inline-flex; align-items:center; justify-content:center;
                            width:40px; height:40px; border-radius:50%;
                            background: linear-gradient(135deg, {COLORS['accent_blue']}, {COLORS['accent_indigo']});
                            margin-bottom:8px;">
                    <span style="font-size:1.2rem; color:white;">🛡️</span>
                </div>
                <div style="font-size:0.92rem; font-weight:700; color:{COLORS['text_bright']};
                            line-height:1.3;">BTP Command</div>
                <div style="font-size:0.66rem; color:{COLORS['text_muted']};
                            text-transform:uppercase; letter-spacing:0.1em; margin-top:2px;">
                    Operational Intelligence
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- New Patrol Plan CTA ----
        st.markdown(
            f"""
            <div style="padding: 0 8px 16px;">
                <div style="background: linear-gradient(135deg, {COLORS['accent_blue']}, {COLORS['accent_cyan']});
                            color: white; text-align:center; padding: 9px 0; border-radius: 8px;
                            font-size: 0.8rem; font-weight: 600; cursor: pointer;
                            transition: opacity 0.2s;">
                    + New Patrol Plan
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Navigation Links ----
        nav_items = [
            ("📊", "Executive", "executive"),
            ("🔍", "Intelligence", "intelligence"),
            ("⚙️", "Operations", "operations"),
            ("📈", "Analytics", "analytics"),
            ("📋", "Planning", "planning"),
            ("🧮", "Simulator", "simulator"),
        ]

        for icon, label, key in nav_items:
            is_active = label == active_page
            if is_active:
                bg = f"linear-gradient(90deg, rgba(34,211,238,0.12), transparent)"
                border = f"3px solid {COLORS['accent_cyan']}"
                text_color = COLORS["accent_cyan"]
                weight = "600"
            else:
                bg = "transparent"
                border = "3px solid transparent"
                text_color = COLORS["text_secondary"]
                weight = "400"

            st.markdown(
                f"""
                <div style="display:flex; align-items:center; gap:10px;
                            padding: 8px 14px; margin: 2px 0;
                            background: {bg}; border-left: {border};
                            border-radius: 0 6px 6px 0; cursor: pointer;
                            transition: all 0.2s;">
                    <span style="font-size:0.9rem;">{icon}</span>
                    <span style="font-size:0.82rem; font-weight:{weight};
                                color:{text_color};">{label}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Actual Streamlit page links (hidden visually, used for navigation)
        border_color = COLORS["border"]
        st.markdown(
            f"<div style='height:1px; margin:6px 0; background:{border_color};'></div>",
            unsafe_allow_html=True,
        )

        # ---- Spacer ----
        st.markdown("<div style='flex:1; min-height:100px;'></div>", unsafe_allow_html=True)

        # ---- Footer Links ----
        st.markdown(
            f"""
            <div style="padding: 0 8px;">
                <div style="display:flex; align-items:center; gap:10px;
                            padding: 8px 14px; cursor:pointer;">
                    <span style="font-size:0.85rem;">⚙️</span>
                    <span style="font-size:0.82rem; color:{COLORS['text_secondary']};">Settings</span>
                </div>
                <div style="display:flex; align-items:center; gap:10px;
                            padding: 8px 14px; cursor:pointer;">
                    <span style="font-size:0.85rem;">❓</span>
                    <span style="font-size:0.82rem; color:{COLORS['text_secondary']};">Support</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
