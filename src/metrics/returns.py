"""Growth and return metrics computed from index values.

All functions operate on *index values* (e.g. a price index rebased to 100 at the start year).
Growth figures are returned as fractions: 0.10 means +10%, -0.05 means -5%.
"""

from __future__ import annotations

from collections.abc import Sequence


def total_growth(start_value: float, end_value: float) -> float:
    """Total growth over the whole period as a fraction.

    Example: an index that moves 100 -> 150 has total growth (150 - 100) / 100 = 0.50 (+50%).
    """
    if start_value == 0:
        raise ValueError("start_value must be non-zero to compute total growth.")
    return (end_value - start_value) / start_value


def cagr(start_value: float, end_value: float, periods: int) -> float:
    """Compound Annual Growth Rate as a fraction per year.

    ``periods`` is the number of YEARS between the start and end values. For an annual series
    with N data points the gap is ``N - 1`` periods (e.g. 2015..2025 inclusive is 10 periods).

    Example: 100 -> 121 over 2 periods => (121/100) ** (1/2) - 1 = 0.10 (+10% per year).
    """
    if start_value <= 0:
        raise ValueError("start_value must be positive to compute CAGR.")
    if periods <= 0:
        raise ValueError("periods must be a positive number of years.")
    return (end_value / start_value) ** (1 / periods) - 1


def annual_growth_rates(values: Sequence[float]) -> list[float]:
    """Year-on-year growth rates from a sequence of index values.

    Returns a list with one fewer element than the input (the first year has no prior year).
    Example: [100, 110, 121] -> [0.10, 0.10].
    """
    vals = list(values)
    if len(vals) < 2:
        return []
    rates: list[float] = []
    for previous, current in zip(vals[:-1], vals[1:]):
        if previous == 0:
            raise ValueError("Cannot compute a growth rate from a zero base value.")
        rates.append((current - previous) / previous)
    return rates
