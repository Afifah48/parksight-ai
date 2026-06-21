"""
components_v2/chart_factory.py
==============================
Plotly chart builders with the V2 dark theme applied.
All charts return plotly Figure objects styled consistently.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from styles_v2.theme import COLORS, BAND_COLORS, get_plotly_layout, FONT_MONO


def bar_chart(df, x, y, title="", color=None, color_map=None, orientation="v",
              height=350, show_legend=False):
    """Create a styled bar chart.

    Parameters
    ----------
    df : pd.DataFrame
    x, y : str
        Column names for x and y axes.
    title : str
    color : str, optional
        Column for color coding.
    color_map : dict, optional
        Explicit color mapping.
    orientation : str
        'v' for vertical, 'h' for horizontal.
    height : int
    show_legend : bool
    """
    if color and color_map:
        fig = px.bar(
            df, x=x, y=y, color=color,
            color_discrete_map=color_map,
            orientation=orientation,
        )
    elif color:
        fig = px.bar(df, x=x, y=y, color=color, orientation=orientation)
    else:
        fig = go.Figure(
            go.Bar(
                x=df[x] if orientation == "v" else df[y],
                y=df[y] if orientation == "v" else df[x],
                orientation=orientation,
                marker=dict(
                    color=COLORS["accent_cyan"],
                    line=dict(width=0),
                    cornerradius=4,
                ),
            )
        )

    fig.update_layout(
        **get_plotly_layout(
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"])),
            height=height,
            showlegend=show_legend,
            bargap=0.25,
        )
    )
    return fig


def grouped_bar_chart(df, x, y_cols, names=None, colors=None, title="", height=350):
    """Create a grouped bar chart with multiple series."""
    fig = go.Figure()
    names = names or y_cols
    default_colors = [COLORS["accent_cyan"], COLORS["accent_blue"],
                      COLORS["accent_indigo"], COLORS["high"]]
    colors = colors or default_colors

    for i, (col, name) in enumerate(zip(y_cols, names)):
        fig.add_trace(go.Bar(
            x=df[x],
            y=df[col],
            name=name,
            marker=dict(color=colors[i % len(colors)], cornerradius=3),
        ))

    fig.update_layout(
        **get_plotly_layout(
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"])),
            height=height,
            barmode="group",
            bargap=0.3,
            showlegend=True,
        )
    )
    return fig


def donut_chart(labels, values, title="", colors=None, height=300, hole=0.55):
    """Create a donut chart."""
    colors = colors or [BAND_COLORS.get(l, COLORS["accent_blue"]) for l in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=hole,
        marker=dict(colors=colors, line=dict(color=COLORS["bg_primary"], width=2)),
        textfont=dict(size=11, color=COLORS["text_primary"]),
        textinfo="label+percent",
        hoverinfo="label+value+percent",
    ))

    fig.update_layout(
        **get_plotly_layout(
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"])),
            height=height,
            showlegend=False,
        )
    )
    return fig


def line_chart(df, x, y, title="", color=None, height=300):
    """Create a styled line chart."""
    line_color = color or COLORS["accent_cyan"]

    fig = go.Figure(go.Scatter(
        x=df[x],
        y=df[y],
        mode="lines+markers",
        line=dict(color=line_color, width=2),
        marker=dict(size=5, color=line_color),
        fill="tozeroy",
        fillcolor=f"rgba(34, 211, 238, 0.08)",
    ))

    fig.update_layout(
        **get_plotly_layout(
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"])),
            height=height,
        )
    )
    return fig


def risk_acceleration_chart(df, x="hotspot_name", y="drift_score", title="Risk Acceleration (24h)",
                            height=350):
    """Create the risk acceleration bar chart from Screenshot 3."""
    df_sorted = df.sort_values(y, ascending=True).tail(15)

    colors = []
    for val in df_sorted[y]:
        if val >= 90:
            colors.append(COLORS["critical"])
        elif val >= 70:
            colors.append(COLORS["high"])
        elif val >= 50:
            colors.append(COLORS["elevated"])
        else:
            colors.append(COLORS["accent_blue"])

    fig = go.Figure(go.Bar(
        x=df_sorted[y],
        y=df_sorted[x],
        orientation="h",
        marker=dict(color=colors, cornerradius=3),
    ))

    fig.update_layout(
        **get_plotly_layout(
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"])),
            height=height,
            yaxis=dict(
                gridcolor="rgba(30, 41, 59, 0.3)",
                tickfont=dict(size=9, color=COLORS["text_muted"]),
            ),
        )
    )
    return fig


def stacked_bar_chart(df, x, y_cols, names=None, colors=None, title="", height=350):
    """Create a stacked bar chart for score decomposition."""
    fig = go.Figure()
    names = names or y_cols
    default_colors = [COLORS["accent_cyan"], COLORS["accent_blue"],
                      COLORS["accent_indigo"], COLORS["accent_purple"]]
    colors = colors or default_colors

    for i, (col, name) in enumerate(zip(y_cols, names)):
        fig.add_trace(go.Bar(
            x=df[x],
            y=df[col],
            name=name,
            marker=dict(color=colors[i % len(colors)]),
        ))

    fig.update_layout(
        **get_plotly_layout(
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"])),
            height=height,
            barmode="stack",
            showlegend=True,
        )
    )
    return fig


def scatter_chart(df, x, y, color_col=None, size_col=None, title="", height=350,
                  color_map=None):
    """Create a styled scatter plot."""
    if color_col and color_map:
        fig = px.scatter(
            df, x=x, y=y, color=color_col, size=size_col,
            color_discrete_map=color_map,
        )
    elif color_col:
        fig = px.scatter(df, x=x, y=y, color=color_col, size=size_col)
    else:
        fig = go.Figure(go.Scatter(
            x=df[x], y=df[y],
            mode="markers",
            marker=dict(color=COLORS["accent_cyan"], size=8),
        ))

    fig.update_layout(
        **get_plotly_layout(
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"])),
            height=height,
        )
    )
    return fig


def waterfall_chart(categories, values, title="", height=350):
    """Create a waterfall chart for ROI projection."""
    measures = ["absolute"] + ["relative"] * (len(values) - 2) + ["total"]

    fig = go.Figure(go.Waterfall(
        orientation="v",
        x=categories,
        y=values,
        measure=measures,
        connector=dict(line=dict(color=COLORS["border"])),
        increasing=dict(marker=dict(color=COLORS["low"])),
        decreasing=dict(marker=dict(color=COLORS["critical"])),
        totals=dict(marker=dict(color=COLORS["accent_cyan"])),
    ))

    fig.update_layout(
        **get_plotly_layout(
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"])),
            height=height,
        )
    )
    return fig


def activity_timeline_chart(data, title="Activity Timeline", height=300):
    """Create a weekly activity bar chart matching Screenshot 4.

    Parameters
    ----------
    data : list of dict
        Each dict has: day, critical (int), standard (int).
    """
    days = [d["day"] for d in data]
    critical = [d.get("critical", 0) for d in data]
    standard = [d.get("standard", 0) for d in data]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=days, y=standard, name="Standard",
        marker=dict(color=COLORS["accent_blue"], cornerradius=2),
    ))
    fig.add_trace(go.Bar(
        x=days, y=critical, name="Critical",
        marker=dict(color=COLORS["critical"], cornerradius=2),
    ))

    fig.update_layout(
        **get_plotly_layout(
            title=dict(text=title, font=dict(size=13, color=COLORS["text_secondary"])),
            height=height,
            barmode="stack",
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                font=dict(size=10),
            ),
        )
    )
    return fig
