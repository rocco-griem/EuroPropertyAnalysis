"""EuroPropertyAnalysis — Streamlit dashboard entry point (Overview page).

Run with: `streamlit run dashboard/app.py`

This page only ever reads through `src.services.analytics` — never raw SQLAlchemy queries —
so the query logic stays testable independent of the UI. Later pages (M6: City Comparison,
Rankings, Affordability, Methodology) will follow the same pattern.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sibling modules in dashboard/components importable regardless of how the script was
# launched (`streamlit run` adds the script's directory to sys.path, but test runners may not).
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from components import charts, metric_cards
from components.bootstrap import ensure_database
from src.database.connection import get_session
from src.services import analytics

st.set_page_config(page_title="EuroPropertyAnalysis", layout="wide")

ensure_database()

st.title("EuroPropertyAnalysis")
st.caption(
    "Historical residential property performance across European capitals, benchmarked "
    "against national housing markets."
)
st.warning(
    "Showing **mock placeholder data** (Paris & Madrid, 2015–2020) while real data "
    "sourcing is still in progress.",
    icon="⚠️",
)

with get_session() as session:
    summary_df = analytics.get_summary_table(session)
    cities_df = analytics.list_available_cities(session)
    all_cities = cities_df["city"].tolist()
    selected_cities = st.multiselect("Cities", options=all_cities, default=all_cities)
    annual_df = analytics.get_annual_metrics(session, city_names=selected_cities or None)

selected_summary_df = summary_df[summary_df["city"].isin(selected_cities)]

st.subheader("At a glance")
metric_cards.render_summary_cards(selected_summary_df)

st.subheader("Property price index over time (real, inflation-adjusted)")
st.plotly_chart(charts.property_index_line_chart(annual_df), width="stretch")

st.subheader("Whole-period summary")
st.dataframe(selected_summary_df, hide_index=True)
