"""Tests for the Overview page's two satellite-imagery hero visuals (flat map + 3D globe).

Doesn't render a browser/WebGL context — just checks that both `render()` functions produce HTML
referencing every place that should get a city light, the expected static-asset URLs, and that
the underlying imagery files (committed by `src/tools/fetch_map_imagery.py`) actually exist on
disk, since a missing file would silently trigger each hero's JS-side fallback.
"""

from __future__ import annotations

import sys
from pathlib import Path

# hero_map / hero_globe do `from components import hero_assets, theme`, which assumes
# `dashboard/` is on sys.path — the same convention dashboard/app.py itself relies on.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dashboard"))

from components import hero_assets, hero_globe, hero_map  # noqa: E402

from src.config import settings  # noqa: E402

_STATIC_DIR = Path(__file__).resolve().parents[1] / "dashboard" / "static"

_EXPECTED_CITY_NAMES = [
    p.city
    for p in settings.PLACES
    if p.place_type in ("capital", "city") and p.lat is not None and p.lon is not None
]


def test_expected_imagery_files_exist():
    for filename in (
        hero_assets.EARTH_DAY,
        hero_assets.EARTH_NIGHT,
        hero_assets.EUROPE_DAY,
        hero_assets.EUROPE_NIGHT,
    ):
        path = _STATIC_DIR / filename
        assert path.is_file(), f"{path} missing — run `python -m src.tools.fetch_map_imagery`"
        assert path.stat().st_size > 0


def test_flat_hero_references_all_cities_and_assets():
    html = hero_map.render()
    for name in _EXPECTED_CITY_NAMES:
        assert name in html
    assert hero_assets.static_url(hero_assets.EUROPE_DAY) in html
    assert hero_assets.static_url(hero_assets.EUROPE_NIGHT) in html


def test_globe_hero_references_all_cities_and_assets():
    html = hero_globe.render()
    for name in _EXPECTED_CITY_NAMES:
        assert name in html
    assert hero_assets.static_url(hero_assets.EARTH_DAY) in html
    assert hero_assets.static_url(hero_assets.EARTH_NIGHT) in html
