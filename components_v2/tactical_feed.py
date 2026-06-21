"""
components_v2/tactical_feed.py
==============================
Tactical feed / right-side panel for the Executive Dashboard.
Renders active alerts, AI recommendations, and threat summary.
"""

import streamlit as st
from styles_v2.theme import COLORS
from components_v2.alert_badge import count_badge


def render_tactical_feed(recommendations):
    """Render the tactical feed panel (right column of Executive Dashboard).

    Parameters
    ----------
    recommendations : dict
        Output from generate_recommendations(). Expected keys:
        top_actions, emerging_alerts, offender_targets, stations_at_risk.
    """
    # ---- Active Alerts Section ----
    alerts = recommendations.get("emerging_alerts", [])
    alert_count = len(alerts)

    st.markdown(
        f"""
        <div style="font-size:0.92rem; font-weight:700; color:{COLORS['text_bright']};
                    margin-bottom:12px;">
            Tactical Feed
        </div>
        <div style="margin-bottom:14px;">
            <span style="display:inline-block; padding:3px 12px; border-radius:12px;
                        background:{COLORS['critical_bg']}; color:{COLORS['critical']};
                        font-size:0.72rem; font-weight:700;">
                Active Alerts ({alert_count})
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Render alert cards (top 3)
    for alert in alerts[:3]:
        urgency = alert.get("urgency", "ELEVATED")
        urgency_lower = urgency.lower()
        if urgency_lower == "critical":
            border_color = COLORS["critical"]
        elif urgency_lower == "high":
            border_color = COLORS["high"]
        else:
            border_color = COLORS["elevated"]

        name = alert.get("hotspot_name", "Unknown")
        desc = alert.get("recommended_action", "Monitor situation.")
        pct = alert.get("pct_increase", 0)
        pct_text = f"+{pct:.0f}% increase" if pct else ""

        st.markdown(
            f"""
            <div class="v2-alert-card {urgency_lower}">
                <div class="v2-alert-title">{name}</div>
                <div class="v2-alert-text">{desc}</div>
                {f'<div style="color:{COLORS["critical"]}; font-size:0.7rem; font-weight:600; margin-top:4px;">{pct_text}</div>' if pct_text else ''}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---- AI Recommendations Section ----
    top_actions = recommendations.get("top_actions", [])
    if top_actions:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:6px; margin:18px 0 10px;
                        font-size:0.82rem; font-weight:700; color:{COLORS['accent_cyan']};">
                <span>⚡</span> AI Recommendations
            </div>
            """,
            unsafe_allow_html=True,
        )

        for action in top_actions[:3]:
            action_type = action.get("action_type", "")
            name = action.get("hotspot_name", "")
            reason = action.get("reason", "")
            band = action.get("priority_band", "High")

            if "URGENT" in action_type:
                btn_text = "Execute"
                btn_class = "v2-btn-primary"
            elif "OFFENDER" in action_type:
                btn_text = "Dispatch"
                btn_class = "v2-btn-danger"
            else:
                btn_text = "Review"
                btn_class = "v2-btn-ghost"

            st.markdown(
                f"""
                <div style="background:{COLORS['surface']}; border:1px solid {COLORS['border']};
                            border-radius:8px; padding:12px; margin-bottom:8px;">
                    <div style="font-size:0.82rem; font-weight:700; color:{COLORS['text_primary']};
                                margin-bottom:4px;">{name}</div>
                    <div style="font-size:0.72rem; color:{COLORS['text_secondary']};
                                line-height:1.4; margin-bottom:8px;">{reason}</div>
                    <span class="v2-btn {btn_class}">{btn_text}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ---- Threat Summary ----
    stations_risk = recommendations.get("stations_at_risk", [])
    if stations_risk:
        top_station = stations_risk[0] if stations_risk else {}
        critical_count = top_station.get("critical_count", 0)

        st.markdown(
            f"""
            <div style="margin-top:18px; background:{COLORS['surface']};
                        border:1px solid {COLORS['border']}; border-radius:8px; padding:12px;">
                <div style="font-size:0.76rem; font-weight:700; color:{COLORS['text_secondary']};
                            text-transform:uppercase; letter-spacing:0.06em; margin-bottom:6px;">
                    Threat Summary (Next 2 hrs)
                </div>
                <div style="display:flex; align-items:flex-start; gap:8px;">
                    <span style="font-size:1.2rem;">⚠️</span>
                    <div style="font-size:0.74rem; color:{COLORS['text_secondary']}; line-height:1.4;">
                        <strong style="color:{COLORS['critical']};">{critical_count} critical</strong>
                        hotspots require immediate attention.
                        Highest risk zone: <strong>{top_station.get('police_station', 'N/A')}</strong>.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
