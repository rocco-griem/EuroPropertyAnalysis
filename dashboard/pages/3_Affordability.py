"""Affordability page: how property prices are moving relative to incomes, per city."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components import charts
from components.bootstrap import ensure_database
from src.database.connection import get_session
from src.services import analytics

st.set_page_config(page_title="EuroPropertyAnalysis — Affordability", layout="wide")
ensure_database()

st.title("Affordability")
st.caption(
    "Affordability pressure = property price growth minus income growth, in percentage "
    "points. A positive value means prices have grown faster than incomes."
)

with get_session() as session:
    summary_df = analytics.get_summary_table(session)
    annual_df = analytics.get_annual_metrics(session)

st.subheader("Affordability pressure over time")
st.plotly_chart(
    charts.metric_line_chart(annual_df, "affordability_pressure_pct", "Affordability pressure (pp)"),
    width="stretch",
)

st.subheader("Average affordability pressure by city (whole period)")
st.plotly_chart(
    charts.metric_bar_chart(
        summary_df, "avg_affordability_pressure_pct", "Avg affordability pressure (pp)"
    ),
    width="stretch",
)

st.subheader("Capital vs. national market gap (end of period)")
st.caption("A capital's cumulative growth minus its country's cumulative growth, in percentage points.")
st.plotly_chart(
    charts.metric_bar_chart(
        summary_df, "capital_vs_national_gap_pct", "Capital vs national gap (pp)"
    ),
    width="stretch",
)

st.subheader("Full metrics")
st.dataframe(summary_df, hide_index=True)
