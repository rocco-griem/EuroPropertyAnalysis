"""City Comparison page: pick cities and compare price trajectories and headline metrics."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components import charts
from components.bootstrap import ensure_database
from src.database.connection import get_session
from src.services import analytics

st.set_page_config(page_title="EuroPropertyAnalysis — City Comparison", layout="wide")
ensure_database()

st.title("City Comparison")
st.caption("Compare price trajectories and headline metrics across selected cities.")

with get_session() as session:
    summary_df = analytics.get_summary_table(session)
    all_cities = summary_df["city"].tolist()
    selected_cities = st.multiselect("Cities to compare", options=all_cities, default=all_cities[:2])
    annual_df = analytics.get_annual_metrics(session, city_names=selected_cities or None)

selected_summary_df = summary_df[summary_df["city"].isin(selected_cities)]

if not selected_cities:
    st.info("Select at least one city to compare.")
else:
    st.subheader("Property price index over time (real, inflation-adjusted)")
    st.plotly_chart(charts.property_index_line_chart(annual_df), width="stretch")

    st.subheader("CAGR (%)")
    st.plotly_chart(
        charts.metric_bar_chart(selected_summary_df, "cagr_pct", "CAGR (%)"), width="stretch"
    )

    st.subheader("Volatility (%)")
    st.plotly_chart(
        charts.metric_bar_chart(selected_summary_df, "volatility_pct", "Volatility (%)"),
        width="stretch",
    )

    st.subheader("Full metrics")
    st.dataframe(selected_summary_df, hide_index=True)
