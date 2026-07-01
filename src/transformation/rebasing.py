"""Rebasing index series to a common base of 100.

Different sources publish indices with different base years (e.g. 2010=100 vs 2015=100). To
compare cities fairly we rebase every series so the chosen base period equals 100; growth is
then read directly off the index (110 = +10% since the base).
"""

from __future__ import annotations

from collections.abc import Sequence


def rebase_to_100(values: Sequence[float], base_index: int = 0) -> list[float]:
    """Scale a series so the value at ``base_index`` becomes 100.

    Example: rebase_to_100([200, 220, 240]) -> [100.0, 110.0, 120.0].
    """
    vals = list(values)
    if not vals:
        raise ValueError("Cannot rebase an empty series.")
    if not 0 <= base_index < len(vals):
        raise IndexError("base_index is out of range for the provided series.")
    base_value = vals[base_index]
    if base_value == 0:
        raise ValueError("Cannot rebase when the base value is zero.")
    return [value / base_value * 100 for value in vals]
