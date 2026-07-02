"""End-to-end vertical slice using hand-written mock data — NOT real market data.

Proves the full chain works (raw series in -> computed metrics out) before real data sourcing,
which is a later milestone. Run directly: `python -m src.pipeline.mock_pipeline`
"""

from __future__ import annotations

from sqlalchemy.orm import Session

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

MOCK_CITY_TO_COUNTRY: dict[str, str] = {"Paris": "France", "Madrid": "Spain"}

MOCK_YEARS: list[int] = list(range(2015, 2021))

# Illustrative numbers only, loosely realistic in shape but NOT sourced from any real dataset.
# Real series are wired in at a later milestone; this exists purely to exercise the pipeline.
MOCK_PROPERTY_CITY: dict[str, list[float]] = {
    "Paris": [100, 106, 113, 121, 128, 134],
    "Madrid": [100, 104, 109, 116, 121, 118],
}
MOCK_PROPERTY_NATIONAL: dict[str, list[float]] = {
    "France": [100, 103, 107, 111, 115, 118],
    "Spain": [100, 102, 106, 110, 113, 109],
}
MOCK_CPI: dict[str, list[float]] = {
    "France": [100, 100.2, 101.0, 102.3, 103.4, 103.9],
    "Spain": [100, 99.8, 102.0, 103.5, 104.6, 104.1],
}
MOCK_INCOME: dict[str, list[float]] = {
    "France": [100, 101.5, 103.0, 104.8, 106.5, 107.9],
    "Spain": [100, 101.0, 102.3, 103.9, 105.0, 104.2],
}


def load_mock_raw_data(session: Session) -> None:
    """Insert the mock property/inflation/income series for the demo cities and their countries.

    Cities must already exist (via `seed_countries_and_cities`).
    """
    source = get_or_create_data_source(
        session,
        name="Mock data (M3 placeholder)",
        description="Hand-written, illustrative only — not a real market data source.",
    )
    for city_name, country_name in MOCK_CITY_TO_COUNTRY.items():
        city = get_city_by_name(session, city_name)
        if city is None:
            raise ValueError(f"City {city_name!r} not seeded — run seed_countries_and_cities() first.")
        country = city.country

        for year, value in zip(MOCK_YEARS, MOCK_PROPERTY_CITY[city_name]):
            upsert_property_index(
                session, country=country, city=city, year=year, index_value=value, source=source
            )
        for year, value in zip(MOCK_YEARS, MOCK_PROPERTY_NATIONAL[country_name]):
            upsert_property_index(session, country=country, year=year, index_value=value, source=source)
        for year, value in zip(MOCK_YEARS, MOCK_CPI[country_name]):
            upsert_inflation_index(session, country=country, year=year, cpi_value=value, source=source)
        for year, value in zip(MOCK_YEARS, MOCK_INCOME[country_name]):
            upsert_income_index(session, country=country, year=year, index_value=value, source=source)


def run_mock_pipeline() -> None:
    """Seed reference data, load mock raw series, and compute metrics for the demo cities."""
    seed_countries_and_cities()
    with get_session() as session:
        load_mock_raw_data(session)
        for city_name in MOCK_CITY_TO_COUNTRY:
            city = get_city_by_name(session, city_name)
            compute_city_metrics(session, city)


if __name__ == "__main__":
    run_mock_pipeline()
