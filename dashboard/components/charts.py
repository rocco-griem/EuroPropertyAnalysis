"""Reusable Plotly chart builders for the dashboard.

Kept separate from `app.py` / pages so the same chart can be reused across pages without
duplicating the Plotly setup. All builders route through `theme.apply_chart_theme` so the dark
template, fonts, and grid styling stay consistent, and line charts use `theme.city_color_map`
so each city keeps a stable color across every page.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components import theme


def metric_line_chart(annual_df: pd.DataFrame, y_col: str, y_label: str) -> go.Figure:
    """One line per city for a chosen `annual_metrics` column, e.g. affordability over time."""
    cities = annual_df["city"].unique().tolist() if not annual_df.empty else []
    fig = px.line(
        annual_df,
        x="year",
        y=y_col,
        color="city",
        markers=True,
        color_discrete_map=theme.city_color_map(cities),
        labels={"year": "Year", y_col: y_label},
    )
    fig.update_traces(line=dict(width=2.4), marker=dict(size=7))
    fig.update_layout(legend_title_text="City", hovermode="x unified")
    return theme.apply_chart_theme(fig)


def property_index_line_chart(annual_df: pd.DataFrame) -> go.Figure:
    """One line per city: real (inflation-adjusted) property index, base year = 100."""
    return metric_line_chart(annual_df, "property_index_real", "Property index (real, base = 100)")


def quarterly_property_chart(quarterly_df: pd.DataFrame) -> go.Figure:
    """One line per city: quarterly EUR/m², for places with sub-annual history (currently only
    Palma/Mallorca — see `analytics.get_quarterly_property_index`). A single decimal `period`
    column (year + (quarter-1)/4) drives the x-axis so quarters within a year space out evenly."""
    df = quarterly_df.copy()
    df["period"] = df["year"] + (df["quarter"] - 1) / 4
    df["period_label"] = df["year"].astype(str) + " Q" + df["quarter"].astype(str)
    cities = df["city"].unique().tolist() if not df.empty else []
    fig = px.line(
        df,
        x="period",
        y="eur_per_sqm",
        color="city",
        color_discrete_map=theme.city_color_map(cities),
        labels={"period": "Year", "eur_per_sqm": "Price (€/m²)"},
        custom_data=["period_label"],
    )
    fig.update_traces(
        line=dict(width=2.2),
        hovertemplate="%{customdata[0]}: €%{y:,.0f}/m²<extra>%{fullData.name}</extra>",
    )
    fig.update_layout(legend_title_text="City", hovermode="x unified")
    return theme.apply_chart_theme(fig)


def metric_bar_chart(summary_df: pd.DataFrame, metric_col: str, metric_label: str) -> go.Figure:
    """Horizontal bar chart of one `summary_metrics` column, one bar per city, ranked descending.

    Bars are colored on a single-hue amber ramp by value, so the ranking reads as a gradient,
    with the value printed directly on each bar (the axis is a secondary read)."""
    ranked_df = summary_df.sort_values(metric_col, ascending=False)
    fig = px.bar(
        ranked_df,
        x=metric_col,
        y="city",
        orientation="h",
        color=metric_col,
        color_continuous_scale=theme.AMBER_SCALE,
        text=ranked_df[metric_col].map(lambda v: f"{v:,.1f}"),
        labels={metric_col: metric_label, "city": "City"},
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(color=theme.TEXT),
        cliponaxis=False,
        marker=dict(line=dict(width=0)),
    )
    # Scale height with the number of bars so thickness stays consistent whether 2 or 9 cities
    # are shown (otherwise Plotly stretches a couple of bars to fill a fixed-height canvas).
    n = len(ranked_df)
    fig.update_layout(
        yaxis={"autorange": "reversed"},
        coloraxis_showscale=False,
        showlegend=False,
        height=max(240, 70 + n * 46),
        bargap=0.35,
    )
    return theme.apply_chart_theme(fig)
