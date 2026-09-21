"""End-to-end real-data pipeline: committed CSVs in `data/raw/` -> database -> computed metrics.

Replaces `mock_pipeline` now that real series have been sourced (see `docs/data_sources.md`).
Run directly: `python -m src.pipeline.real_pipeline`
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.config.settings import PLACES
from src.database.connection import get_session
from src.database.repository import (
    get_city_by_name,
    get_or_create_data_source,
    upsert_income_index,
    upsert_inflation_index,
    upsert_property_index,
    upsert_property_index_quarterly,
    upsert_rental_price,
)
from src.database.seed import seed_countries_and_cities
from src.pipeline.compute_metrics import compute_city_metrics
from src.pipeline.csv_loader import (
    load_city_property_index,
    load_city_property_index_quarterly,
    load_city_rental_per_sqm,
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
_CITY_RENTAL_SOURCE = dict(
    name="Deloitte Property Index — Average Monthly Rent (EUR/m²)",
    url="https://www.deloitte.com/cz-sk/en/Industries/real-estate/research/property-index-archive.html",
    description=(
        "Average monthly residential rent in EUR/m² read from the rent chart in each annual "
        "Deloitte Property Index (editions 2017–2025, covering rent years 2016–2024). London is "
        "the mean of the inner/outer figures where both are published. Deloitte's rent "
        "methodology and labels vary across editions (average vs. asking rent), so the series is "
        "indicative — see docs/data_sources.md."
    ),
)
_CITY_PROPERTY_QUARTERLY_SOURCE = dict(
    name="Tinsa IMIE Local Markets — quarterly EUR/m²",
    url="https://www.tinsa.es/precio-vivienda/",
    description=(
        "Quarterly average appraised value (EUR/m²), 2001 Q1–present, read from Tinsa's public "
        "price-history chart (same private, appraisal-based series as the annual Madrid/Palma "
        "figures). Covers Palma de Mallorca (municipality) and Mallorca (proxied by Tinsa's "
        "'Islas Baleares' province figure — no official series exists at the Mallorca-island "
        "level; see docs/data_sources.md). The 2015–2024 annual rows in "
        "city_property_index.csv are the mean of each year's 4 quarters from this same source."
    ),
)


def load_real_raw_data(session: Session) -> None:
    """Insert the real property/inflation/income series for every place in `settings.PLACES`.

    Cities must already exist (via `seed_countries_and_cities`).
    """
    national_property = load_national_property_index()
    national_inflation = load_national_inflation_index()
    national_income = load_national_income_index()
    city_property = load_city_property_index()
    city_rental = load_city_rental_per_sqm()
    city_property_quarterly = load_city_property_index_quarterly()

    property_source = get_or_create_data_source(session, **_NATIONAL_PROPERTY_SOURCE)
    inflation_source = get_or_create_data_source(session, **_NATIONAL_INFLATION_SOURCE)
    income_source = get_or_create_data_source(session, **_NATIONAL_INCOME_SOURCE)
    city_source = get_or_create_data_source(session, **_CITY_PROPERTY_SOURCE)
    rental_source = get_or_create_data_source(session, **_CITY_RENTAL_SOURCE)
    quarterly_source = get_or_create_data_source(session, **_CITY_PROPERTY_QUARTERLY_SOURCE)

    for place in PLACES:
        city = get_city_by_name(session, place.city)
        if city is None:
            raise ValueError(
                f"City {place.city!r} not seeded — run seed_countries_and_cities() first."
            )
        country = city.country

        for year, value in national_property[place.country].items():
            upsert_property_index(
                session, country=country, year=year, index_value=value, source=property_source
            )
        for year, value in city_property[place.city].items():
            upsert_property_index(
                session,
                country=country,
                city=city,
                year=year,
                index_value=value,
                source=city_source,
            )
        for year, value in national_inflation[place.country].items():
            upsert_inflation_index(
                session, country=country, year=year, cpi_value=value, source=inflation_source
            )
        for year, value in national_income[place.country].items():
            upsert_income_index(
                session, country=country, year=year, index_value=value, source=income_source
            )
        for year, value in city_rental.get(place.city, {}).items():
            upsert_rental_price(
                session,
                country=country,
                city=city,
                year=year,
                rental_eur_sqm=value,
                source=rental_source,
            )
        for (year, quarter), value in city_property_quarterly.get(place.city, {}).items():
            upsert_property_index_quarterly(
                session,
                country=country,
                city=city,
                year=year,
                quarter=quarter,
                eur_per_sqm=value,
                source=quarterly_source,
            )


def run_real_pipeline() -> None:
    """Seed reference data, load the real raw series, and compute metrics for every place."""
    seed_countries_and_cities()
    with get_session() as session:
        load_real_raw_data(session)
        for place in PLACES:
            city = get_city_by_name(session, place.city)
            compute_city_metrics(session, city)


if __name__ == "__main__":
    run_real_pipeline()
