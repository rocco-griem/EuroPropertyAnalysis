"""Tests for src.metrics.returns."""

import pytest

from src.metrics.returns import annual_growth_rates, cagr, total_growth


class TestTotalGrowth:
    def test_simple_gain(self):
        assert total_growth(100, 150) == pytest.approx(0.50)

    def test_loss(self):
        assert total_growth(200, 150) == pytest.approx(-0.25)

    def test_no_change(self):
        assert total_growth(100, 100) == pytest.approx(0.0)

    def test_zero_start_raises(self):
        with pytest.raises(ValueError):
            total_growth(0, 100)


class TestCagr:
    def test_ten_percent_over_two_years(self):
        # 100 grows to 121 over two years -> 10% compounded annually.
        assert cagr(100, 121, 2) == pytest.approx(0.10)

    def test_single_period_equals_total_growth(self):
        assert cagr(100, 150, 1) == pytest.approx(0.50)

    def test_decline(self):
        assert cagr(100, 81, 2) == pytest.approx(-0.10)

    def test_non_positive_start_raises(self):
        with pytest.raises(ValueError):
            cagr(0, 100, 5)

    def test_non_positive_periods_raises(self):
        with pytest.raises(ValueError):
            cagr(100, 150, 0)


class TestAnnualGrowthRates:
    def test_constant_growth(self):
        assert annual_growth_rates([100, 110, 121]) == pytest.approx([0.10, 0.10])

    def test_mixed_growth(self):
        assert annual_growth_rates([100, 120, 90]) == pytest.approx([0.20, -0.25])

    def test_single_value_returns_empty(self):
        assert annual_growth_rates([100]) == []

    def test_empty_returns_empty(self):
        assert annual_growth_rates([]) == []

    def test_zero_base_raises(self):
        with pytest.raises(ValueError):
            annual_growth_rates([0, 100])
