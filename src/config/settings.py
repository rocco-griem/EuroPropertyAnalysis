"""Central configuration: filesystem paths, database URL, and the city/country definitions.

This module is the single source of truth for *where things live* and *which places we analyse*.
Keeping it free of business logic means every other module (pipeline, database seed, dashboard)
can import these values without circular dependencies.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load variables from a local `.env` file if present (no-op if the file is absent).
load_dotenv()

# --------------------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------------------
# settings.py lives at <root>/src/config/settings.py, so the project root is two parents up.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
PROCESSED_DIR: Path = DATA_DIR / "processed"
DATABASE_DIR: Path = DATA_DIR / "database"

# --------------------------------------------------------------------------------------
# Database
# --------------------------------------------------------------------------------------
# Default to a local SQLite file; allow override via the DATABASE_URL env var so the data
# layer can later point at PostgreSQL without any code change.
DEFAULT_DB_PATH: Path = DATABASE_DIR / "europropertyanalysis.db"
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# --------------------------------------------------------------------------------------
# Analysis period
# --------------------------------------------------------------------------------------
# Target period is 2015 to TARGET_END_YEAR, falling back to FALLBACK_END_YEAR if 2025 data
# is incomplete. The pipeline derives the actual end year from the data; these are intents.
START_YEAR: int = 2015
TARGET_END_YEAR: int = 2025
FALLBACK_END_YEAR: int = 2024


# --------------------------------------------------------------------------------------
# Places (cities, plus non-capital places of special interest) & countries
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Place:
    """A target place and the country whose national market benchmarks it.

    Named `Place` rather than `CapitalCity` (its name through M8) because the set is no longer
    only national capitals — `place_type` distinguishes the roles.
    """

    city: str
    country: str
    iso_code: str  # ISO 3166-1 alpha-2 (matches Eurostat geo codes; UK uses "UK")
    currency_code: str  # ISO 4217
    # "capital" (national capital, the Version 1 set) | "city" (a non-capital city added later,
    # e.g. Palma) | "island" (a region/island-level place used only for deep-dive comparison,
    # e.g. Mallorca — excluded from the main capitals-and-cities comparison views by default).
    place_type: str = "capital"
    # The containing place, by `city` name (e.g. Palma's parent is "Mallorca"). `None` if this
    # place has no parent in the set. Not a foreign key here — resolved to `City.parent_id` by
    # `seed.py` in a second pass, since parents and children can appear in either order below.
    parent: str | None = None
    # Approximate city-centre coordinates (WGS84), used only to place the city on the Overview
    # map. `None` for a place without coordinates (it's then simply omitted from the map).
    lat: float | None = None
    lon: float | None = None
    # Set only when this place's property index source is a methodological outlier versus the
    # rest of the set (e.g. a private/appraisal-based series rather than an official
    # transaction statistic) — see docs/data_sources.md for the full per-city research.
    data_quality_note: str | None = None


# The Version 1 target capitals. Data-discovery milestone (see docs/data_sources.md) confirmed
# a credible, fetchable city-level property source for 9 of the original 10 — Madrid's source is
# flagged as a methodology asymmetry (private/appraisal-based). Lisbon was dropped: its municipal
# series is fragmented across incompatible methodology vintages with no clean 2015-2024 coverage.
#
# M9 (2026-07-23) added Palma and Mallorca as places of special interest, requested by name: Palma
# joins the main comparison (it is a city, and the Balearic Islands' regional capital, so the
# existing "city vs. national market" framing holds unchanged); Mallorca is the island itself,
# shown only on the dedicated Mallorca deep-dive page (`place_type="island"`).
PLACES: tuple[Place, ...] = (
    Place("London", "United Kingdom", "UK", "GBP", lat=51.5074, lon=-0.1278),
    Place("Paris", "France", "FR", "EUR", lat=48.8566, lon=2.3522),
    Place("Berlin", "Germany", "DE", "EUR", lat=52.5200, lon=13.4050),
    Place(
        "Madrid",
        "Spain",
        "ES",
        "EUR",
        lat=40.4168,
        lon=-3.7038,
        data_quality_note=(
            "Property index sourced from Tinsa IMIE Local Markets, a private, appraisal-based "
            "series — not an official transaction statistic like the other cities here."
        ),
    ),
    Place("Amsterdam", "Netherlands", "NL", "EUR", lat=52.3676, lon=4.9041),
    Place("Vienna", "Austria", "AT", "EUR", lat=48.2082, lon=16.3738),
    Place("Warsaw", "Poland", "PL", "PLN", lat=52.2297, lon=21.0122),
    Place("Prague", "Czechia", "CZ", "CZK", lat=50.0755, lon=14.4378),
    Place("Budapest", "Hungary", "HU", "HUF", lat=47.4979, lon=19.0402),
    Place(
        "Palma",
        "Spain",
        "ES",
        "EUR",
        place_type="city",
        parent="Mallorca",
        lat=39.5696,
        lon=2.6502,
        data_quality_note=(
            "Property index sourced from Tinsa IMIE Local Markets (Palma de Mallorca market), "
            "the same private, appraisal-based series used for Madrid — not an official "
            "transaction statistic like the other cities here."
        ),
    ),
    Place(
        "Mallorca",
        "Spain",
        "ES",
        "EUR",
        place_type="island",
        data_quality_note=(
            "No official price series exists at the Mallorca-island level (Spain's own "
            "statistics stop at the Balearic Islands region, which also includes Menorca and "
            "Ibiza/Formentera). This series is Tinsa IMIE Local Markets' 'Islas Baleares' "
            "province figure, used as the closest available Mallorca proxy — Mallorca accounts "
            "for the large majority of the region's housing stock and population. Private, "
            "appraisal-based, like Madrid and Palma. See docs/data_sources.md."
        ),
    ),
)
