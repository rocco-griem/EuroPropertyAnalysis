"""Tests for src.metrics.affordability."""

import pytest

from src.metrics.affordability import affordability_pressure, capital_vs_national_gap


class TestAffordabilityPressure:
    def test_prices_outpace_incomes(self):
        assert affordability_pressure(0.50, 0.30) == pytest.approx(0.20)

    def test_incomes_outpace_prices(self):
        assert affordability_pressure(0.10, 0.25) == pytest.approx(-0.15)

    def test_equal_growth(self):
        assert affordability_pressure(0.20, 0.20) == pytest.approx(0.0)


class TestCapitalVsNationalGap:
    def test_capital_outperforms(self):
        assert capital_vs_national_gap(0.60, 0.45) == pytest.approx(0.15)

    def test_capital_underperforms(self):
        assert capital_vs_national_gap(0.30, 0.40) == pytest.approx(-0.10)
