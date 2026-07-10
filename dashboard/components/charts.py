"""Reusable Plotly chart builders for the dashboard.

Kept separate from `app.py` / future pages so the same chart can be reused across pages (e.g.
Overview and City Comparison in M6) without duplicating the Plotly setup.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def property_index_line_chart(annual_df: pd.DataFrame) -> go.Figure:
    """One line per city: real (inflation-adjusted) property index, base year = 100."""
    fig = px.line(
        annual_df,
        x="year",
        y="property_index_real",
        color="city",
        markers=True,
        labels={"year": "Year", "property_index_real": "Property index (real, base = 100)"},
    )
    fig.update_layout(legend_title_text="City", hovermode="x unified")
    return fig
