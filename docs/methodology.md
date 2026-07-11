# Methodology

## Data

Nine European capitals, **2015–2024**: London, Paris, Berlin, Madrid, Amsterdam, Vienna, Warsaw,
Prague, Budapest. A tenth candidate, Lisbon, was evaluated and excluded — its municipal series is
fragmented across incompatible statistical-methodology vintages with no clean period-length
coverage. Full per-country and per-city source list (Eurostat, ONS/Land Registry, INSEE, CBS,
OeNB, MNB, NBP, vdp Research, ČSÚ, Tinsa, OECD): [`docs/data_sources.md`](data_sources.md).

Every included city has a **true city-level property price index** — national figures are never
substituted for missing city data. One exception is flagged rather than hidden: **Madrid's** index
is Tinsa IMIE Local Markets, a private, appraisal-based series, not an official transaction
statistic like every other city here. This caveat is also surfaced directly in the dashboard via
`City.data_quality_note`.

Income data is available only at **country level**, not city level, in every source found — so
affordability pressure compares a city's property prices against its *national* income growth, not
a city-specific one.

## Indices and rebasing
All property and CPI series are rebased to **100 at the start year** so cities with different
source base years are comparable. Growth is read directly off the rebased index.

## Growth metrics
- **Total growth** — change over the whole period, `(end - start) / start`.
- **CAGR** — compound annual growth rate, `(end / start) ** (1 / years) - 1`.
- **Annual growth rates** — year-on-year change of the index.

## Risk metrics
- **Volatility** — sample standard deviation (n-1) of annual growth rates.
- **Risk-adjusted return** — `CAGR / volatility` (Sharpe-like, no risk-free rate).
- *Caveat:* with ~10 annual observations these are indicative, not precise.

## Real (inflation-adjusted) values
Nominal indices are deflated by CPI: `real = nominal * (cpi_base / cpi)`, expressing growth in
constant base-year money.

## Affordability pressure
`property_price_growth - income_growth` in percentage points. Positive means prices outpaced
incomes (housing became less affordable).

## Capital vs national
Each city index is compared with its national house price index; the gap is
`city_growth - national_growth` in percentage points.

## Disclaimer
Historical analysis only. Past performance does not predict future returns. Not investment advice.
