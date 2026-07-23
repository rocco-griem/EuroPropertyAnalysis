"""Tests for src.pipeline.real_pipeline: the real CSVs, loaded end-to-end into a database.

Uses an in-memory database and monkeypatches `get_session`/`init_db` on both `real_pipeline` and
`src.database.seed` (the same pattern `test_database.py::TestSeed` uses) so the run never touches
the real project database file.
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import src.database.seed as seed_module
import src.pipeline.real_pipeline as real_pipeline_module
from src.config.settings import PLACES
from src.database.models import AnnualMetric, Base, PropertyIndexQuarterly, SummaryMetric
from src.database.repository import get_city_by_name

# Deloitte doesn't cover Palma/Mallorca yet — see docs/data_sources.md's M9 section.
_PLACES_WITHOUT_RENT = {"Palma", "Mallorca"}
_QUARTERLY_PLACES = {"Palma", "Mallorca"}


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def ran_pipeline(session, monkeypatch):
    @contextmanager
    def fake_get_session():
        yield session

    monkeypatch.setattr(seed_module, "init_db", lambda: None)
    monkeypatch.setattr(seed_module, "get_session", fake_get_session)
    monkeypatch.setattr(real_pipeline_module, "get_session", fake_get_session)

    real_pipeline_module.run_real_pipeline()
    return session


class TestRunRealPipeline:
    def test_computes_a_summary_for_every_place(self, ran_pipeline):
        summaries = ran_pipeline.scalars(select(SummaryMetric)).all()

        assert len(summaries) == len(PLACES)

    def test_every_city_covers_the_full_committed_period(self, ran_pipeline):
        for place in PLACES:
            city = get_city_by_name(ran_pipeline, place.city)
            annual_rows = ran_pipeline.scalars(
                select(AnnualMetric).where(AnnualMetric.city_id == city.id)
            ).all()
            assert {r.year for r in annual_rows} == set(range(2015, 2025))

    def test_madrid_keeps_its_data_quality_note(self, ran_pipeline):
        city = get_city_by_name(ran_pipeline, "Madrid")

        assert city.data_quality_note is not None
        assert "Tinsa" in city.data_quality_note

    def test_rerunning_the_pipeline_is_idempotent(self, ran_pipeline):
        real_pipeline_module.run_real_pipeline()

        summaries = ran_pipeline.scalars(select(SummaryMetric)).all()
        assert len(summaries) == len(PLACES)

    def test_rental_metrics_populate_for_every_place_deloitte_covers(self, ran_pipeline):
        for place in PLACES:
            if place.city in _PLACES_WITHOUT_RENT:
                continue
            city = get_city_by_name(ran_pipeline, place.city)
            summary = ran_pipeline.scalar(
                select(SummaryMetric).where(SummaryMetric.city_id == city.id)
            )
            assert summary.latest_rental_per_sqm is not None and summary.latest_rental_per_sqm > 0
            assert summary.rental_cagr_pct is not None

    def test_palma_and_mallorca_have_no_rent_yet(self, ran_pipeline):
        for city_name in _PLACES_WITHOUT_RENT:
            city = get_city_by_name(ran_pipeline, city_name)
            summary = ran_pipeline.scalar(
                select(SummaryMetric).where(SummaryMetric.city_id == city.id)
            )
            assert summary.latest_rental_per_sqm is None

    def test_rental_starts_in_2016_not_2015(self, ran_pipeline):
        city = get_city_by_name(ran_pipeline, "Berlin")
        rows = ran_pipeline.scalars(
            select(AnnualMetric).where(AnnualMetric.city_id == city.id)
        ).all()
        by_year = {r.year: r.rental_per_sqm for r in rows}
        # Property runs 2015–2024, but rent is only published from 2016.
        assert by_year[2015] is None
        assert all(by_year[y] is not None and by_year[y] > 0 for y in range(2016, 2025))

    def test_palma_is_a_city_and_mallorca_is_an_island(self, ran_pipeline):
        palma = get_city_by_name(ran_pipeline, "Palma")
        mallorca = get_city_by_name(ran_pipeline, "Mallorca")

        assert palma.place_type == "city"
        assert mallorca.place_type == "island"
        assert palma.parent_id == mallorca.id

    def test_quarterly_property_data_loaded_for_palma_and_mallorca(self, ran_pipeline):
        for city_name in _QUARTERLY_PLACES:
            city = get_city_by_name(ran_pipeline, city_name)
            rows = ran_pipeline.scalars(
                select(PropertyIndexQuarterly).where(PropertyIndexQuarterly.city_id == city.id)
            ).all()
            assert len(rows) >= 100  # 2001 Q1 - 2026 Q2 or later
            assert all(r.eur_per_sqm > 0 for r in rows)

    def test_other_cities_have_no_quarterly_data_yet(self, ran_pipeline):
        city = get_city_by_name(ran_pipeline, "Paris")
        rows = ran_pipeline.scalars(
            select(PropertyIndexQuarterly).where(PropertyIndexQuarterly.city_id == city.id)
        ).all()
        assert rows == []
