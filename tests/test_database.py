"""Tests for the database layer: models, repository upserts, and the seed routine.

Each test gets a fresh in-memory SQLite database so tests never touch the real project
database file (`data/database/europropertyanalysis.db`).
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from src.config.settings import PLACES
from src.database.models import (
    AnnualMetric,
    Base,
    City,
    Country,
    PropertyIndex,
    PropertyIndexQuarterly,
    SummaryMetric,
)
from src.database.repository import (
    get_or_create_city,
    get_or_create_country,
    get_or_create_data_source,
    list_cities,
    set_city_parent,
    upsert_annual_metric,
    upsert_income_index,
    upsert_inflation_index,
    upsert_property_index,
    upsert_property_index_quarterly,
    upsert_summary_metric,
)


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestCountryAndCity:
    def test_get_or_create_country_is_idempotent(self, session):
        first = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
        second = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")

        assert first.id == second.id
        assert session.scalars(select(Country)).all() == [first]

    def test_get_or_create_city_is_idempotent(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
        first = get_or_create_city(session, name="Paris", country=country)
        second = get_or_create_city(session, name="Paris", country=country)

        assert first.id == second.id
        assert session.scalars(select(City)).all() == [first]

    def test_same_city_name_in_different_countries_is_allowed(self, session):
        # Guards against an over-eager uniqueness rule keyed on name alone.
        fr = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
        de = get_or_create_country(session, name="Germany", iso_code="DE", currency_code="EUR")
        get_or_create_city(session, name="Springfield", country=fr)
        get_or_create_city(session, name="Springfield", country=de)

        assert len(list_cities(session)) == 2

    def test_place_type_defaults_to_capital(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
        city = get_or_create_city(session, name="Paris", country=country)

        assert city.place_type == "capital"

    def test_place_type_can_be_set(self, session):
        country = get_or_create_country(session, name="Spain", iso_code="ES", currency_code="EUR")
        city = get_or_create_city(session, name="Mallorca", country=country, place_type="island")

        assert city.place_type == "island"

    def test_set_city_parent(self, session):
        country = get_or_create_country(session, name="Spain", iso_code="ES", currency_code="EUR")
        mallorca = get_or_create_city(
            session, name="Mallorca", country=country, place_type="island"
        )
        palma = get_or_create_city(session, name="Palma", country=country, place_type="city")

        set_city_parent(session, city=palma, parent=mallorca)

        assert palma.parent_id == mallorca.id


class TestDataSource:
    def test_get_or_create_data_source_is_idempotent(self, session):
        first = get_or_create_data_source(
            session, name="Eurostat prc_hpi_a", url="https://ec.europa.eu"
        )
        second = get_or_create_data_source(session, name="Eurostat prc_hpi_a")

        assert first.id == second.id


class TestPropertyIndexUpsert:
    def test_creates_city_level_row(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
        city = get_or_create_city(session, name="Paris", country=country)

        row = upsert_property_index(
            session, country=country, city=city, year=2015, index_value=100.0
        )

        assert row.city_id == city.id
        assert row.index_value == pytest.approx(100.0)

    def test_national_row_has_no_city(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")

        row = upsert_property_index(session, country=country, year=2015, index_value=100.0)

        assert row.city_id is None

    def test_repeat_call_updates_instead_of_duplicating(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
        city = get_or_create_city(session, name="Paris", country=country)

        upsert_property_index(session, country=country, city=city, year=2015, index_value=100.0)
        upsert_property_index(session, country=country, city=city, year=2015, index_value=105.0)

        rows = session.scalars(select(PropertyIndex)).all()
        assert len(rows) == 1
        assert rows[0].index_value == pytest.approx(105.0)

    def test_city_and_national_rows_for_same_year_coexist(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
        city = get_or_create_city(session, name="Paris", country=country)

        upsert_property_index(session, country=country, city=city, year=2015, index_value=110.0)
        upsert_property_index(session, country=country, year=2015, index_value=100.0)

        rows = session.scalars(select(PropertyIndex)).all()
        assert len(rows) == 2


class TestPropertyIndexQuarterlyUpsert:
    def test_creates_a_quarterly_row(self, session):
        country = get_or_create_country(session, name="Spain", iso_code="ES", currency_code="EUR")
        city = get_or_create_city(session, name="Palma", country=country)

        row = upsert_property_index_quarterly(
            session, country=country, city=city, year=2015, quarter=1, eur_per_sqm=1634.31
        )

        assert row.city_id == city.id
        assert row.year == 2015 and row.quarter == 1
        assert row.eur_per_sqm == pytest.approx(1634.31)

    def test_repeat_call_updates_instead_of_duplicating(self, session):
        country = get_or_create_country(session, name="Spain", iso_code="ES", currency_code="EUR")
        city = get_or_create_city(session, name="Palma", country=country)

        upsert_property_index_quarterly(
            session, country=country, city=city, year=2015, quarter=1, eur_per_sqm=1000.0
        )
        upsert_property_index_quarterly(
            session, country=country, city=city, year=2015, quarter=1, eur_per_sqm=1050.0
        )

        rows = session.scalars(select(PropertyIndexQuarterly)).all()
        assert len(rows) == 1
        assert rows[0].eur_per_sqm == pytest.approx(1050.0)

    def test_different_quarters_of_same_year_coexist(self, session):
        country = get_or_create_country(session, name="Spain", iso_code="ES", currency_code="EUR")
        city = get_or_create_city(session, name="Palma", country=country)

        upsert_property_index_quarterly(
            session, country=country, city=city, year=2015, quarter=1, eur_per_sqm=1000.0
        )
        upsert_property_index_quarterly(
            session, country=country, city=city, year=2015, quarter=2, eur_per_sqm=1010.0
        )

        rows = session.scalars(select(PropertyIndexQuarterly)).all()
        assert len(rows) == 2


class TestInflationAndIncomeUpsert:
    def test_inflation_index_upsert_updates_value(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")

        upsert_inflation_index(session, country=country, year=2015, cpi_value=100.0)
        row = upsert_inflation_index(session, country=country, year=2015, cpi_value=101.5)

        assert row.cpi_value == pytest.approx(101.5)

    def test_income_index_upsert_updates_value(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")

        upsert_income_index(session, country=country, year=2015, index_value=100.0)
        row = upsert_income_index(session, country=country, year=2015, index_value=103.0)

        assert row.index_value == pytest.approx(103.0)


class TestComputedMetricsUpsert:
    def test_annual_metric_upsert_overwrites_previous_run(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
        city = get_or_create_city(session, name="Paris", country=country)

        upsert_annual_metric(session, city=city, year=2016, yoy_growth_pct=5.0)
        row = upsert_annual_metric(session, city=city, year=2016, yoy_growth_pct=6.5)

        assert row.yoy_growth_pct == pytest.approx(6.5)
        assert session.scalars(select(AnnualMetric)).all() == [row]

    def test_summary_metric_upsert_is_one_row_per_city(self, session):
        country = get_or_create_country(session, name="France", iso_code="FR", currency_code="EUR")
        city = get_or_create_city(session, name="Paris", country=country)

        upsert_summary_metric(session, city=city, start_year=2015, end_year=2024, cagr_pct=4.0)
        row = upsert_summary_metric(
            session, city=city, start_year=2015, end_year=2024, cagr_pct=4.8
        )

        assert row.cagr_pct == pytest.approx(4.8)
        assert session.scalars(select(SummaryMetric)).all() == [row]


class TestSeed:
    def test_seed_populates_countries_and_cities(self, session, monkeypatch):
        import src.database.seed as seed_module

        @contextmanager
        def fake_get_session():
            yield session

        monkeypatch.setattr(seed_module, "init_db", lambda: None)
        monkeypatch.setattr(seed_module, "get_session", fake_get_session)

        seed_module.seed_countries_and_cities()

        assert len(session.scalars(select(Country)).all()) == len({p.country for p in PLACES})
        assert len(list_cities(session)) == len(PLACES)

    def test_seed_is_idempotent(self, session, monkeypatch):
        import src.database.seed as seed_module

        @contextmanager
        def fake_get_session():
            yield session

        monkeypatch.setattr(seed_module, "init_db", lambda: None)
        monkeypatch.setattr(seed_module, "get_session", fake_get_session)

        seed_module.seed_countries_and_cities()
        seed_module.seed_countries_and_cities()

        assert len(list_cities(session)) == len(PLACES)

    def test_seed_resolves_palma_mallorca_parent_link(self, session, monkeypatch):
        import src.database.seed as seed_module
        from src.database.repository import get_city_by_name

        @contextmanager
        def fake_get_session():
            yield session

        monkeypatch.setattr(seed_module, "init_db", lambda: None)
        monkeypatch.setattr(seed_module, "get_session", fake_get_session)

        seed_module.seed_countries_and_cities()

        palma = get_city_by_name(session, "Palma")
        mallorca = get_city_by_name(session, "Mallorca")
        assert palma.parent_id == mallorca.id
        assert mallorca.place_type == "island"
        assert palma.place_type == "city"
