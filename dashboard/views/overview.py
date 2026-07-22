"""Overview page: at-a-glance KPIs and the real property index over time, all cities by default.

Page config (title, icon) is set centrally by `app.py`'s `st.navigation` router.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components import charts, metric_cards, theme
from components.bootstrap import ensure_database
from src.database.connection import get_session
from src.services import analytics

theme.inject_css()
ensure_database()

theme.page_header(
    "EuroPropertyAnalysis",
    "Historical residential property performance across European capitals, benchmarked "
    "against national housing markets.",
    accent_word="Property",
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
theme.styled_dataframe(selected_summary_df)
metric_cards.render_data_quality_notes(selected_summary_df)
