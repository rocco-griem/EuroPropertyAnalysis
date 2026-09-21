"""Methodology page: explains the metrics, data, and caveats behind the dashboard."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components import metric_cards, theme
from components.bootstrap import ensure_database
from src.config import settings
from src.database.connection import get_session
from src.services import analytics

theme.inject_css()
ensure_database()

theme.page_header("Methodology", accent_word="Methodology")

with get_session() as session:
    summary_df = analytics.get_summary_table(session)

current_cities = (
    ", ".join(sorted(summary_df["city"])) if not summary_df.empty else "none loaded yet"
)

st.markdown(
    f"""
### What this dashboard shows

Historical residential property performance for European capital cities, benchmarked against
each city's own national housing market, from **{settings.START_YEAR}** to the latest available
year. Every metric below is computed by the same tested code that produces the numbers on the
other pages — the formulas here are exactly what runs.
"""
)

st.markdown("### The formulas")

st.markdown(
    "**Price index (rebasing).** Each raw price series is rescaled so its first year equals 100, "
    "so all cities start from a common base and the lines are directly comparable:"
)
st.latex(r"\text{index}_t = \frac{\text{price}_t}{\text{price}_{\text{start}}} \times 100")

st.markdown(
    "**Real (inflation-adjusted) index.** The nominal index is deflated by the country's CPI, "
    "expressed in start-year money. Because the nominal index is 100 at the start, the real index "
    "is too, so any gap between them is pure inflation:"
)
st.latex(r"\text{real}_t = \text{nominal}_t \times \frac{\text{CPI}_{\text{start}}}{\text{CPI}_t}")

st.markdown(
    "**Total growth** — cumulative change in the (nominal) index over the whole period; "
    "**CAGR** — the constant annual rate that compounds to it, where "
    r"$N = \text{years} - 1$ is the number of year-steps:"
)
st.latex(
    r"\text{total growth} = \frac{P_{\text{end}} - P_{\text{start}}}{P_{\text{start}}}"
    r"\qquad\qquad"
    r"\text{CAGR} = \left(\frac{P_{\text{end}}}{P_{\text{start}}}\right)^{\!1/N} - 1"
)

st.markdown(
    "**Volatility** — the **sample** standard deviation (divisor $n-1$) of the year-on-year "
    "growth rates $g_t$; it measures how bumpy the ride was, not how large the gains:"
)
st.latex(
    r"g_t = \frac{P_t - P_{t-1}}{P_{t-1}}"
    r"\qquad\qquad"
    r"\text{volatility} = \sqrt{\frac{1}{n-1}\sum_{t}\left(g_t - \bar{g}\right)^2}"
)

st.markdown(
    "**Risk-adjusted return** — CAGR per unit of volatility (a Sharpe-like ratio with no "
    "risk-free rate); higher means more growth for each unit of year-to-year swing:"
)
st.latex(r"\text{risk-adjusted return} = \frac{\text{CAGR}}{\text{volatility}}")

st.markdown(
    "**Affordability pressure (pp)** — cumulative property-price growth minus cumulative income "
    "growth, where each cumulative growth is $\\text{index}/100 - 1$. Positive means prices "
    "outpaced incomes. The headline figure is the **mean across all years**:"
)
st.latex(
    r"\text{affordability pressure}_t = "
    r"\big(\text{price growth}_t - \text{income growth}_t\big)\times 100"
)

st.markdown(
    "**Capital vs. national gap (pp)** — a capital's cumulative growth minus its country's "
    "cumulative national growth. Positive means the capital outperformed its own national market; "
    "the headline figure is the **end-of-period** value:"
)
st.latex(
    r"\text{capital vs national}_t = "
    r"\big(\text{city growth}_t - \text{national growth}_t\big)\times 100"
)

st.markdown(
    "**Rent (€/m²) and rent CAGR.** Rent is a real level (euros per m² per month), not an index, "
    "so it is shown as published. Its whole-period growth uses the same CAGR formula over the "
    "years with rental data:"
)
st.latex(
    r"\text{rent CAGR} = \left(\frac{\text{rent}_{\text{end}}}{\text{rent}_{\text{start}}}"
    r"\right)^{\!1/N} - 1"
)

st.markdown(
    f"""
### Data

Showing **real historical data** for {current_cities}, sourced from national statistical offices,
Eurostat, and OECD (see `docs/data_sources.md` for the full per-country and per-city breakdown).
Cities are only included where a credible city-level property index exists — national data alone
is never substituted for a missing city series. Data-discovery research confirmed a usable source
for 9 of the 10 originally targeted capitals; Lisbon was excluded because its municipal series is
fragmented across incompatible methodology vintages with no clean period-length coverage. Madrid
and Palma are flagged below as methodology outliers (private, appraisal-based Tinsa source) rather
than dropped.

**Palma** was added as a place of special interest (M9) — a non-capital city, but the Balearic
Islands' regional capital, so it's grouped with the other cities here. **Mallorca**, the island
itself, is a different kind of place (not a city) and is shown only on the Mallorca Deep Dive
page, not in this main comparison — see that page and `docs/data_sources.md` for its own
methodology caveats (it's a regional proxy, not a Mallorca-specific series).

**Rental values** come from the annual **Deloitte Property Index** (editions 2017–2025, covering
rent years 2016–2024) — the average monthly rent in €/m² read from each report's rent chart.
London is the mean of the published inner/outer figures. Deloitte's rent methodology and labels
vary across editions (average vs. asking rent, and some early-year contracted-rent effects — e.g.
Berlin), so the rental series is **indicative**: use it for broad level and trend, not precise
year-on-year moves. Rent-year 2015 is not published, so the rental series starts in 2016.

### Caveats

- Past performance is not predictive of future returns.
- Small annual sample sizes make volatility estimates indicative rather than precise.
- Income data is available only at country level, not city level, so affordability pressure
  compares a city's property prices against its *national* income growth.
- Rental figures are indicative and not fully methodologically consistent across Deloitte editions.
"""
)

metric_cards.render_data_quality_notes(summary_df)
