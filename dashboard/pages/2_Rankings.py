"""Rankings page: leaderboard of all cities by a single whole-period metric."""

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
    "Rankings", "Rank all cities by a single whole-period metric.", accent_word="Rankings"
)

METRIC_OPTIONS: dict[str, tuple[str, str]] = {
    "Total growth (%)": ("total_growth_pct", "Total growth (%)"),
    "CAGR (%)": ("cagr_pct", "CAGR (%)"),
    "Volatility (%)": ("volatility_pct", "Volatility (%)"),
    "Risk-adjusted return": ("risk_adjusted_return", "Risk-adjusted return"),
}

with get_session() as session:
    summary_df = analytics.get_summary_table(session)

metric_choice = st.selectbox("Rank by", options=list(METRIC_OPTIONS.keys()))
metric_col, metric_label = METRIC_OPTIONS[metric_choice]

st.plotly_chart(charts.metric_bar_chart(summary_df, metric_col, metric_label), width="stretch")

st.subheader("Full leaderboard")
theme.styled_dataframe(summary_df.sort_values(metric_col, ascending=False))
metric_cards.render_data_quality_notes(summary_df)
