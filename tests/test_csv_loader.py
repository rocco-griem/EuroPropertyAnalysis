"""Tests for src.pipeline.csv_loader against the actual committed data/raw/*.csv files.

Deliberately reads the real files rather than fixtures — this is the contract check that the
committed CSVs still have exactly the shape the pipeline expects.
"""

from __future__ import annotations

from src.config.settings import PLACES
from src.pipeline.csv_loader import (
    load_city_property_index,
    load_city_property_index_quarterly,
    load_city_rental_per_sqm,
    load_national_income_index,
    load_national_inflation_index,
    load_national_property_index,
)

_EXPECTED_YEARS = list(range(2015, 2025))
# Rent coverage starts in 2016 — Deloitte's rent comparison chart began with the 2017 edition.
_EXPECTED_RENTAL_YEARS = list(range(2016, 2025))
# Deloitte doesn't cover Palma/Mallorca — see docs/data_sources.md's M9 section.
_PLACES_WITHOUT_RENT = {"Palma", "Mallorca"}
_PLACES_WITH_RENT = [p for p in PLACES if p.city not in _PLACES_WITHOUT_RENT]
# Only Palma/Mallorca have quarterly history so far (Tinsa, 2001 Q1–2026 Q2).
_QUARTERLY_PLACES = ["Palma", "Mallorca"]


class TestLoadNationalSeries:
    def test_covers_every_place_country(self):
        series = load_national_property_index()

        for place in PLACES:
            assert place.country in series

    def test_every_country_has_a_complete_contiguous_series(self):
        for loader in (
            load_national_property_index,
            load_national_inflation_index,
            load_national_income_index,
        ):
            series = loader()
            for country, values in series.items():
                assert sorted(values) == _EXPECTED_YEARS, (
                    f"{country} missing years in {loader.__name__}"
                )

    def test_values_are_positive(self):
        series = load_national_property_index()

        for values in series.values():
            for value in values.values():
                assert value > 0


class TestLoadCityPropertyIndex:
    def test_covers_every_place_city(self):
        series = load_city_property_index()

        for place in PLACES:
            assert place.city in series

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
    def test_covers_every_place_with_deloitte_coverage(self):
        series = load_city_rental_per_sqm()

        for place in _PLACES_WITH_RENT:
            assert place.city in series

    def test_palma_and_mallorca_have_no_rent_yet(self):
        # Deloitte doesn't cover either — documented gap, not an oversight (see the Mallorca
        # Deep Dive page and docs/data_sources.md).
        series = load_city_rental_per_sqm()

        for city in _PLACES_WITHOUT_RENT:
            assert city not in series

    def test_every_city_has_the_full_rental_period(self):
        series = load_city_rental_per_sqm()

        for city, values in series.items():
            assert sorted(values) == _EXPECTED_RENTAL_YEARS, f"{city} missing rental years"

    def test_values_are_positive(self):
        series = load_city_rental_per_sqm()

        for values in series.values():
            for value in values.values():
                assert value > 0


class TestLoadCityPropertyIndexQuarterly:
    def test_covers_the_expected_quarterly_places(self):
        series = load_city_property_index_quarterly()

        assert set(series) == set(_QUARTERLY_PLACES)

    def test_each_place_has_every_quarter_2015_through_2024(self):
        series = load_city_property_index_quarterly()

        expected = {(year, q) for year in range(2015, 2025) for q in (1, 2, 3, 4)}
        for city in _QUARTERLY_PLACES:
            assert expected.issubset(series[city].keys()), f"{city} missing quarters in 2015-2024"

    def test_includes_history_back_to_2001(self):
        series = load_city_property_index_quarterly()

        for city in _QUARTERLY_PLACES:
            years = {year for year, _quarter in series[city]}
            assert min(years) <= 2001

    def test_values_are_positive(self):
        series = load_city_property_index_quarterly()

        for values in series.values():
            for value in values.values():
                assert value > 0
