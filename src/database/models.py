"""SQLAlchemy ORM models for the EuroPropertyAnalysis database.

Eight tables in three layers:
- Reference data: `Country`, `City`, `DataSource`.
- Raw sourced series, one row per scope per year, as published:
  `PropertyIndex`, `InflationIndex`, `IncomeIndex`.
- Computed results, produced by the pipeline from the raw series using the pure
  functions in `src.metrics` / `src.transformation`: `AnnualMetric`, `SummaryMetric`.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Country(Base):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    iso_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)

    cities: Mapped[list["City"]] = relationship(back_populates="country")

    def __repr__(self) -> str:
        return f"Country(id={self.id}, name={self.name!r}, iso_code={self.iso_code!r})"


class City(Base):
    __tablename__ = "cities"
    __table_args__ = (UniqueConstraint("name", "country_id", name="uq_city_name_country"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)
    # Set only for cities whose property index source is a methodological outlier (e.g. private/
    # appraisal-based rather than an official transaction statistic) — surfaced in the dashboard
    # so the caveat travels with the data instead of living only in docs/data_sources.md.
    data_quality_note: Mapped[str | None] = mapped_column(Text)

    country: Mapped["Country"] = relationship(back_populates="cities")

    def __repr__(self) -> str:
        return f"City(id={self.id}, name={self.name!r}, country_id={self.country_id})"


class DataSource(Base):
    """A citation for a raw series: where it came from, so the dashboard can credit it."""

    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    series_type: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)
    access_date: Mapped[dt.date | None] = mapped_column(Date)

    def __repr__(self) -> str:
        return f"DataSource(id={self.id}, name={self.name!r})"


class PropertyIndex(Base):
    """A raw property price index value for one year, as published by a source.

    `city_id` is NULL for a country's *national* index (used for the capital-vs-national
    comparison); a non-NULL `city_id` is that country's city-level index. SQLite treats each
    NULL as distinct, so the unique constraint below can't stop two national rows for the same
    country/year — `repository.upsert_property_index` guards that case in application code.
    """

    __tablename__ = "property_indices"
    __table_args__ = (
        UniqueConstraint("country_id", "city_id", "year", name="uq_property_index_scope_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    index_value: Mapped[float] = mapped_column(Float, nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.id"))

    country: Mapped["Country"] = relationship()
    city: Mapped["City | None"] = relationship()
    source: Mapped["DataSource | None"] = relationship()

    def __repr__(self) -> str:
        return f"PropertyIndex(country_id={self.country_id}, city_id={self.city_id}, year={self.year})"


class RentalPrice(Base):
    """A raw average residential rent for one city-year, in EUR per square metre per month.

    Stored as an absolute level (not rebased) because it's a real €/m² figure, unlike the
    property/CPI/income series which are indices. National scope isn't used here — rent is
    city-level only — but `country_id` is kept for symmetry with `PropertyIndex` and joins.
    """

    __tablename__ = "rental_prices"
    __table_args__ = (
        UniqueConstraint("city_id", "year", name="uq_rental_price_city_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    rental_eur_sqm: Mapped[float] = mapped_column(Float, nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.id"))

    country: Mapped["Country"] = relationship()
    city: Mapped["City"] = relationship()
    source: Mapped["DataSource | None"] = relationship()

    def __repr__(self) -> str:
        return f"RentalPrice(city_id={self.city_id}, year={self.year})"


class InflationIndex(Base):
    """Country-level CPI value for one year, used to compute inflation-adjusted values."""

    __tablename__ = "inflation_indices"
    __table_args__ = (UniqueConstraint("country_id", "year", name="uq_inflation_country_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    cpi_value: Mapped[float] = mapped_column(Float, nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.id"))

    country: Mapped["Country"] = relationship()
    source: Mapped["DataSource | None"] = relationship()

    def __repr__(self) -> str:
        return f"InflationIndex(country_id={self.country_id}, year={self.year})"


class IncomeIndex(Base):
    """Country-level income index value for one year (Version 1: income is country-level only)."""

    __tablename__ = "income_indices"
    __table_args__ = (UniqueConstraint("country_id", "year", name="uq_income_country_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    index_value: Mapped[float] = mapped_column(Float, nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.id"))

    country: Mapped["Country"] = relationship()
    source: Mapped["DataSource | None"] = relationship()

    def __repr__(self) -> str:
        return f"IncomeIndex(country_id={self.country_id}, year={self.year})"


class AnnualMetric(Base):
    """Computed year-by-year metrics for a city, derived from the raw series by the pipeline.

    Growth-based fields are cumulative *since the start year* (not year-on-year), which is what
    the dashboard's time series charts plot directly.
    """

    __tablename__ = "annual_metrics"
    __table_args__ = (UniqueConstraint("city_id", "year", name="uq_annual_metric_city_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    property_index_nominal: Mapped[float | None] = mapped_column(Float)
    property_index_real: Mapped[float | None] = mapped_column(Float)
    yoy_growth_pct: Mapped[float | None] = mapped_column(Float)
    affordability_pressure_pct: Mapped[float | None] = mapped_column(Float)
    capital_vs_national_gap_pct: Mapped[float | None] = mapped_column(Float)
    # Average residential rent, EUR/m²/month (absolute level, not an index). Null for years
    # with no sourced rent figure — rental coverage can differ from the property-index years.
    rental_per_sqm: Mapped[float | None] = mapped_column(Float)

    city: Mapped["City"] = relationship()

    def __repr__(self) -> str:
        return f"AnnualMetric(city_id={self.city_id}, year={self.year})"


class SummaryMetric(Base):
    """One row per city: whole-period aggregate metrics for the comparison leaderboard."""

    __tablename__ = "summary_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"), unique=True, nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_growth_pct: Mapped[float | None] = mapped_column(Float)
    cagr_pct: Mapped[float | None] = mapped_column(Float)
    volatility_pct: Mapped[float | None] = mapped_column(Float)
    risk_adjusted_return: Mapped[float | None] = mapped_column(Float)
    avg_affordability_pressure_pct: Mapped[float | None] = mapped_column(Float)
    capital_vs_national_gap_pct: Mapped[float | None] = mapped_column(Float)
    # Rent (EUR/m²/month) in the latest year with data, and its whole-period CAGR (%). Null when
    # the city has no rental series or too few rental years to compute a growth rate.
    latest_rental_per_sqm: Mapped[float | None] = mapped_column(Float)
    rental_cagr_pct: Mapped[float | None] = mapped_column(Float)
    computed_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc)
    )

    city: Mapped["City"] = relationship()

    def __repr__(self) -> str:
        return f"SummaryMetric(city_id={self.city_id})"
