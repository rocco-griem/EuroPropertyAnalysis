"""Seed the `countries` and `cities` tables from `settings.PLACES`.

Run directly: `python -m src.database.seed`
"""

from __future__ import annotations

from src.config.settings import PLACES
from src.database.connection import get_session, init_db
from src.database.repository import (
    get_city_by_name,
    get_or_create_city,
    get_or_create_country,
    set_city_parent,
)


def seed_countries_and_cities() -> None:
    init_db()
    with get_session() as session:
        for place in PLACES:
            country = get_or_create_country(
                session,
                name=place.country,
                iso_code=place.iso_code,
                currency_code=place.currency_code,
            )
            get_or_create_city(
                session,
                name=place.city,
                country=country,
                place_type=place.place_type,
                data_quality_note=place.data_quality_note,
            )

        # Second pass: resolve parent links by name, since a parent (e.g. "Mallorca") may be
        # defined later in PLACES than its child ("Palma") and every place must exist first.
        for place in PLACES:
            if place.parent is None:
                continue
            city = get_city_by_name(session, place.city)
            parent = get_city_by_name(session, place.parent)
            if parent is None:
                raise ValueError(
                    f"{place.city!r} declares parent {place.parent!r}, which is not in PLACES."
                )
            set_city_parent(session, city=city, parent=parent)


if __name__ == "__main__":
    seed_countries_and_cities()
