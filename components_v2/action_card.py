"""
components_v2/action_card.py
============================
Action and recommendation card renderers for ParkSight AI V2.
Used across Operations, Emerging Threats, and Repeat Offender pages.
"""

import streamlit as st
from styles_v2.theme import COLORS
from components_v2.alert_badge import priority_badge


def render_action_card(title, description, priority_band="High", action_type="",
                       metrics=None, show_buttons=True):
    """Render a styled action/recommendation card.

    Parameters
    ----------
    title : str
        Card title (e.g., hotspot name or action title).
    description : str
        Action description / reason.
    priority_band : str
        Priority band for border color.
    action_type : str
        Action type label (e.g., "🚨 URGENT DEPLOY").
    metrics : dict, optional
        Key-value pairs to display as mini metrics.
    show_buttons : bool
        Whether to show Execute/Dismiss buttons.
    """
    band_colors = {
        "Critical": COLORS["critical"],
        "High": COLORS["high"],
        "Medium": COLORS["medium"],
        "Low": COLORS["low"],
    }
    border_color = band_colors.get(priority_band, COLORS["border"])

    metrics_html = ""
    if metrics:
        metrics_html = '<div style="display:flex; gap:16px; margin:8px 0;">'
        for key, val in metrics.items():
            metrics_html += f"""
                <div>
                    <div style="font-size:0.64rem; color:{COLORS['text_muted']};
                                text-transform:uppercase;">{key}</div>
                    <div style="font-size:0.88rem; font-weight:600;
                                color:{COLORS['accent_cyan']};">{val}</div>
                </div>
            """
        metrics_html += "</div>"

    buttons_html = ""
    if show_buttons:
        buttons_html = f"""
            <div style="margin-top:8px;">
                <span class="v2-btn v2-btn-primary">Execute</span>
                <span class="v2-btn v2-btn-ghost">Dismiss</span>
            </div>
        """

    type_html = ""
    if action_type:
        type_html = f"""
            <div style="font-size:0.66rem; font-weight:700; color:{COLORS['text_muted']};
                        text-transform:uppercase; letter-spacing:0.08em; margin-bottom:4px;">
                {action_type}
            </div>
        """

    st.markdown(
        f"""
        <div style="background:{COLORS['surface']}; border:1px solid {COLORS['border']};
                    border-left:3px solid {border_color}; border-radius:8px;
                    padding:14px 16px; margin-bottom:10px;">
            {type_html}
            <div style="font-size:0.88rem; font-weight:700; color:{COLORS['text_primary']};
                        margin-bottom:4px;">{title}</div>
            <div style="font-size:0.76rem; color:{COLORS['text_secondary']};
                        line-height:1.45;">{description}</div>
            {metrics_html}
            {buttons_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_enforcement_card(vehicle_number, violation_count, confidence,
                            description="", primary_offense=""):
    """Render an enforcement recommendation card (Screenshot 4 style).

    Parameters
    ----------
    vehicle_number : str
        Target vehicle plate number.
    violation_count : int
        Number of violations.
    confidence : float
        Confidence score (0-100).
    description : str
        Enforcement reason text.
    primary_offense : str
        Primary offense type and location.
    """
    conf_pct = min(max(confidence, 0), 100)

    st.markdown(
        f"""
        <div class="v2-enforce-card">
            <div class="v2-enforce-label">Enforcement Recommendation</div>
            <div style="font-size:1.1rem; font-weight:700; color:{COLORS['text_bright']};
                        margin-bottom:8px;">
                Target: {vehicle_number}
            </div>
            <div style="font-size:0.78rem; color:{COLORS['text_secondary']};
                        line-height:1.5; margin-bottom:10px;">
                Vehicle has exceeded critical threshold ({violation_count} violations in 72h).
                {f"Primary offense: {primary_offense}." if primary_offense else ""}
                {description}
            </div>
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;">
                        <span style="font-size:0.7rem; color:{COLORS['text_muted']};">Confidence Score</span>
                        <span style="font-size:0.7rem; font-weight:600;
                                    color:{COLORS['accent_cyan']}; font-family:{COLORS['text_bright']};">
                            {conf_pct:.1f}%
                        </span>
                    </div>
                    <div class="v2-confidence-bar">
                        <div class="v2-confidence-fill" style="width:{conf_pct}%;"></div>
                    </div>
                </div>
            </div>
            <div>
                <span class="v2-btn v2-btn-danger">🚩 Flag for Towing</span>
                <span class="v2-btn v2-btn-ghost">📋 Issue Citation</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_station_status_card(station_name, status="Elevated", active_units=8,
                               total_units=10):
    """Render a station status card (Screenshot 3 style).

    Parameters
    ----------
    station_name : str
        Station display name.
    status : str
        Status label (Critical Load, Elevated, Normal).
    active_units : int
        Active patrol units.
    total_units : int
        Total available units.
    """
    status_colors = {
        "Critical Load": COLORS["critical"],
        "Elevated": COLORS["elevated"],
        "Normal": COLORS["low"],
    }
    dot_color = status_colors.get(status, COLORS["accent_blue"])

    st.markdown(
        f"""
        <div class="v2-station-card">
            <div class="v2-station-name">{station_name}</div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:0.66rem; color:{COLORS['text_muted']};
                                text-transform:uppercase;">Status</div>
                    <div style="display:flex; align-items:center; gap:6px; margin-top:3px;">
                        <span style="display:inline-block; width:8px; height:8px;
                                    border-radius:50%; background:{dot_color};"></span>
                        <span style="font-size:0.78rem; font-weight:500;
                                    color:{dot_color};">{status}</span>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:0.66rem; color:{COLORS['text_muted']};
                                text-transform:uppercase;">Active Units</div>
                    <div style="font-size:1.3rem; font-weight:700;
                                color:{COLORS['text_bright']}; margin-top:2px;">
                        {active_units:02d}/{total_units:02d}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hotspot_detail_card(name, hotspot_id="", impact_score=0, trend_24h="",
                               description="", show_buttons=True):
    """Render a junction detail card (Screenshot 2 right panel style).

    Parameters
    ----------
    name : str
        Junction/hotspot name.
    hotspot_id : str
        Hotspot identifier.
    impact_score : float
        PCIS or impact score.
    trend_24h : str
        24h trend text (e.g., "+12%").
    description : str
        Description text.
    show_buttons : bool
        Show action buttons.
    """
    # Score color
    if impact_score >= 8:
        score_color = COLORS["critical"]
    elif impact_score >= 6:
        score_color = COLORS["high"]
    elif impact_score >= 4:
        score_color = COLORS["elevated"]
    else:
        score_color = COLORS["low"]

    buttons_html = ""
    if show_buttons:
        buttons_html = f"""
            <div style="display:flex; gap:8px; margin-top:12px;">
                <span class="v2-btn v2-btn-primary" style="flex:1; text-align:center;">View Cameras</span>
                <span class="v2-btn v2-btn-ghost" style="flex:1; text-align:center;">Issue Alert</span>
            </div>
        """

    st.markdown(
        f"""
        <div style="background:{COLORS['surface']}; border:1px solid {COLORS['accent_cyan']};
                    border-radius:10px; padding:16px; margin-top:12px;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <div style="font-size:1rem; font-weight:700;
                                color:{COLORS['text_bright']};">{name}</div>
                    <div style="font-size:0.7rem; color:{COLORS['text_muted']};
                                margin-top:2px;">ID: {hotspot_id}</div>
                </div>
                <span class="v2-btn v2-btn-ghost" style="font-size:0.7rem; margin:0;">Dispatch Unit</span>
            </div>
            <div style="display:flex; gap:16px; margin:12px 0;">
                <div style="flex:1; background:{COLORS['bg_secondary']}; border-radius:6px; padding:8px 12px;">
                    <div style="font-size:0.64rem; color:{COLORS['text_muted']};
                                text-transform:uppercase;">Impact Score</div>
                    <div style="font-size:1.3rem; font-weight:700;
                                color:{score_color};">{impact_score:.1f}</div>
                </div>
                <div style="flex:1; background:{COLORS['bg_secondary']}; border-radius:6px; padding:8px 12px;">
                    <div style="font-size:0.64rem; color:{COLORS['text_muted']};
                                text-transform:uppercase;">Trend (24h)</div>
                    <div style="font-size:1.3rem; font-weight:700;
                                color:{COLORS['text_bright']};">{trend_24h} 📈</div>
                </div>
            </div>
            <div style="font-size:0.76rem; color:{COLORS['text_secondary']};
                        line-height:1.45;">{description}</div>
            {buttons_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
