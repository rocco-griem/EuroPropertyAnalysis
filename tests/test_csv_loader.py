"""Tests for src.pipeline.csv_loader against the actual committed data/raw/*.csv files.

Deliberately reads the real files rather than fixtures — this is the contract check that the
committed CSVs still have exactly the shape the pipeline expects.
"""

from __future__ import annotations

from src.config.settings import CAPITALS
from src.pipeline.csv_loader import (
    load_city_property_index,
    load_city_rental_per_sqm,
    load_national_income_index,
    load_national_inflation_index,
    load_national_property_index,
)

_EXPECTED_YEARS = list(range(2015, 2025))
# Rent coverage starts in 2016 — Deloitte's rent comparison chart began with the 2017 edition.
_EXPECTED_RENTAL_YEARS = list(range(2016, 2025))


class TestLoadNationalSeries:
    def test_covers_every_capital_country(self):
        series = load_national_property_index()

        for capital in CAPITALS:
            assert capital.country in series

    def test_every_country_has_a_complete_contiguous_series(self):
        for loader in (
            load_national_property_index,
            load_national_inflation_index,
            load_national_income_index,
        ):
            series = loader()
            for country, values in series.items():
                assert sorted(values) == _EXPECTED_YEARS, f"{country} missing years in {loader.__name__}"

    def test_values_are_positive(self):
        series = load_national_property_index()

        for values in series.values():
            for value in values.values():
                assert value > 0


class TestLoadCityPropertyIndex:
    def test_covers_every_capital_city(self):
        series = load_city_property_index()

        for capital in CAPITALS:
            assert capital.city in series

    def test_every_city_has_a_complete_contiguous_series(self):
        series = load_city_property_index()

        for city, values in series.items():
            assert sorted(values) == _EXPECTED_YEARS, f"{city} missing years"

    def test_values_are_positive(self):
        series = load_city_property_index()

        for values in series.values():
            for value in values.values():
                assert value > 0


class TestLoadCityRentalPerSqm:
    def test_covers_every_capital_city(self):
        series = load_city_rental_per_sqm()

        for capital in CAPITALS:
            assert capital.city in series

    def test_every_city_has_the_full_rental_period(self):
        series = load_city_rental_per_sqm()

        for city, values in series.items():
            assert sorted(values) == _EXPECTED_RENTAL_YEARS, f"{city} missing rental years"

    def test_values_are_positive(self):
        series = load_city_rental_per_sqm()

        for values in series.values():
            for value in values.values():
                assert value > 0
