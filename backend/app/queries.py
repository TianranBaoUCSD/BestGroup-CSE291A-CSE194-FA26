"""SQL for the API. Every query returns county rows only; subdivisions stay in the
database but aren't served for now. Table and column names come from this module
and metrics_config, never from a request.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from .metrics_config import metric_columns

TABLES = {"housing": "housing_prices", "demographics": "demographics"}

IS_COUNTY = "geoid IN (SELECT geoid FROM regions WHERE level = 'county')"


def is_county(db: Session, geoid: str) -> bool:
    sql = "SELECT EXISTS (SELECT 1 FROM regions WHERE geoid = :geoid AND level = 'county')"
    return db.execute(text(sql), {"geoid": geoid}).scalar()


def years_with_data(db: Session) -> list[int]:
    sql = f"""
        SELECT year FROM housing_prices WHERE {IS_COUNTY}
        UNION
        SELECT year FROM demographics WHERE {IS_COUNTY}
        ORDER BY year
    """
    return list(db.execute(text(sql)).scalars())


def data_year_for(db: Session, dataset: str, year: int) -> int | None:
    """Latest county data year at or before `year` for this dataset; else its earliest."""
    table = TABLES[dataset]
    sql = f"""
        SELECT COALESCE((SELECT max(year) FROM {table} WHERE {IS_COUNTY} AND year <= :year),
                        (SELECT min(year) FROM {table} WHERE {IS_COUNTY}))
    """
    return db.execute(text(sql), {"year": year}).scalar()


def values_for(db: Session, dataset: str, data_year: int) -> dict[str, dict]:
    """{county geoid: {metric: value}} for one year. Missing values are left out."""
    metrics = metric_columns(dataset)
    columns = ", ".join(sorted(set(metrics.values())))
    sql = f"SELECT geoid, {columns} FROM {TABLES[dataset]} WHERE {IS_COUNTY} AND year = :data_year"

    values: dict[str, dict] = {}
    for row in db.execute(text(sql), {"data_year": data_year}).mappings():
        county_values = {key: row[column] for key, column in metrics.items() if row[column] is not None}
        if county_values:
            values[row["geoid"]] = county_values
    return values


def domains(db: Session, dataset: str) -> dict[str, list[float] | None]:
    """2nd–98th percentile of county values across all years, so colors are comparable over time."""
    metrics = metric_columns(dataset)
    selects = ", ".join(
        f"percentile_cont(ARRAY[0.02, 0.98]) WITHIN GROUP (ORDER BY {column}) AS {column}"
        for column in sorted(set(metrics.values()))
    )
    row = db.execute(text(f"SELECT {selects} FROM {TABLES[dataset]} WHERE {IS_COUNTY}")).mappings().one()
    return {key: row[column] for key, column in metrics.items()}


def series(db: Session, dataset: str, column: str, geoid: str) -> list[dict]:
    """One county's values over time."""
    sql = f"""
        SELECT year, {column} AS value
        FROM {TABLES[dataset]}
        WHERE geoid = :geoid AND {column} IS NOT NULL
        ORDER BY year
    """
    return [dict(row) for row in db.execute(text(sql), {"geoid": geoid}).mappings()]
