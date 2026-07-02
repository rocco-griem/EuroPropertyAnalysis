"""Compute `annual_metrics` and `summary_metrics` for a city from its raw indices.

This is the orchestration layer: it reads raw rows via the repository, feeds them through the
pure functions in `src.metrics` / `src.transformation`, and writes the results back via the
repository. No formulas live here — only wiring, so the same formula is never duplicated.
"""

from __future__ import annotations

from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import City, IncomeIndex, InflationIndex, PropertyIndex
from src.database.repository import upsert_annual_metric, upsert_summary_metric
from src.metrics.affordability import affordability_pressure, capital_vs_national_gap
from src.metrics.returns import annual_growth_rates, cagr, total_growth
from src.metrics.risk import risk_adjusted_return, volatility
from src.transformation.inflation_adjustment import real_index
from src.transformation.rebasing import rebase_to_100


def _property_series(session: Session, *, country_id: int, city_id: int | None) -> dict[int, float]:
    rows = session.scalars(
        select(PropertyIndex).where(
            PropertyIndex.country_id == country_id, PropertyIndex.city_id == city_id
        )
    )
    return {row.year: row.index_value for row in rows}


def _inflation_series(session: Session, *, country_id: int) -> dict[int, float]:
    rows = session.scalars(select(InflationIndex).where(InflationIndex.country_id == country_id))
    return {row.year: row.cpi_value for row in rows}


def _income_series(session: Session, *, country_id: int) -> dict[int, float]:
    rows = session.scalars(select(IncomeIndex).where(IncomeIndex.country_id == country_id))
    return {row.year: row.index_value for row in rows}


def compute_city_metrics(session: Session, city: City) -> None:
    """Read a city's raw series, compute annual + summary metrics, and upsert both.

    Requires the city's property series, its country's national property series, CPI, and
    income series to all cover exactly the same years — Version 1 doesn't attempt partial-year
    interpolation, so a mismatch is a data problem to fix upstream, not to paper over here.
    """
    country_id = city.country_id

    city_raw = _property_series(session, country_id=country_id, city_id=city.id)
    national_raw = _property_series(session, country_id=country_id, city_id=None)
    cpi_raw = _inflation_series(session, country_id=country_id)
    income_raw = _income_series(session, country_id=country_id)

    years = sorted(city_raw)
    if not years:
        raise ValueError(f"No property index data for city_id={city.id}.")
    for label, series in (("national", national_raw), ("CPI", cpi_raw), ("income", income_raw)):
        if sorted(series) != years:
            raise ValueError(
                f"{label} series years {sorted(series)} do not match the city's "
                f"property series years {years} for city_id={city.id}."
            )

    city_nominal = rebase_to_100([city_raw[y] for y in years])
    national_nominal = rebase_to_100([national_raw[y] for y in years])
    cpi = [cpi_raw[y] for y in years]
    income_nominal = rebase_to_100([income_raw[y] for y in years])

    city_real = real_index(city_nominal, cpi)
    yoy = annual_growth_rates(city_nominal)  # fractions; one shorter than `years`

    # Cumulative growth since the start year, as of each year (index/100 - 1).
    city_cum_growth = [v / 100 - 1 for v in city_nominal]
    national_cum_growth = [v / 100 - 1 for v in national_nominal]
    income_cum_growth = [v / 100 - 1 for v in income_nominal]
    affordability_pct = [
        affordability_pressure(c, i) * 100 for c, i in zip(city_cum_growth, income_cum_growth)
    ]
    capital_vs_national_pct = [
        capital_vs_national_gap(c, n) * 100 for c, n in zip(city_cum_growth, national_cum_growth)
    ]

    for i, year in enumerate(years):
        upsert_annual_metric(
            session,
            city=city,
            year=year,
            property_index_nominal=city_nominal[i],
            property_index_real=city_real[i],
            yoy_growth_pct=yoy[i - 1] * 100 if i > 0 else None,
            affordability_pressure_pct=affordability_pct[i],
            capital_vs_national_gap_pct=capital_vs_national_pct[i],
        )

    cagr_value = cagr(city_nominal[0], city_nominal[-1], len(years) - 1)
    summary_kwargs: dict[str, object] = dict(
        city=city,
        start_year=years[0],
        end_year=years[-1],
        total_growth_pct=total_growth(city_nominal[0], city_nominal[-1]) * 100,
        cagr_pct=cagr_value * 100,
        avg_affordability_pressure_pct=mean(affordability_pct),
        capital_vs_national_gap_pct=capital_vs_national_pct[-1],
    )
    if len(yoy) >= 2:
        volatility_value = volatility(yoy)
        summary_kwargs["volatility_pct"] = volatility_value * 100
        if volatility_value != 0:
            summary_kwargs["risk_adjusted_return"] = risk_adjusted_return(cagr_value, volatility_value)

    upsert_summary_metric(session, **summary_kwargs)
