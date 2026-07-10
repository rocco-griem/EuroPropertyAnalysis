"""Methodology page: explains the metrics, data, and caveats behind the dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components.bootstrap import ensure_database
from src.config import settings
from src.database.connection import get_session
from src.services import analytics

st.set_page_config(page_title="EuroPropertyAnalysis — Methodology", layout="wide")
ensure_database()

st.title("Methodology")

with get_session() as session:
    summary_df = analytics.get_summary_table(session)

current_cities = ", ".join(sorted(summary_df["city"])) if not summary_df.empty else "none loaded yet"

st.markdown(
    f"""
### What this dashboard shows

Historical residential property performance for European capital cities, benchmarked against
each city's own national housing market, from **{settings.START_YEAR}** to the latest available
year.

### Metrics

- **Total growth (%)** — cumulative percentage change in the price index from the first to the
  last year in the period.
- **CAGR (%)** — the compound annual growth rate implied by that total growth.
- **Volatility (%)** — standard deviation of year-on-year growth rates. *Caveat: with roughly a
  decade of annual data points, this is indicative of relative risk, not a precise estimate.*
- **Risk-adjusted return** — CAGR divided by volatility; higher means more growth per unit of
  year-on-year swings.
- **Affordability pressure (pp)** — property price growth minus income growth. Positive values
  mean prices have outpaced incomes.
- **Capital vs. national gap (pp)** — a capital's cumulative growth minus its country's
  cumulative growth, measured at the end of the period; positive means the capital
  outperformed its own national market.

### Data

Currently showing **mock, hand-written placeholder data** ({current_cities}), used to prove the
pipeline end-to-end (raw series → database → metrics → dashboard). Real national house-price,
inflation, and income data will replace it in a later milestone. Cities are only included where a
credible true city-level property index exists — national data alone is never substituted for a
missing city series — and the final list (documented in `docs/data_sources.md`) may be fewer than
the 10 originally targeted.

### Caveats

- Past performance is not predictive of future returns.
- Small annual sample sizes make volatility estimates indicative rather than precise.
- Income data is available only at country level, not city level, so affordability pressure
  compares a city's property prices against its *national* income growth.
"""
)
