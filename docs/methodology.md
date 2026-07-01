# Methodology

> Stub — expanded as metrics and data are finalised.

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
incomes (housing became less affordable). Income data is country-level in Version 1.

## Capital vs national
Each city index is compared with its national house price index; the gap is
`city_growth - national_growth` in percentage points.

## Disclaimer
Historical analysis only. Past performance does not predict future returns. Not investment advice.
