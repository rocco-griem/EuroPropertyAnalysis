"""Seed the `countries` and `cities` tables from `settings.CAPITALS`.

Run directly: `python -m src.database.seed`
"""

from __future__ import annotations

from src.config.settings import CAPITALS
from src.database.connection import get_session, init_db
from src.database.repository import get_or_create_city, get_or_create_country


def seed_countries_and_cities() -> None:
    init_db()
    with get_session() as session:
        for capital in CAPITALS:
            country = get_or_create_country(
                session,
                name=capital.country,
                iso_code=capital.iso_code,
                currency_code=capital.currency_code,
            )
            get_or_create_city(session, name=capital.city, country=country)


if __name__ == "__main__":
    seed_countries_and_cities()
