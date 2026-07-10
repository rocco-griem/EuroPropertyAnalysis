"""Reusable Plotly chart builders for the dashboard.

Kept separate from `app.py` / pages so the same chart can be reused across pages without
duplicating the Plotly setup.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def metric_line_chart(annual_df: pd.DataFrame, y_col: str, y_label: str) -> go.Figure:
    """One line per city for a chosen `annual_metrics` column, e.g. affordability over time."""
    fig = px.line(
        annual_df,
        x="year",
        y=y_col,
        color="city",
        markers=True,
        labels={"year": "Year", y_col: y_label},
    )
    fig.update_layout(legend_title_text="City", hovermode="x unified")
    return fig


def property_index_line_chart(annual_df: pd.DataFrame) -> go.Figure:
    """One line per city: real (inflation-adjusted) property index, base year = 100."""
    return metric_line_chart(annual_df, "property_index_real", "Property index (real, base = 100)")


def metric_bar_chart(summary_df: pd.DataFrame, metric_col: str, metric_label: str) -> go.Figure:
    """Horizontal bar chart of one `summary_metrics` column, one bar per city, ranked descending."""
    ranked_df = summary_df.sort_values(metric_col, ascending=False)
    fig = px.bar(
        ranked_df,
        x=metric_col,
        y="city",
        orientation="h",
        labels={metric_col: metric_label, "city": "City"},
    )
    fig.update_layout(yaxis={"autorange": "reversed"})
    return fig
