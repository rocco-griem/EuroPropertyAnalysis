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
# Cities & countries
# --------------------------------------------------------------------------------------
@dataclass(frozen=True)
class CapitalCity:
    """A target capital city and the country whose national market benchmarks it."""

    city: str
    country: str
    iso_code: str       # ISO 3166-1 alpha-2 (matches Eurostat geo codes; UK uses "UK")
    currency_code: str  # ISO 4217
    # Approximate city-centre coordinates (WGS84), used only to place the city on the Overview
    # map. `None` for a city without coordinates (it's then simply omitted from the map).
    lat: float | None = None
    lon: float | None = None
    # Set only when this city's property index source is a methodological outlier versus the
    # rest of the set (e.g. a private/appraisal-based series rather than an official
    # transaction statistic) — see docs/data_sources.md for the full per-city research.
    data_quality_note: str | None = None


# The Version 1 target capitals. Data-discovery milestone (see docs/data_sources.md) confirmed
# a credible, fetchable city-level property source for 9 of the original 10 — Madrid's source is
# flagged as a methodology asymmetry (private/appraisal-based). Lisbon was dropped: its municipal
# series is fragmented across incompatible methodology vintages with no clean 2015-2024 coverage.
CAPITALS: tuple[CapitalCity, ...] = (
    CapitalCity("London", "United Kingdom", "UK", "GBP", lat=51.5074, lon=-0.1278),
    CapitalCity("Paris", "France", "FR", "EUR", lat=48.8566, lon=2.3522),
    CapitalCity("Berlin", "Germany", "DE", "EUR", lat=52.5200, lon=13.4050),
    CapitalCity(
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
    CapitalCity("Amsterdam", "Netherlands", "NL", "EUR", lat=52.3676, lon=4.9041),
    CapitalCity("Vienna", "Austria", "AT", "EUR", lat=48.2082, lon=16.3738),
    CapitalCity("Warsaw", "Poland", "PL", "PLN", lat=52.2297, lon=21.0122),
    CapitalCity("Prague", "Czechia", "CZ", "CZK", lat=50.0755, lon=14.4378),
    CapitalCity("Budapest", "Hungary", "HU", "HUF", lat=47.4979, lon=19.0402),
)
