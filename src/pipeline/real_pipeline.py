"""End-to-end real-data pipeline: committed CSVs in `data/raw/` -> database -> computed metrics.

Replaces `mock_pipeline` now that real series have been sourced (see `docs/data_sources.md`).
Run directly: `python -m src.pipeline.real_pipeline`
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.config.settings import CAPITALS
from src.database.connection import get_session
from src.database.repository import (
    get_city_by_name,
    get_or_create_data_source,
    upsert_income_index,
    upsert_inflation_index,
    upsert_property_index,
)
from src.database.seed import seed_countries_and_cities
from src.pipeline.compute_metrics import compute_city_metrics
from src.pipeline.csv_loader import (
    load_city_property_index,
    load_national_income_index,
    load_national_inflation_index,
    load_national_property_index,
)

# One citation per raw file rather than per country/city — the full per-country/per-city source
# breakdown (Eurostat vs. ONS, INSEE vs. CBS vs. Tinsa, ...) lives in docs/data_sources.md.
_NATIONAL_PROPERTY_SOURCE = dict(
    name="National House Price Index",
    description=(
        "Eurostat prc_hpi_a (9 countries) + ONS/HM Land Registry UK HPI (UK). "
        "See docs/data_sources.md for the full per-country breakdown."
    ),
)
_NATIONAL_INFLATION_SOURCE = dict(
    name="National CPI",
    description=(
        "Eurostat prc_hicp_aind (9 countries) + ONS CPI series D7BT (UK). "
        "See docs/data_sources.md for the full per-country breakdown."
    ),
)
_NATIONAL_INCOME_SOURCE = dict(
    name="National average annual wages",
    description=(
        "OECD 'Average annual wages' (AV_AN_WAGE), national currency, current prices, all 10 "
        "countries. See docs/data_sources.md."
    ),
)
_CITY_PROPERTY_SOURCE = dict(
    name="City-level House Price Index",
    description=(
        "One source per city (Land Registry, INSEE, CBS, OeNB, MNB, NBP, vdp Research, CSU, "
        "Tinsa) — see docs/data_sources.md for the full per-city breakdown, including the Madrid "
        "methodology caveat recorded on City.data_quality_note."
    ),
)


def load_real_raw_data(session: Session) -> None:
    """Insert the real property/inflation/income series for every capital in `settings.CAPITALS`.

    Cities must already exist (via `seed_countries_and_cities`).
    """
    national_property = load_national_property_index()
    national_inflation = load_national_inflation_index()
    national_income = load_national_income_index()
    city_property = load_city_property_index()

    property_source = get_or_create_data_source(session, **_NATIONAL_PROPERTY_SOURCE)
    inflation_source = get_or_create_data_source(session, **_NATIONAL_INFLATION_SOURCE)
    income_source = get_or_create_data_source(session, **_NATIONAL_INCOME_SOURCE)
    city_source = get_or_create_data_source(session, **_CITY_PROPERTY_SOURCE)

    for capital in CAPITALS:
        city = get_city_by_name(session, capital.city)
        if city is None:
            raise ValueError(f"City {capital.city!r} not seeded — run seed_countries_and_cities() first.")
        country = city.country

        for year, value in national_property[capital.country].items():
            upsert_property_index(session, country=country, year=year, index_value=value, source=property_source)
        for year, value in city_property[capital.city].items():
            upsert_property_index(
                session, country=country, city=city, year=year, index_value=value, source=city_source
            )
        for year, value in national_inflation[capital.country].items():
            upsert_inflation_index(session, country=country, year=year, cpi_value=value, source=inflation_source)
        for year, value in national_income[capital.country].items():
            upsert_income_index(session, country=country, year=year, index_value=value, source=income_source)


def run_real_pipeline() -> None:
    """Seed reference data, load the real raw series, and compute metrics for every capital."""
    seed_countries_and_cities()
    with get_session() as session:
        load_real_raw_data(session)
        for capital in CAPITALS:
            city = get_city_by_name(session, capital.city)
            compute_city_metrics(session, city)


if __name__ == "__main__":
    run_real_pipeline()
