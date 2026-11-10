"""Database schema.

  regions                 one row per county or county subdivision (Census GEOID)
  demographics            population by race, per region and year
  housing_prices          annual county housing values (Zillow ZHVI and ZORI, FHFA index)
  housing_prices_monthly  monthly county Zillow values
"""

from __future__ import annotations

import enum

from sqlalchemy import CheckConstraint, Double, Enum, ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RegionLevel(str, enum.Enum):
    county = "county"
    subdivision = "subdivision"


class Region(Base):
    __tablename__ = "regions"

    # 5 digits for a county (06001), 10 for a county subdivision (0600190020)
    geoid: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    level: Mapped[RegionLevel] = mapped_column(Enum(RegionLevel, name="region_level"))
    county_geoid: Mapped[str | None] = mapped_column(
        String(10), ForeignKey("regions.geoid", ondelete="CASCADE"), index=True
    )

    county: Mapped[Region | None] = relationship(remote_side=[geoid], back_populates="subdivisions")
    subdivisions: Mapped[list[Region]] = relationship(back_populates="county")

    __table_args__ = (
        CheckConstraint(
            "(level = 'county' AND county_geoid IS NULL AND length(geoid) = 5)"
            " OR (level = 'subdivision' AND county_geoid IS NOT NULL AND length(geoid) = 10)",
            name="level_matches_geoid",
        ),
    )

    def __repr__(self) -> str:
        return f"<Region {self.geoid} {self.name!r} ({self.level.value})>"


class Demographics(Base):
    """One source per region and year. An ACS 5-year span is stored under its end year."""

    __tablename__ = "demographics"

    geoid: Mapped[str] = mapped_column(
        String(10), ForeignKey("regions.geoid", ondelete="CASCADE"), primary_key=True
    )
    year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    source: Mapped[str] = mapped_column(String(32))  # census2000, acs1, acs5, acs5_ccd_sum, …
    period_label: Mapped[str] = mapped_column(String(16))  # 2000, 2012, 2005-2009, …
    total_population: Mapped[int] = mapped_column(Integer)
    white: Mapped[int] = mapped_column(Integer)
    black: Mapped[int] = mapped_column(Integer)
    native_american: Mapped[int] = mapped_column(Integer)
    asian: Mapped[int] = mapped_column(Integer)
    pacific_islander: Mapped[int] = mapped_column(Integer)
    other_race: Mapped[int] = mapped_column(Integer)
    two_or_more: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint("year BETWEEN 1990 AND 2100", name="year_range"),
        Index("ix_demographics_year", "year"),
    )


class HousingPrice(Base):
    """Annual county values. Means use the months available; *_months_observed says how many."""

    __tablename__ = "housing_prices"

    geoid: Mapped[str] = mapped_column(
        String(10), ForeignKey("regions.geoid", ondelete="CASCADE"), primary_key=True
    )
    year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    zillow_region_id: Mapped[int | None] = mapped_column(Integer)
    zhvi_usd: Mapped[float | None] = mapped_column(Double)
    zhvi_months_observed: Mapped[int | None] = mapped_column(SmallInteger)
    zori_usd: Mapped[float | None] = mapped_column(Double)  # USD per month
    zori_months_observed: Mapped[int | None] = mapped_column(SmallInteger)
    fhfa_annual_change_pct: Mapped[float | None] = mapped_column(Double)
    fhfa_hpi_native: Mapped[float | None] = mapped_column(Double)
    fhfa_hpi_1990_base: Mapped[float | None] = mapped_column(Double)
    fhfa_hpi_2000_base: Mapped[float | None] = mapped_column(Double)

    __table_args__ = (
        CheckConstraint("length(geoid) = 5", name="county_only"),
        CheckConstraint("year BETWEEN 1990 AND 2100", name="year_range"),
        Index("ix_housing_prices_year", "year"),
    )


class HousingPriceMonthly(Base):
    __tablename__ = "housing_prices_monthly"

    geoid: Mapped[str] = mapped_column(
        String(10), ForeignKey("regions.geoid", ondelete="CASCADE"), primary_key=True
    )
    year: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    month: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    zhvi_usd: Mapped[float | None] = mapped_column(Double)
    zori_usd: Mapped[float | None] = mapped_column(Double)  # USD per month

    __table_args__ = (
        CheckConstraint("length(geoid) = 5", name="county_only"),
        CheckConstraint("year BETWEEN 1990 AND 2100", name="year_range"),
        CheckConstraint("month BETWEEN 1 AND 12", name="month_range"),
    )
