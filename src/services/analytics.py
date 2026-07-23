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

from src.database.models import AnnualMetric, City, Country, PropertyIndexQuarterly, SummaryMetric

# Default `place_types` filter for the main comparison views (capitals + non-capital cities like
# Palma) — excludes "island" places (e.g. Mallorca), which are shown only on their own deep-dive
# page via an explicit `place_types=("island",)` call.
MAIN_PLACE_TYPES = ("capital", "city")


def list_available_cities(
    session: Session, place_types: Sequence[str] | None = MAIN_PLACE_TYPES
) -> pd.DataFrame:
    """Cities that have a computed summary, for populating a dashboard city selector.

    Columns: city, country, place_type, parent.

    `place_types=None` returns every place type; the default restricts to the main
    capitals-and-cities comparison set.
    """
    parent_city = City.__table__.alias("parent_city")
    query = (
        select(
            City.name.label("city"),
            Country.name.label("country"),
            City.place_type,
            parent_city.c.name.label("parent"),
        )
        .join(Country, City.country_id == Country.id)
        .join(SummaryMetric, SummaryMetric.city_id == City.id)
        .outerjoin(parent_city, City.parent_id == parent_city.c.id)
        .order_by(City.name)
    )
    if place_types is not None:
        query = query.where(City.place_type.in_(place_types))
    rows = session.execute(query).all()
    return pd.DataFrame(rows, columns=["city", "country", "place_type", "parent"])


def get_summary_table(
    session: Session, place_types: Sequence[str] | None = MAIN_PLACE_TYPES
) -> pd.DataFrame:
    """One row per city with whole-period aggregate metrics, for the comparison leaderboard.

    Columns: city, country, place_type, parent, start_year, end_year, total_growth_pct, cagr_pct,
    volatility_pct, risk_adjusted_return, avg_affordability_pressure_pct,
    capital_vs_national_gap_pct, latest_rental_per_sqm, rental_cagr_pct, data_quality_note (None
    unless the city's source is a methodological outlier).

    `place_types=None` returns every place type; the default restricts to the main
    capitals-and-cities comparison set (excludes islands like Mallorca).
    """
    columns = [
        "city",
        "country",
        "place_type",
        "parent",
        "start_year",
        "end_year",
        "total_growth_pct",
        "cagr_pct",
        "volatility_pct",
        "risk_adjusted_return",
        "avg_affordability_pressure_pct",
        "capital_vs_national_gap_pct",
        "latest_rental_per_sqm",
        "rental_cagr_pct",
        "data_quality_note",
    ]
    parent_city = City.__table__.alias("parent_city")
    query = (
        select(
            City.name.label("city"),
            Country.name.label("country"),
            City.place_type,
            parent_city.c.name.label("parent"),
            SummaryMetric.start_year,
            SummaryMetric.end_year,
            SummaryMetric.total_growth_pct,
            SummaryMetric.cagr_pct,
            SummaryMetric.volatility_pct,
            SummaryMetric.risk_adjusted_return,
            SummaryMetric.avg_affordability_pressure_pct,
            SummaryMetric.capital_vs_national_gap_pct,
            SummaryMetric.latest_rental_per_sqm,
            SummaryMetric.rental_cagr_pct,
            City.data_quality_note,
        )
        .join(City, SummaryMetric.city_id == City.id)
        .join(Country, City.country_id == Country.id)
        .outerjoin(parent_city, City.parent_id == parent_city.c.id)
        .order_by(City.name)
    )
    if place_types is not None:
        query = query.where(City.place_type.in_(place_types))
    rows = session.execute(query).all()
    return pd.DataFrame(rows, columns=columns)


def get_annual_metrics(
    session: Session,
    city_names: Sequence[str] | None = None,
    place_types: Sequence[str] | None = MAIN_PLACE_TYPES,
) -> pd.DataFrame:
    """Year-by-year metrics, for time series charts.

    Columns: city, country, year, property_index_nominal, property_index_real, yoy_growth_pct,
    affordability_pressure_pct, capital_vs_national_gap_pct, rental_per_sqm.

    `city_names=None` (the default) returns every place passing the `place_types` filter.
    `place_types=None` disables that filter — pass `place_types=("island",)` for Mallorca-only.
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
        "rental_per_sqm",
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
            AnnualMetric.rental_per_sqm,
        )
        .join(City, AnnualMetric.city_id == City.id)
        .join(Country, City.country_id == Country.id)
        .order_by(City.name, AnnualMetric.year)
    )
    if city_names is not None:
        query = query.where(City.name.in_(city_names))
    if place_types is not None:
        query = query.where(City.place_type.in_(place_types))
    rows = session.execute(query).all()
    return pd.DataFrame(rows, columns=columns)


def get_quarterly_property_index(
    session: Session, city_names: Sequence[str] | None = None
) -> pd.DataFrame:
    """Quarterly EUR/m² property values, for cities with sub-annual history (currently Palma and
    Mallorca only — see `PropertyIndexQuarterly`'s docstring). Used by the Mallorca deep-dive page.

    Columns: city, country, year, quarter, eur_per_sqm. No `place_types` filter — quarterly data
    exists only for the deep-dive places, so callers name the cities they want directly.
    """
    query = (
        select(
            City.name.label("city"),
            Country.name.label("country"),
            PropertyIndexQuarterly.year,
            PropertyIndexQuarterly.quarter,
            PropertyIndexQuarterly.eur_per_sqm,
        )
        .join(City, PropertyIndexQuarterly.city_id == City.id)
        .join(Country, City.country_id == Country.id)
        .order_by(City.name, PropertyIndexQuarterly.year, PropertyIndexQuarterly.quarter)
    )
    if city_names is not None:
        query = query.where(City.name.in_(city_names))
    rows = session.execute(query).all()
    return pd.DataFrame(rows, columns=["city", "country", "year", "quarter", "eur_per_sqm"])
