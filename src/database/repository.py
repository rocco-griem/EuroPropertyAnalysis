"""CRUD/upsert/query helpers for the database layer.

Plain functions taking an explicit `Session` (no repository classes) so call sites stay explicit
about transactions — a caller decides when to commit, typically via `connection.get_session()`.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import (
    AnnualMetric,
    City,
    Country,
    DataSource,
    IncomeIndex,
    InflationIndex,
    PropertyIndex,
    RentalPrice,
    SummaryMetric,
)

# --------------------------------------------------------------------------------------
# Reference data
# --------------------------------------------------------------------------------------


def get_or_create_country(
    session: Session, *, name: str, iso_code: str, currency_code: str
) -> Country:
    country = session.scalar(select(Country).where(Country.name == name))
    if country is None:
        country = Country(name=name, iso_code=iso_code, currency_code=currency_code)
        session.add(country)
        session.flush()
    return country


def get_or_create_city(
    session: Session, *, name: str, country: Country, data_quality_note: str | None = None
) -> City:
    city = session.scalar(select(City).where(City.name == name, City.country_id == country.id))
    if city is None:
        city = City(name=name, country=country, data_quality_note=data_quality_note)
        session.add(city)
        session.flush()
    return city


def get_or_create_data_source(
    session: Session,
    *,
    name: str,
    url: str | None = None,
    series_type: str | None = None,
    description: str | None = None,
    access_date: dt.date | None = None,
) -> DataSource:
    source = session.scalar(select(DataSource).where(DataSource.name == name))
    if source is None:
        source = DataSource(
            name=name,
            url=url,
            series_type=series_type,
            description=description,
            access_date=access_date,
        )
        session.add(source)
        session.flush()
    return source


def list_cities(session: Session) -> list[City]:
    return list(session.scalars(select(City)))


def get_city_by_name(session: Session, name: str) -> City | None:
    return session.scalar(select(City).where(City.name == name))


# --------------------------------------------------------------------------------------
# Raw series — upsert creates on first call, overwrites the value on repeats
# --------------------------------------------------------------------------------------


def upsert_property_index(
    session: Session,
    *,
    country: Country,
    year: int,
    index_value: float,
    city: City | None = None,
    source: DataSource | None = None,
) -> PropertyIndex:
    row = session.scalar(
        select(PropertyIndex).where(
            PropertyIndex.country_id == country.id,
            PropertyIndex.city_id == (city.id if city else None),
            PropertyIndex.year == year,
        )
    )
    if row is None:
        row = PropertyIndex(country=country, city=city, year=year, index_value=index_value, source=source)
        session.add(row)
    else:
        row.index_value = index_value
        row.source = source
    session.flush()
    return row


def upsert_rental_price(
    session: Session,
    *,
    country: Country,
    city: City,
    year: int,
    rental_eur_sqm: float,
    source: DataSource | None = None,
) -> RentalPrice:
    row = session.scalar(
        select(RentalPrice).where(RentalPrice.city_id == city.id, RentalPrice.year == year)
    )
    if row is None:
        row = RentalPrice(
            country=country, city=city, year=year, rental_eur_sqm=rental_eur_sqm, source=source
        )
        session.add(row)
    else:
        row.rental_eur_sqm = rental_eur_sqm
        row.source = source
    session.flush()
    return row


def upsert_inflation_index(
    session: Session,
    *,
    country: Country,
    year: int,
    cpi_value: float,
    source: DataSource | None = None,
) -> InflationIndex:
    row = session.scalar(
        select(InflationIndex).where(InflationIndex.country_id == country.id, InflationIndex.year == year)
    )
    if row is None:
        row = InflationIndex(country=country, year=year, cpi_value=cpi_value, source=source)
        session.add(row)
    else:
        row.cpi_value = cpi_value
        row.source = source
    session.flush()
    return row


def upsert_income_index(
    session: Session,
    *,
    country: Country,
    year: int,
    index_value: float,
    source: DataSource | None = None,
) -> IncomeIndex:
    row = session.scalar(
        select(IncomeIndex).where(IncomeIndex.country_id == country.id, IncomeIndex.year == year)
    )
    if row is None:
        row = IncomeIndex(country=country, year=year, index_value=index_value, source=source)
        session.add(row)
    else:
        row.index_value = index_value
        row.source = source
    session.flush()
    return row


# --------------------------------------------------------------------------------------
# Computed results — upsert so pipeline re-runs overwrite previous values for the same key
# --------------------------------------------------------------------------------------


def upsert_annual_metric(
    session: Session,
    *,
    city: City,
    year: int,
    property_index_nominal: float | None = None,
    property_index_real: float | None = None,
    yoy_growth_pct: float | None = None,
    affordability_pressure_pct: float | None = None,
    capital_vs_national_gap_pct: float | None = None,
    rental_per_sqm: float | None = None,
) -> AnnualMetric:
    row = session.scalar(
        select(AnnualMetric).where(AnnualMetric.city_id == city.id, AnnualMetric.year == year)
    )
    if row is None:
        row = AnnualMetric(city=city, year=year)
        session.add(row)
    row.property_index_nominal = property_index_nominal
    row.property_index_real = property_index_real
    row.yoy_growth_pct = yoy_growth_pct
    row.affordability_pressure_pct = affordability_pressure_pct
    row.capital_vs_national_gap_pct = capital_vs_national_gap_pct
    row.rental_per_sqm = rental_per_sqm
    session.flush()
    return row


def upsert_summary_metric(
    session: Session,
    *,
    city: City,
    start_year: int,
    end_year: int,
    total_growth_pct: float | None = None,
    cagr_pct: float | None = None,
    volatility_pct: float | None = None,
    risk_adjusted_return: float | None = None,
    avg_affordability_pressure_pct: float | None = None,
    capital_vs_national_gap_pct: float | None = None,
    latest_rental_per_sqm: float | None = None,
    rental_cagr_pct: float | None = None,
) -> SummaryMetric:
    row = session.scalar(select(SummaryMetric).where(SummaryMetric.city_id == city.id))
    if row is None:
        row = SummaryMetric(city=city, start_year=start_year, end_year=end_year)
        session.add(row)
    row.start_year = start_year
    row.end_year = end_year
    row.total_growth_pct = total_growth_pct
    row.cagr_pct = cagr_pct
    row.volatility_pct = volatility_pct
    row.risk_adjusted_return = risk_adjusted_return
    row.avg_affordability_pressure_pct = avg_affordability_pressure_pct
    row.capital_vs_national_gap_pct = capital_vs_national_gap_pct
    row.latest_rental_per_sqm = latest_rental_per_sqm
    row.rental_cagr_pct = rental_cagr_pct
    row.computed_at = dt.datetime.now(dt.timezone.utc)
    session.flush()
    return row
