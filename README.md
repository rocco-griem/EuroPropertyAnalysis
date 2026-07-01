# EuroPropertyAnalysis

> **Status: work in progress (Version 1).** This README is a stub that grows with the project.

## One-sentence summary

A production-style Python analytics project comparing residential property market performance
across European capital cities from **2015 to the latest available year**, benchmarked against
each country's wider national housing market.

## The question it answers

How have European capital-city property markets performed since 2015, and how do they compare
with their wider national housing markets — in nominal terms, after inflation, and on a
risk-adjusted basis?

## Live dashboard

_Coming soon (Streamlit Community Cloud)._

## Dashboard preview

_Screenshots to be added (Overview, City Comparison, Rankings, Affordability)._

## Key questions

- Which European capitals had the strongest property price growth?
- Which cities performed best **after inflation**?
- Which cities had the best **risk-adjusted** returns?
- Which capitals **outperformed** their national housing markets?
- Where is **affordability pressure** (prices vs incomes) strongest?

## Cities analysed

Target capitals (final inclusion depends on availability of credible city-level data):
London, Paris, Berlin, Madrid, Lisbon, Amsterdam, Vienna, Warsaw, Prague, Budapest.

## Methodology (summary)

Property price indices are rebased to 100 at the start year. From these we compute total growth,
CAGR, year-on-year growth, volatility (variability of annual growth), and a risk-adjusted return
(CAGR ÷ volatility). Real (inflation-adjusted) figures deflate the nominal index by CPI.
Affordability pressure is **property-price growth minus income growth (percentage points)**.
Capital-vs-national compares each city index against its national house price index.
Full details: [`docs/methodology.md`](docs/methodology.md).

## Tech stack

Python · pandas · numpy · SQLite · SQLAlchemy · Plotly · Streamlit · pytest

## How to run locally (Windows)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
```

The data pipeline and dashboard commands will be added as those layers are built:

```bat
python -m src.pipeline.run_pipeline   :: (added at the pipeline milestone)
streamlit run dashboard/app.py        :: (added at the dashboard milestone)
```

## Project structure

```
src/
  config/          settings: paths, DB URL, city/country definitions
  metrics/         pure, tested calculations (returns, risk, affordability)
  transformation/  rebasing & inflation adjustment (pure functions)
  ingestion/       CSV loading (and optional API helpers) — later milestone
  database/        SQLAlchemy models, connection, repository — later milestone
  services/        analytics service layer the dashboard reads from — later milestone
  pipeline/        end-to-end pipeline runner — later milestone
  utils/           logging configuration
dashboard/         Streamlit app (read-only) — later milestone
tests/             pytest unit tests
data/              raw (committed CSVs), processed, database (generated)
docs/              methodology and data-source notes
```

## Limitations

- Historical analysis only — **no forecasting**.
- Capital appreciation only — no rental yield, currency adjustment, taxes, or transaction costs.
- Data availability varies by city; only cities with credible city-level data are included.
- Past performance does not predict future returns. This is **not** investment advice.

## Future extensions

Forecasting · machine learning · rental yield · currency-adjusted returns · mortgage affordability
· PostgreSQL · FastAPI · CI/CD · data-quality dashboards.
