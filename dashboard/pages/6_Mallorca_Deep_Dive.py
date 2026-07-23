"""Mallorca deep-dive page: Palma (the city, part of the main comparison) alongside Mallorca
(the island, not a capital and not part of the main comparison — shown only here).

This is the first "deep dive" section, on the same model as the Rentals page: a place of
special interest gets its own page rather than being folded into the 9-capitals-plus-Palma
comparison. It is built to grow — the sections below are independently titled so further,
more granular Mallorca data (individual resorts/municipalities, seasonality, etc.) can be added
as its own section later without restructuring the page.
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

_PLACES = ["Palma", "Mallorca"]

theme.inject_css()
ensure_database()

theme.page_header(
    "Mallorca deep dive",
    "Palma is part of the main city comparison; Mallorca — the island as a whole — is a place "
    "of special interest shown only here, where more granular Mallorca data will be added over "
    "time.",
    accent_word="Mallorca",
)

with get_session() as session:
    # place_types=None: Mallorca is an "island", excluded from the main-set default filter.
    summary_df = analytics.get_summary_table(session, place_types=None)
    annual_df = analytics.get_annual_metrics(session, city_names=_PLACES, place_types=None)
    quarterly_df = analytics.get_quarterly_property_index(session, city_names=_PLACES)

summary_df = summary_df[summary_df["city"].isin(_PLACES)]

st.subheader("At a glance")
metric_cards.render_summary_cards(summary_df)
metric_cards.render_data_quality_notes(summary_df)

st.subheader("Palma vs. Mallorca vs. Spain — property index since 2015")
st.plotly_chart(
    charts.property_index_line_chart(annual_df),
    width="stretch",
)

st.subheader("Palma / Mallorca vs. the Spanish national market")
st.caption(
    "Each place's cumulative growth minus Spain's cumulative national growth, in percentage "
    "points. Positive means the place outperformed the wider Spanish market."
)
gap_fig = charts.metric_line_chart(
    annual_df, "capital_vs_national_gap_pct", "vs. national gap (pp)"
)
gap_fig.add_hline(y=0, line_dash="dot", line_color=theme.AXIS)
st.plotly_chart(gap_fig, width="stretch")

st.subheader("Quarterly detail, 2001–present")
st.caption(
    "The only sub-annual view in the dashboard so far — Tinsa publishes Palma/Mallorca prices "
    "quarterly back to 2001, long enough to include the 2008 crash and the following recovery. "
    "Every other place's data is annual only, pending a planned quarterly re-acquisition."
)
st.plotly_chart(charts.quarterly_property_chart(quarterly_df), width="stretch")

st.subheader("Full metrics")
theme.styled_dataframe(summary_df)

st.info(
    "**Rent (€/m²) isn't available yet for Palma or Mallorca.** Spain's official SERPAVI "
    "rental-price database (built from tax records) covers both, but its data isn't published "
    "as a simple download and needs further acquisition work — tracked as a follow-up, not "
    "quietly dropped.\n\n"
    "**What's next in this section:** more granular Mallorca data — individual resorts/"
    "municipalities, seasonal (tourist-season) price patterns — will be added here as its own "
    "section, once sourced.",
    icon="🏝️",
)

st.caption(
    "Sources: property index — Tinsa IMIE Local Markets (Palma de Mallorca municipality; "
    "Mallorca uses Tinsa's Balearic Islands province figure as the closest available proxy — no "
    "official Mallorca-island-level series exists). Both are private, appraisal-based series, "
    "like Madrid's — see the Methodology page and docs/data_sources.md for the full caveat."
)
