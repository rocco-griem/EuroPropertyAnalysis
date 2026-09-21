"""Overview page: at-a-glance KPIs and the real property index over time, all cities by default.

Page config (title, icon) is set centrally by `app.py`'s `st.navigation` router.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import streamlit.components.v1 as components

from components import charts, hero_globe, hero_map, metric_cards, theme
from components.bootstrap import ensure_database
from src.database.connection import get_session
from src.services import analytics

theme.inject_css()
ensure_database()

theme.page_header(
    "EuroPropertyAnalysis",
    "How nine European capital cities — plus Palma — have performed since 2015 — in price, "
    "after inflation, against incomes, and versus their national markets. Want to go deeper on "
    "one place? See the Mallorca Deep Dive page.",
    accent_word="Property",
)

# Day→night map of the capitals (scroll within it to bring on the city lights). Two renderings
# of the same NASA satellite imagery — a flat Web-Mercator map and a 3D rotating globe — sit
# behind a toggle so both can be compared with real data around them before picking one.
hero_choice = st.radio(
    "Hero visual",
    ["Flat map", "Globe"],
    horizontal=True,
    key="hero_choice",
    label_visibility="collapsed",
)
if hero_choice == "Globe":
    components.html(hero_globe.render(), height=560, scrolling=False)
else:
    components.html(hero_map.render(), height=560, scrolling=False)

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
