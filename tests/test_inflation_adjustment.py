"""Tests for src.transformation.inflation_adjustment."""

import pytest

from src.transformation.inflation_adjustment import deflate, real_index


class TestDeflate:
    def test_strips_inflation(self):
        # 110 nominal with prices 5% higher than base -> ~104.76 in base-year money.
        assert deflate(110, cpi_value=105, cpi_base=100) == pytest.approx(11000 / 105)

    def test_no_inflation_returns_input(self):
        assert deflate(120, cpi_value=100, cpi_base=100) == pytest.approx(120.0)

    def test_zero_cpi_raises(self):
        with pytest.raises(ValueError):
            deflate(120, cpi_value=0, cpi_base=100)


class TestRealIndex:
    def test_real_series(self):
        result = real_index([100, 110, 120], [100, 105, 110])
        assert result == pytest.approx([100.0, 11000 / 105, 12000 / 110])

    def test_base_period_unchanged(self):
        # When nominal is 100 at the base, real is also 100 at the base.
        result = real_index([100, 110, 120], [100, 105, 110])
        assert result[0] == pytest.approx(100.0)

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            real_index([100, 110], [100])

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            real_index([], [])
