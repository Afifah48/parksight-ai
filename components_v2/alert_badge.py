"""
components_v2/alert_badge.py
============================
Status badges, priority pills, trend arrows, and count badges for V2.
"""

from styles_v2.theme import COLORS, BAND_COLORS


def priority_badge(band):
    """Return HTML for a colored priority-band pill.

    Parameters
    ----------
    band : str
        One of "Critical", "High", "Medium", "Low", "Elevated", "Normal".
    """
    css_class = f"v2-badge-{band.lower()}"
    return f'<span class="v2-badge {css_class}">{band}</span>'


def status_dot(status):
    """Return HTML for a colored status dot.

    Parameters
    ----------
    status : str
        One of "critical", "high", "elevated", "medium", "low", "live".
    """
    css_class = f"v2-dot-{status.lower()}"
    return f'<span class="v2-status-dot {css_class}"></span>'


def trend_arrow(direction, value=""):
    """Return HTML for a trend indicator arrow with optional value.

    Parameters
    ----------
    direction : str
        One of "up", "down", "flat", "accelerating", "decelerating".
    value : str
        Optional value to display (e.g., "+12%").
    """
    arrows = {
        "up": "↗",
        "down": "↘",
        "flat": "→",
        "accelerating": "↗↗",
        "decelerating": "↘",
        "stable": "→",
    }
    colors = {
        "up": COLORS["critical"],
        "down": COLORS["low"],
        "flat": COLORS["text_muted"],
        "accelerating": COLORS["critical"],
        "decelerating": COLORS["low"],
        "stable": COLORS["text_muted"],
    }
    arrow = arrows.get(direction, "→")
    color = colors.get(direction, COLORS["text_muted"])
    val_html = f" {value}" if value else ""
    return f'<span style="color:{color}; font-weight:600; font-size:0.78rem;">{arrow}{val_html}</span>'


def count_badge(count, label=""):
    """Return HTML for a count badge (e.g., '4 NEW').

    Parameters
    ----------
    count : int
        Number to display.
    label : str
        Optional label text (e.g., "NEW", "ACTIVE").
    """
    text = f"{count} {label}".strip()
    return f'<span class="v2-count-badge">{text}</span>'


def band_color(band):
    """Return the hex color for a given priority band."""
    return BAND_COLORS.get(band, COLORS["text_muted"])
