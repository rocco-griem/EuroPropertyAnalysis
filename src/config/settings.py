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


# The 10 Version 1 target capitals. Final inclusion still depends on whether credible
# city-level property data exists for each (decided at the data-discovery milestone), but
# all 10 are attempted and documented before any exclusion.
CAPITALS: tuple[CapitalCity, ...] = (
    CapitalCity("London", "United Kingdom", "UK", "GBP"),
    CapitalCity("Paris", "France", "FR", "EUR"),
    CapitalCity("Berlin", "Germany", "DE", "EUR"),
    CapitalCity("Madrid", "Spain", "ES", "EUR"),
    CapitalCity("Lisbon", "Portugal", "PT", "EUR"),
    CapitalCity("Amsterdam", "Netherlands", "NL", "EUR"),
    CapitalCity("Vienna", "Austria", "AT", "EUR"),
    CapitalCity("Warsaw", "Poland", "PL", "PLN"),
    CapitalCity("Prague", "Czechia", "CZ", "CZK"),
    CapitalCity("Budapest", "Hungary", "HU", "HUF"),
)
