"""Tests for src.services.analytics — the query layer the dashboard reads from."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.database.models import Base
from src.database.repository import (
    get_or_create_city,
    get_or_create_country,
    upsert_income_index,
    upsert_inflation_index,
    upsert_property_index,
)
from src.pipeline.compute_metrics import compute_city_metrics
from src.services.analytics import get_annual_metrics, get_summary_table, list_available_cities


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _seed_city(
    session, *, country_name, iso_code, city_name, city_values, national_values, cpi_values, income_values, years
):
    country = get_or_create_country(session, name=country_name, iso_code=iso_code, currency_code="EUR")
    city = get_or_create_city(session, name=city_name, country=country)
    for year, value in zip(years, city_values):
        upsert_property_index(session, country=country, city=city, year=year, index_value=value)
    for year, value in zip(years, national_values):
        upsert_property_index(session, country=country, year=year, index_value=value)
    for year, value in zip(years, cpi_values):
        upsert_inflation_index(session, country=country, year=year, cpi_value=value)
    for year, value in zip(years, income_values):
        upsert_income_index(session, country=country, year=year, index_value=value)
    compute_city_metrics(session, city)
    return city


def _seed_two_cities(session):
    years = [2015, 2016, 2017]
    _seed_city(
        session,
        country_name="France",
        iso_code="FR",
        city_name="Paris",
        city_values=[100, 110, 121],
        national_values=[100, 105, 110],
        cpi_values=[100, 102, 104],
        income_values=[100, 103, 106],
        years=years,
    )
    _seed_city(
        session,
        country_name="Spain",
        iso_code="ES",
        city_name="Madrid",
        city_values=[100, 104, 108],
        national_values=[100, 103, 106],
        cpi_values=[100, 101, 103],
        income_values=[100, 102, 104],
        years=years,
    )


class TestListAvailableCities:
    def test_returns_all_cities_with_a_summary(self, session):
        _seed_two_cities(session)

        df = list_available_cities(session)

        assert sorted(df["city"]) == ["Madrid", "Paris"]
        assert set(df.columns) == {"city", "country"}

    def test_empty_database_returns_empty_dataframe(self, session):
        df = list_available_cities(session)

        assert df.empty


class TestGetSummaryTable:
    def test_one_row_per_city(self, session):
        _seed_two_cities(session)

        df = get_summary_table(session)

        assert len(df) == 2
        assert set(df["city"]) == {"Madrid", "Paris"}

    def test_values_match_the_computed_metrics(self, session):
        _seed_two_cities(session)

        df = get_summary_table(session)

        paris = df[df["city"] == "Paris"].iloc[0]
        assert paris["country"] == "France"
        assert paris["total_growth_pct"] == pytest.approx(21.0)
        assert paris["cagr_pct"] == pytest.approx(10.0)


class TestGetAnnualMetrics:
    def test_returns_all_cities_by_default(self, session):
        _seed_two_cities(session)

        df = get_annual_metrics(session)

        assert len(df) == 6  # 2 cities * 3 years
        assert set(df["city"]) == {"Madrid", "Paris"}

    def test_filters_to_requested_cities(self, session):
        _seed_two_cities(session)

        df = get_annual_metrics(session, city_names=["Paris"])

        assert set(df["city"]) == {"Paris"}
        assert len(df) == 3

    def test_rows_ordered_by_year_within_city(self, session):
        _seed_two_cities(session)

        df = get_annual_metrics(session, city_names=["Paris"])

        assert list(df["year"]) == [2015, 2016, 2017]

    def test_unknown_city_name_returns_empty_dataframe(self, session):
        _seed_two_cities(session)

        df = get_annual_metrics(session, city_names=["Nowhere"])

        assert df.empty
