"""Shared constants and helpers for the two Overview-page hero visuals (`hero_map`, `hero_globe`).

Both heroes are textured with the same NASA GIBS satellite imagery, fetched once by
`src/tools/fetch_map_imagery.py` into `dashboard/static/` (see that script for the exact WMS
layers/params, and `docs/data_sources.md` for licensing). This module is the single place that
knows the resulting filenames, how to turn them into browser-loadable URLs, the Europe crop's
geographic bounds (must match the fetch script's `EUROPE_LON`/`EUROPE_LAT`), and the capital-city
list shared by both renderers.
"""

from __future__ import annotations

import json

from src.config import settings

# Filenames written by src/tools/fetch_map_imagery.py into dashboard/static/.
EARTH_DAY = "earth_day.webp"
EARTH_NIGHT = "earth_night.webp"
EUROPE_DAY = "europe_day.webp"
EUROPE_NIGHT = "europe_night.webp"

# Must match EUROPE_LON / EUROPE_LAT in src/tools/fetch_map_imagery.py — the geographic bounds of
# the europe_day/europe_night crop, used by hero_map.py to place the image with proj().
EUROPE_LON = (-25.0, 40.0)
EUROPE_LAT = (33.0, 60.0)


def static_url(filename: str) -> str:
    """Relative URL for a file in dashboard/static/, per Streamlit's static-file-serving docs.

    Relative (no leading slash) so it resolves correctly from inside the `components.html`
    srcdoc iframe, both locally and behind a base path on Streamlit Cloud.
    """
    return f"app/static/{filename}"


def cities_json() -> str:
    # Only "capital"/"city" places render as a city light — "island" places (e.g. Mallorca) are
    # excluded even if they gained coordinates later, since the hero is a city map, not a region
    # map. In practice this is redundant with the `lat`/`lon is not None` filter below (Mallorca
    # has neither set), but kept explicit so the intent survives a future data change.
    cities = [
        {"name": p.city, "lat": p.lat, "lon": p.lon}
        for p in settings.PLACES
        if p.place_type in ("capital", "city") and p.lat is not None and p.lon is not None
    ]
    return json.dumps(cities)
