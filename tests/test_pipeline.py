"""Tests for the pipeline layer: `compute_metrics` orchestration and the mock vertical slice."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.database.models import AnnualMetric, Base, SummaryMetric
from src.database.repository import (
    get_city_by_name,
    get_or_create_city,
    get_or_create_country,
    upsert_income_index,
    upsert_inflation_index,
    upsert_property_index,
)
from src.pipeline.compute_metrics import compute_city_metrics
from src.pipeline.mock_pipeline import MOCK_CITY_TO_COUNTRY, MOCK_YEARS, load_mock_raw_data

_ISO_CODES = {"France": "FR", "Spain": "ES"}


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _seed_simple_city(session):
    """A 3-year dataset with round numbers so expected metrics can be hand-computed."""
    country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
    city = get_or_create_city(session, name="Paris", country=country)
    years = [2015, 2016, 2017]
    city_values = [100, 110, 121]  # +10% every year
    national_values = [100, 105, 110]
    cpi_values = [100, 102, 104]
    income_values = [100, 103, 106]
    for year, value in zip(years, city_values):
        upsert_property_index(session, country=country, city=city, year=year, index_value=value)
    for year, value in zip(years, national_values):
        upsert_property_index(session, country=country, year=year, index_value=value)
    for year, value in zip(years, cpi_values):
        upsert_inflation_index(session, country=country, year=year, cpi_value=value)
    for year, value in zip(years, income_values):
        upsert_income_index(session, country=country, year=year, index_value=value)
    return city


class TestComputeCityMetrics:
    def test_annual_metrics_written_for_every_year(self, session):
        city = _seed_simple_city(session)

        compute_city_metrics(session, city)

        rows = session.scalars(select(AnnualMetric).order_by(AnnualMetric.year)).all()
        assert [r.year for r in rows] == [2015, 2016, 2017]

    def test_first_year_has_no_yoy_growth(self, session):
        city = _seed_simple_city(session)
        compute_city_metrics(session, city)

        rows = session.scalars(select(AnnualMetric).order_by(AnnualMetric.year)).all()
        assert rows[0].yoy_growth_pct is None
        assert rows[1].yoy_growth_pct == pytest.approx(10.0)
        assert rows[2].yoy_growth_pct == pytest.approx(10.0)

    def test_property_index_is_rebased_to_100_at_start_year(self, session):
        city = _seed_simple_city(session)
        compute_city_metrics(session, city)

        rows = session.scalars(select(AnnualMetric).order_by(AnnualMetric.year)).all()
        assert rows[0].property_index_nominal == pytest.approx(100.0)
        assert rows[2].property_index_nominal == pytest.approx(121.0)

    def test_real_index_is_below_nominal_when_there_is_inflation(self, session):
        city = _seed_simple_city(session)
        compute_city_metrics(session, city)

        rows = session.scalars(select(AnnualMetric).order_by(AnnualMetric.year)).all()
        assert rows[2].property_index_real < rows[2].property_index_nominal

    def test_summary_totals(self, session):
        city = _seed_simple_city(session)
        compute_city_metrics(session, city)

        summary = session.scalar(select(SummaryMetric).where(SummaryMetric.city_id == city.id))
        assert summary.start_year == 2015
        assert summary.end_year == 2017
        assert summary.total_growth_pct == pytest.approx(21.0)
        assert summary.cagr_pct == pytest.approx(10.0)

    def test_volatility_is_near_zero_for_near_constant_growth(self, session):
        city = _seed_simple_city(session)
        compute_city_metrics(session, city)

        summary = session.scalar(select(SummaryMetric).where(SummaryMetric.city_id == city.id))
        # +10% every year -> volatility near 0 (not bit-exact: 121/110 has floating-point noise).
        assert summary.volatility_pct == pytest.approx(0.0, abs=1e-6)

    def test_capital_vs_national_gap_reflects_outperformance(self, session):
        city = _seed_simple_city(session)
        compute_city_metrics(session, city)

        summary = session.scalar(select(SummaryMetric).where(SummaryMetric.city_id == city.id))
        # City +21% vs national +10% over the period -> positive gap of 11 percentage points.
        assert summary.capital_vs_national_gap_pct == pytest.approx(11.0)

    def test_missing_national_series_raises(self, session):
        country = get_or_create_country(session, name="Germany", iso_code="DE", currency_code="EUR")
        city = get_or_create_city(session, name="Berlin", country=country)
        for year, value in zip([2015, 2016], [100, 110]):
            upsert_property_index(session, country=country, city=city, year=year, index_value=value)

        with pytest.raises(ValueError):
            compute_city_metrics(session, city)

    def test_mismatched_series_years_raises(self, session):
        country = get_or_create_country(session, name="Germany", iso_code="DE", currency_code="EUR")
        city = get_or_create_city(session, name="Berlin", country=country)
        for year, value in zip([2015, 2016], [100, 110]):
            upsert_property_index(session, country=country, city=city, year=year, index_value=value)
            upsert_property_index(session, country=country, year=year, index_value=value)
            upsert_income_index(session, country=country, year=year, index_value=value)
        # CPI only covers one of the two years -> mismatch.
        upsert_inflation_index(session, country=country, year=2015, cpi_value=100)

        with pytest.raises(ValueError):
            compute_city_metrics(session, city)


class TestMockPipelineVerticalSlice:
    def test_load_and_compute_for_every_demo_city(self, session):
        for city_name, country_name in MOCK_CITY_TO_COUNTRY.items():
            country = get_or_create_country(
                session,
                name=country_name,
                iso_code=_ISO_CODES[country_name],
                currency_code="EUR",
            )
            get_or_create_city(session, name=city_name, country=country)

        load_mock_raw_data(session)

        for city_name in MOCK_CITY_TO_COUNTRY:
            city = get_city_by_name(session, city_name)
            compute_city_metrics(session, city)

            annual_rows = session.scalars(
                select(AnnualMetric).where(AnnualMetric.city_id == city.id)
            ).all()
            assert len(annual_rows) == len(MOCK_YEARS)

            summary = session.scalar(select(SummaryMetric).where(SummaryMetric.city_id == city.id))
            assert summary is not None
            assert summary.start_year == MOCK_YEARS[0]
            assert summary.end_year == MOCK_YEARS[-1]

    def test_missing_city_raises(self, session):
        with pytest.raises(ValueError):
            load_mock_raw_data(session)
