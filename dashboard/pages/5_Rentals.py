"""Rentals page: average residential rent per m² (EUR/month) by capital, over time.

Self-contained rental section. Rent is a real €/m² level (not an index), sourced from the annual
Deloitte Property Index — see the Methodology page and docs/data_sources.md for the caveats.
"""

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
    "Rental values",
    "Average residential rent per square metre (EUR/month) across the capitals, and how it has "
    "moved since 2016.",
    accent_word="Rental",
)

with get_session() as session:
    summary_df = analytics.get_summary_table(session)
    annual_df = analytics.get_annual_metrics(session)

# Rent coverage starts in 2016 (the property index runs from 2015); drop the empty 2015 rows so
# the time series doesn't carry a leading gap.
rent_annual = annual_df.dropna(subset=["rental_per_sqm"])

st.subheader("Rent per m² over time")
st.plotly_chart(
    charts.metric_line_chart(rent_annual, "rental_per_sqm", "Rent (€/m²/month)"),
    width="stretch",
)

st.subheader("Latest rent by city (€/m²/month)")
st.plotly_chart(
    charts.metric_bar_chart(summary_df, "latest_rental_per_sqm", "Latest rent (€/m²/month)"),
    width="stretch",
)

st.subheader("Rent growth by city (CAGR, 2016–latest)")
st.plotly_chart(
    charts.metric_bar_chart(summary_df, "rental_cagr_pct", "Rent CAGR (%)"),
    width="stretch",
)

st.subheader("Rental summary")
rental_table = summary_df[["city", "country", "latest_rental_per_sqm", "rental_cagr_pct"]]
theme.styled_dataframe(rental_table)

st.caption(
    "Source: Deloitte Property Index (annual editions 2017–2025, covering rent years 2016–2024). "
    "London is the mean of the published inner/outer figures. Deloitte's rent methodology and "
    "labels vary across editions (average vs. asking rent), so early-year and cross-city "
    "comparisons are indicative — see the Methodology page for detail. Palma isn't in Deloitte's "
    "coverage, so it has no rent data here yet — see the Mallorca Deep Dive page for its "
    "property-price detail."
)
