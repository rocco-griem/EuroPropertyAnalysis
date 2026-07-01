"""Risk metrics: volatility of annual growth and a simple risk-adjusted return.

Caveat worth stating in the methodology: with ~10 annual observations these estimates are based
on very few data points and should be read as indicative, not precise.
"""

from __future__ import annotations

from collections.abc import Sequence
from statistics import stdev


def volatility(growth_rates: Sequence[float]) -> float:
    """Sample standard deviation (n-1) of annual growth rates — a measure of variability.

    Needs at least two observations. Identical growth every year gives 0.0.
    Example: [0.0, 0.10, 0.20] -> 0.10.
    """
    rates = list(growth_rates)
    if len(rates) < 2:
        raise ValueError("At least two growth rates are required to compute volatility.")
    return stdev(rates)


def risk_adjusted_return(cagr_value: float, volatility_value: float) -> float:
    """Return per unit of variability: CAGR / volatility (a Sharpe-like ratio, no risk-free rate).

    Higher is better. Undefined when volatility is zero.
    Example: risk_adjusted_return(0.10, 0.05) -> 2.0.
    """
    if volatility_value == 0:
        raise ValueError("risk_adjusted_return is undefined when volatility is zero.")
    return cagr_value / volatility_value
