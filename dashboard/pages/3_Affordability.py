"""Affordability page: how property prices are moving relative to incomes, per city."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from components import charts, theme
from components.bootstrap import ensure_database

from src.database.connection import get_session
from src.services import analytics

theme.inject_css()
ensure_database()

theme.page_header(
    "Affordability",
    "Affordability pressure = property price growth minus income growth, in percentage "
    "points. A positive value means prices have grown faster than incomes.",
    accent_word="Affordability",
)

with get_session() as session:
    summary_df = analytics.get_summary_table(session)
    annual_df = analytics.get_annual_metrics(session)

st.subheader("Affordability pressure over time")
st.plotly_chart(
    charts.metric_line_chart(
        annual_df, "affordability_pressure_pct", "Affordability pressure (pp)"
    ),
    width="stretch",
)

st.subheader("Average affordability pressure by city (whole period)")
st.plotly_chart(
    charts.metric_bar_chart(
        summary_df, "avg_affordability_pressure_pct", "Avg affordability pressure (pp)"
    ),
    width="stretch",
)

st.subheader("Capital vs. national market gap over time")
st.caption(
    "A capital's cumulative growth minus its country's cumulative growth, in percentage points."
)
gap_fig = charts.metric_line_chart(
    annual_df, "capital_vs_national_gap_pct", "Capital vs national gap (pp)"
)
gap_fig.add_hline(y=0, line_dash="dot", line_color=theme.AXIS)
st.plotly_chart(gap_fig, width="stretch")

st.subheader("Capital vs. national market gap (end of period)")
st.plotly_chart(
    charts.metric_bar_chart(
        summary_df, "capital_vs_national_gap_pct", "Capital vs national gap (pp)"
    ),
    width="stretch",
)

st.subheader("Full metrics")
theme.styled_dataframe(summary_df)
