"""Load the committed raw series CSVs from `data/raw/` into plain in-memory series.

Pure I/O + parsing — no database access, no business logic. Each loader returns
`dict[str, dict[int, float]]`, keyed by entity name (country or city) then year, which is
exactly the shape `real_pipeline` needs to feed into the repository's upsert functions.
"""

from __future__ import annotations

import csv
from pathlib import Path

from src.config.settings import RAW_DIR


def _load_long_csv(path: Path, *, key_col: str, value_col: str) -> dict[str, dict[int, float]]:
    series: dict[str, dict[int, float]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            series.setdefault(row[key_col], {})[int(row["year"])] = float(row[value_col])
    return series


def load_national_property_index() -> dict[str, dict[int, float]]:
    """Country -> {year: index_value}, from `national_property_index.csv`."""
    return _load_long_csv(RAW_DIR / "national_property_index.csv", key_col="country", value_col="index_value")


def load_national_inflation_index() -> dict[str, dict[int, float]]:
    """Country -> {year: cpi_value}, from `national_inflation_index.csv`."""
    return _load_long_csv(RAW_DIR / "national_inflation_index.csv", key_col="country", value_col="cpi_value")


def load_national_income_index() -> dict[str, dict[int, float]]:
    """Country -> {year: index_value}, from `national_income_index.csv`."""
    return _load_long_csv(RAW_DIR / "national_income_index.csv", key_col="country", value_col="index_value")


def load_city_property_index() -> dict[str, dict[int, float]]:
    """City -> {year: index_value}, from `city_property_index.csv`."""
    return _load_long_csv(RAW_DIR / "city_property_index.csv", key_col="city", value_col="index_value")
