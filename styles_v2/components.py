"""
styles_v2/components.py
=======================
Reusable CSS component class generators for ParkSight AI V2.
Each function returns an HTML string or CSS block that can be injected
via st.markdown(unsafe_allow_html=True).
"""

from styles_v2.theme import COLORS, FONT_FAMILY, FONT_MONO, BAND_COLORS, BAND_BG_COLORS


def inject_component_css():
    """Return a <style> block with all shared component CSS classes."""
    return f"""
    <style>
    /* ============ V2 COMPONENT CLASSES ============ */

    /* ---- Section Header ---- */
    .v2-section-header {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.82rem;
        font-weight: 700;
        color: {COLORS['text_secondary']};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding-bottom: 10px;
        margin-bottom: 14px;
        border-bottom: 1px solid {COLORS['border']};
    }}
    .v2-section-header .icon {{
        font-size: 1rem;
    }}

    /* ---- Panel / Card Container ---- */
    .v2-panel {{
        background: {COLORS['surface_glass']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 12px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }}
    .v2-panel:hover {{
        border-color: {COLORS['border_hover']};
    }}
    .v2-panel-header {{
        font-size: 0.78rem;
        font-weight: 600;
        color: {COLORS['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }}

    /* ---- Vital Sign Card ---- */
    .v2-vital {{
        background: {COLORS['surface_glass']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        padding: 14px 16px;
        margin-bottom: 10px;
        transition: border-color 0.2s ease;
    }}
    .v2-vital:hover {{
        border-color: {COLORS['accent_cyan']};
    }}
    .v2-vital-label {{
        font-size: 0.7rem;
        font-weight: 600;
        color: {COLORS['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 4px;
    }}
    .v2-vital-value {{
        font-size: 1.5rem;
        font-weight: 800;
        color: {COLORS['text_bright']};
        line-height: 1.2;
        font-family: {FONT_FAMILY};
    }}
    .v2-vital-sub {{
        font-size: 0.72rem;
        color: {COLORS['text_secondary']};
        margin-top: 4px;
    }}
    .v2-vital-trend {{
        font-size: 0.72rem;
        font-weight: 600;
        margin-top: 3px;
    }}
    .v2-trend-up {{ color: {COLORS['critical']}; }}
    .v2-trend-down {{ color: {COLORS['low']}; }}
    .v2-trend-neutral {{ color: {COLORS['text_muted']}; }}

    /* ---- Progress Bar ---- */
    .v2-progress {{
        width: 100%;
        height: 4px;
        background: {COLORS['border']};
        border-radius: 2px;
        margin-top: 6px;
        overflow: hidden;
    }}
    .v2-progress-fill {{
        height: 100%;
        border-radius: 2px;
        transition: width 0.6s ease;
    }}

    /* ---- Data Table ---- */
    .v2-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.8rem;
        font-family: {FONT_FAMILY};
    }}
    .v2-table thead th {{
        color: {COLORS['text_muted']};
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 8px 10px;
        text-align: left;
        border-bottom: 1px solid {COLORS['border']};
        white-space: nowrap;
    }}
    .v2-table tbody tr {{
        border-bottom: 1px solid {COLORS['border_subtle']};
        transition: background 0.15s ease;
    }}
    .v2-table tbody tr:hover {{
        background: rgba(34, 211, 238, 0.04);
    }}
    .v2-table tbody td {{
        padding: 8px 10px;
        color: {COLORS['text_primary']};
        white-space: nowrap;
    }}
    .v2-table .col-num {{
        font-family: {FONT_MONO};
        font-weight: 500;
        text-align: right;
    }}

    /* ---- Priority Badge / Pill ---- */
    .v2-badge {{
        display: inline-block;
        padding: 2px 10px;
        border-radius: 10px;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .v2-badge-critical {{
        background: {COLORS['critical_bg']};
        color: {COLORS['critical']};
        border: 1px solid rgba(239, 68, 68, 0.3);
    }}
    .v2-badge-high {{
        background: {COLORS['high_bg']};
        color: {COLORS['high']};
        border: 1px solid rgba(249, 115, 22, 0.3);
    }}
    .v2-badge-medium {{
        background: {COLORS['medium_bg']};
        color: {COLORS['medium']};
        border: 1px solid rgba(234, 179, 8, 0.3);
    }}
    .v2-badge-low {{
        background: {COLORS['low_bg']};
        color: {COLORS['low']};
        border: 1px solid rgba(34, 197, 94, 0.3);
    }}
    .v2-badge-elevated {{
        background: {COLORS['elevated_bg']};
        color: {COLORS['elevated']};
        border: 1px solid rgba(245, 158, 11, 0.3);
    }}
    .v2-badge-normal {{
        background: rgba(34, 211, 238, 0.1);
        color: {COLORS['accent_cyan']};
        border: 1px solid rgba(34, 211, 238, 0.25);
    }}
    .v2-count-badge {{
        display: inline-block;
        padding: 1px 8px;
        border-radius: 8px;
        font-size: 0.64rem;
        font-weight: 700;
        background: {COLORS['critical']};
        color: white;
        margin-left: 6px;
    }}

    /* ---- Status Dot ---- */
    .v2-status-dot {{
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 4px;
    }}
    .v2-dot-critical {{ background: {COLORS['critical']}; box-shadow: 0 0 6px {COLORS['critical']}; }}
    .v2-dot-high {{ background: {COLORS['high']}; }}
    .v2-dot-elevated {{ background: {COLORS['elevated']}; }}
    .v2-dot-medium {{ background: {COLORS['medium']}; }}
    .v2-dot-low {{ background: {COLORS['low']}; }}
    .v2-dot-live {{ background: {COLORS['low']}; box-shadow: 0 0 8px {COLORS['low']}; animation: v2-pulse 2s infinite; }}

    @keyframes v2-pulse {{
        0%, 100% {{ opacity: 1; }}
        50% {{ opacity: 0.4; }}
    }}

    /* ---- Alert / Feed Card ---- */
    .v2-alert-card {{
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-left: 3px solid {COLORS['text_muted']};
        border-radius: 6px;
        padding: 12px 14px;
        margin-bottom: 10px;
        font-size: 0.8rem;
    }}
    .v2-alert-card.critical {{ border-left-color: {COLORS['critical']}; }}
    .v2-alert-card.high {{ border-left-color: {COLORS['high']}; }}
    .v2-alert-card.elevated {{ border-left-color: {COLORS['elevated']}; }}
    .v2-alert-card.info {{ border-left-color: {COLORS['accent_blue']}; }}
    .v2-alert-title {{
        font-weight: 700;
        color: {COLORS['text_primary']};
        margin-bottom: 4px;
        font-size: 0.82rem;
    }}
    .v2-alert-text {{
        color: {COLORS['text_secondary']};
        font-size: 0.76rem;
        line-height: 1.4;
    }}
    .v2-alert-time {{
        font-size: 0.66rem;
        color: {COLORS['text_muted']};
        float: right;
    }}

    /* ---- Action Buttons ---- */
    .v2-btn {{
        display: inline-block;
        padding: 6px 16px;
        border-radius: 6px;
        font-size: 0.74rem;
        font-weight: 600;
        cursor: pointer;
        border: none;
        text-decoration: none;
        transition: all 0.2s ease;
        margin-right: 8px;
        margin-top: 8px;
    }}
    .v2-btn-primary {{
        background: {COLORS['accent_cyan']};
        color: {COLORS['bg_primary']};
    }}
    .v2-btn-primary:hover {{ opacity: 0.85; }}
    .v2-btn-danger {{
        background: {COLORS['critical']};
        color: white;
    }}
    .v2-btn-danger:hover {{ opacity: 0.85; }}
    .v2-btn-ghost {{
        background: {COLORS['surface']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
    }}
    .v2-btn-ghost:hover {{
        border-color: {COLORS['accent_cyan']};
        color: {COLORS['accent_cyan']};
    }}

    /* ---- Confidence Bar ---- */
    .v2-confidence-bar {{
        width: 100%;
        height: 6px;
        background: {COLORS['border']};
        border-radius: 3px;
        overflow: hidden;
        margin-top: 6px;
    }}
    .v2-confidence-fill {{
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, {COLORS['accent_cyan']}, {COLORS['accent_blue']});
    }}

    /* ---- Topbar ---- */
    .v2-topbar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 0 14px 0;
        border-bottom: 1px solid {COLORS['border']};
        margin-bottom: 18px;
    }}
    .v2-topbar-brand {{
        display: flex;
        align-items: center;
        gap: 16px;
    }}
    .v2-topbar-logo {{
        font-size: 1.15rem;
        font-weight: 800;
        color: {COLORS['text_bright']};
        letter-spacing: -0.02em;
    }}
    .v2-topbar-module {{
        font-size: 0.7rem;
        font-weight: 600;
        color: {COLORS['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 3px 10px;
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
    }}
    .v2-topbar-right {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .v2-system-live {{
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.72rem;
        font-weight: 600;
        color: {COLORS['low']};
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    .v2-emergency-btn {{
        padding: 4px 14px;
        background: rgba(239, 68, 68, 0.15);
        color: {COLORS['critical']};
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    .v2-topbar-icon {{
        color: {COLORS['text_muted']};
        font-size: 1rem;
        cursor: pointer;
        transition: color 0.2s;
    }}
    .v2-topbar-icon:hover {{
        color: {COLORS['accent_cyan']};
    }}

    /* ---- Enforcement Recommendation Card ---- */
    .v2-enforce-card {{
        background: {COLORS['surface']};
        border: 1px solid {COLORS['accent_cyan']};
        border-radius: 10px;
        padding: 18px;
        margin-top: 12px;
    }}
    .v2-enforce-label {{
        font-size: 0.68rem;
        font-weight: 700;
        color: {COLORS['accent_cyan']};
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 6px;
    }}

    /* ---- Station Card ---- */
    .v2-station-card {{
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-left: 3px solid {COLORS['accent_blue']};
        border-radius: 8px;
        padding: 14px 16px;
    }}
    .v2-station-name {{
        font-size: 0.92rem;
        font-weight: 700;
        color: {COLORS['text_primary']};
        margin-bottom: 8px;
    }}

    /* ---- Allocation Matrix ---- */
    .v2-matrix {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.74rem;
    }}
    .v2-matrix th {{
        color: {COLORS['text_muted']};
        font-size: 0.66rem;
        font-weight: 600;
        text-transform: uppercase;
        padding: 6px 10px;
        text-align: center;
        border-bottom: 1px solid {COLORS['border']};
    }}
    .v2-matrix td {{
        padding: 4px 6px;
        text-align: center;
        border-bottom: 1px solid {COLORS['border_subtle']};
    }}
    .v2-matrix-cell {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.68rem;
        font-weight: 600;
        color: white;
        white-space: nowrap;
    }}
    .v2-matrix-patrol {{ background: {COLORS['accent_blue']}; }}
    .v2-matrix-priority {{ background: {COLORS['critical']}; }}
    .v2-matrix-static {{ background: {COLORS['accent_indigo']}; }}
    .v2-matrix-relief {{ background: {COLORS['accent_cyan']}; color: {COLORS['bg_primary']}; }}
    .v2-matrix-break {{ background: {COLORS['surface_hover']}; color: {COLORS['text_muted']}; }}

    /* ---- Map Legend ---- */
    .v2-map-legend {{
        display: flex;
        align-items: center;
        gap: 16px;
        font-size: 0.72rem;
        color: {COLORS['text_secondary']};
        padding: 6px 0;
    }}
    .v2-legend-item {{
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    .v2-legend-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
    }}

    /* ---- Countdown Timer ---- */
    .v2-countdown {{
        text-align: right;
    }}
    .v2-countdown-label {{
        font-size: 0.68rem;
        color: {COLORS['text_muted']};
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    .v2-countdown-value {{
        font-size: 1.6rem;
        font-weight: 700;
        color: {COLORS['text_bright']};
        font-family: {FONT_MONO};
    }}
    .v2-countdown-sub {{
        font-size: 0.72rem;
        color: {COLORS['text_secondary']};
    }}
    </style>
    """
