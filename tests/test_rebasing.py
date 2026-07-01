"""Tests for src.transformation.rebasing."""

import pytest

from src.transformation.rebasing import rebase_to_100


class TestRebaseTo100:
    def test_basic_rebase(self):
        assert rebase_to_100([200, 220, 240]) == pytest.approx([100.0, 110.0, 120.0])

    def test_already_based_at_100(self):
        assert rebase_to_100([100, 105, 99]) == pytest.approx([100.0, 105.0, 99.0])

    def test_non_zero_base_index(self):
        # Rebase so the middle value becomes 100.
        assert rebase_to_100([90, 100, 120], base_index=1) == pytest.approx([90.0, 100.0, 120.0])

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            rebase_to_100([])

    def test_base_index_out_of_range_raises(self):
        with pytest.raises(IndexError):
            rebase_to_100([100, 110], base_index=5)

    def test_zero_base_value_raises(self):
        with pytest.raises(ValueError):
            rebase_to_100([0, 110, 120])
