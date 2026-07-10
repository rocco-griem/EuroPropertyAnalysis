"""Analytics query layer the dashboard reads from.

Every function here takes a `Session` and returns a `pandas.DataFrame` shaped for a specific
chart or table. Streamlit code should only ever call into this module — never build a
SQLAlchemy query itself — so the query logic stays testable independent of the UI.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import AnnualMetric, City, Country, SummaryMetric


def list_available_cities(session: Session) -> pd.DataFrame:
    """Cities that have a computed summary, for populating a dashboard city selector.

    Columns: city, country.
    """
    rows = session.execute(
        select(City.name.label("city"), Country.name.label("country"))
        .join(Country, City.country_id == Country.id)
        .join(SummaryMetric, SummaryMetric.city_id == City.id)
        .order_by(City.name)
    ).all()
    return pd.DataFrame(rows, columns=["city", "country"])


def get_summary_table(session: Session) -> pd.DataFrame:
    """One row per city with whole-period aggregate metrics, for the comparison leaderboard.

    Columns: city, country, start_year, end_year, total_growth_pct, cagr_pct, volatility_pct,
    risk_adjusted_return, avg_affordability_pressure_pct, capital_vs_national_gap_pct,
    data_quality_note (None unless the city's source is a methodological outlier).
    """
    columns = [
        "city",
        "country",
        "start_year",
        "end_year",
        "total_growth_pct",
        "cagr_pct",
        "volatility_pct",
        "risk_adjusted_return",
        "avg_affordability_pressure_pct",
        "capital_vs_national_gap_pct",
        "data_quality_note",
    ]
    rows = session.execute(
        select(
            City.name.label("city"),
            Country.name.label("country"),
            SummaryMetric.start_year,
            SummaryMetric.end_year,
            SummaryMetric.total_growth_pct,
            SummaryMetric.cagr_pct,
            SummaryMetric.volatility_pct,
            SummaryMetric.risk_adjusted_return,
            SummaryMetric.avg_affordability_pressure_pct,
            SummaryMetric.capital_vs_national_gap_pct,
            City.data_quality_note,
        )
        .join(City, SummaryMetric.city_id == City.id)
        .join(Country, City.country_id == Country.id)
        .order_by(City.name)
    ).all()
    return pd.DataFrame(rows, columns=columns)


def get_annual_metrics(session: Session, city_names: Sequence[str] | None = None) -> pd.DataFrame:
    """Year-by-year metrics, for time series charts.

    Columns: city, country, year, property_index_nominal, property_index_real, yoy_growth_pct,
    affordability_pressure_pct, capital_vs_national_gap_pct.

    `city_names=None` (the default) returns every city; otherwise only the named ones.
    """
    columns = [
        "city",
        "country",
        "year",
        "property_index_nominal",
        "property_index_real",
        "yoy_growth_pct",
        "affordability_pressure_pct",
        "capital_vs_national_gap_pct",
    ]
    query = (
        select(
            City.name.label("city"),
            Country.name.label("country"),
            AnnualMetric.year,
            AnnualMetric.property_index_nominal,
            AnnualMetric.property_index_real,
            AnnualMetric.yoy_growth_pct,
            AnnualMetric.affordability_pressure_pct,
            AnnualMetric.capital_vs_national_gap_pct,
        )
        .join(City, AnnualMetric.city_id == City.id)
        .join(Country, City.country_id == Country.id)
        .order_by(City.name, AnnualMetric.year)
    )
    if city_names is not None:
        query = query.where(City.name.in_(city_names))
    rows = session.execute(query).all()
    return pd.DataFrame(rows, columns=columns)
