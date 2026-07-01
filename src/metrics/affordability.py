"""Affordability and capital-vs-national comparison metrics.

Both functions are deliberately tiny — the value is in naming the concept clearly and pinning
the definition with a test, so the same formula is used everywhere in the project.
"""

from __future__ import annotations


def affordability_pressure(price_growth: float, income_growth: float) -> float:
    """How much faster property prices grew than incomes, in percentage points.

    Both inputs must be expressed in the SAME unit (both fractions, or both percentages).
    Positive => housing became less affordable (prices outpaced incomes).
    Example: prices +50%, incomes +30% -> 0.50 - 0.30 = 0.20 (20 percentage points).
    """
    return price_growth - income_growth


def capital_vs_national_gap(city_growth: float, national_growth: float) -> float:
    """Capital outperformance vs its national housing market, in percentage points.

    Positive => the capital grew faster than the wider national market.
    Example: city +60%, national +45% -> 0.60 - 0.45 = 0.15.
    """
    return city_growth - national_growth
