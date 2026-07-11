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
from src.config.settings import CAPITALS
from src.database.models import AnnualMetric, Base, SummaryMetric
from src.database.repository import get_city_by_name


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
    def test_computes_a_summary_for_every_capital(self, ran_pipeline):
        summaries = ran_pipeline.scalars(select(SummaryMetric)).all()

        assert len(summaries) == len(CAPITALS)

    def test_every_city_covers_the_full_committed_period(self, ran_pipeline):
        for capital in CAPITALS:
            city = get_city_by_name(ran_pipeline, capital.city)
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
        assert len(summaries) == len(CAPITALS)
