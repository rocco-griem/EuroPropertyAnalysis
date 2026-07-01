"""Tests for src.metrics.risk."""

import pytest

from src.metrics.risk import risk_adjusted_return, volatility


class TestVolatility:
    def test_known_spread(self):
        # Sample stdev of [0.0, 0.10, 0.20]: mean 0.10, sum of squared deviations 0.02,
        # divided by (n-1)=2 gives 0.01, square root 0.10.
        assert volatility([0.0, 0.10, 0.20]) == pytest.approx(0.10)

    def test_constant_growth_is_zero(self):
        assert volatility([0.05, 0.05, 0.05]) == pytest.approx(0.0)

    def test_requires_two_points(self):
        with pytest.raises(ValueError):
            volatility([0.05])


class TestRiskAdjustedReturn:
    def test_ratio(self):
        assert risk_adjusted_return(0.10, 0.05) == pytest.approx(2.0)

    def test_negative_cagr(self):
        assert risk_adjusted_return(-0.06, 0.03) == pytest.approx(-2.0)

    def test_zero_volatility_raises(self):
        with pytest.raises(ValueError):
            risk_adjusted_return(0.10, 0.0)
