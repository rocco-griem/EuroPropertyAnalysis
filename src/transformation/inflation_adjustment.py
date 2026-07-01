"""Convert nominal index values into real (inflation-adjusted) values using a CPI series.

A nominal index mixes two things: real price movement and general inflation. Dividing by the
relative CPI level strips out inflation, leaving growth expressed in constant (base-year) money.
"""

from __future__ import annotations

from collections.abc import Sequence


def deflate(nominal_value: float, cpi_value: float, cpi_base: float) -> float:
    """Deflate a single nominal value to base-year money.

    real = nominal * (cpi_base / cpi_value).
    Example: deflate(110, cpi_value=105, cpi_base=100) -> 104.7619...
    """
    if cpi_value == 0 or cpi_base == 0:
        raise ValueError("CPI values must be non-zero to deflate.")
    return nominal_value * (cpi_base / cpi_value)


def real_index(
    nominal_index: Sequence[float],
    cpi_index: Sequence[float],
    base_index: int = 0,
) -> list[float]:
    """Convert a nominal index series into a real one, in money of the ``base_index`` period.

    If the nominal series is 100 at the base period, the real series is also 100 there, so the
    two are directly comparable and any divergence is pure inflation.
    Example: real_index([100, 110, 120], [100, 105, 110]) -> [100.0, 104.7619..., 109.0909...].
    """
    nominal = list(nominal_index)
    cpi = list(cpi_index)
    if len(nominal) != len(cpi):
        raise ValueError("nominal_index and cpi_index must have the same length.")
    if not nominal:
        raise ValueError("Cannot adjust an empty series.")
    if not 0 <= base_index < len(cpi):
        raise IndexError("base_index is out of range for the provided series.")
    cpi_base = cpi[base_index]
    return [deflate(n, c, cpi_base) for n, c in zip(nominal, cpi)]
