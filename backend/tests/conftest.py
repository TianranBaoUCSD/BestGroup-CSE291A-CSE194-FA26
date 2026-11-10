"""API tests run against a real PostgreSQL, because the queries use Postgres-only SQL.

Set TEST_DATABASE_URL to a throwaway database: its tables are dropped and recreated.
Tests are skipped when it isn't set, and they never touch DATABASE_URL.
"""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.db import Base
from app.db.session import get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

ALAMEDA = "06001"
MARIN = "06041"
OAKLAND = "0600192230"


def _demographic(geoid, year, total, source="acs5"):
    return {
        "geoid": geoid, "year": year, "source": source, "period_label": str(year), "total_population": total,
        "white": total, "black": 0, "native_american": 0, "asian": 0, "pacific_islander": 0,
        "other_race": 0, "two_or_more": 0,
    }


@pytest.fixture(scope="session")
def engine():
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL is not set")
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def seeded(engine):
    regions = [
        {"geoid": ALAMEDA, "name": "Alameda", "level": "county", "county": None},
        {"geoid": MARIN, "name": "Marin", "level": "county", "county": None},
        {"geoid": OAKLAND, "name": "Oakland", "level": "subdivision", "county": ALAMEDA},
    ]
    demographics = [
        _demographic(ALAMEDA, 2009, 505000, "acs5_ccd_sum"),
        _demographic(ALAMEDA, 2012, 1500000, "acs1"),
        _demographic(ALAMEDA, 2020, 1600000, "census2020_ccd_sum"),
        _demographic(OAKLAND, 2009, 400000),
        _demographic(OAKLAND, 2014, 420000),  # no county row this year
        _demographic(OAKLAND, 2020, 460000),
    ]
    housing = [
        {"geoid": ALAMEDA, "year": 2005, "zhvi": 500000.0, "zori": None},
        {"geoid": ALAMEDA, "year": 2015, "zhvi": 700000.0, "zori": 2100.0},
        {"geoid": ALAMEDA, "year": 2020, "zhvi": 950000.0, "zori": 2500.0},
        {"geoid": MARIN, "year": 2020, "zhvi": 1200000.0, "zori": 3000.0},
    ]
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE regions, demographics, housing_prices, housing_prices_monthly"))
        conn.execute(text("INSERT INTO regions VALUES (:geoid, :name, :level, :county)"), regions)
        conn.execute(
            text(
                "INSERT INTO demographics VALUES (:geoid, :year, :source, :period_label, :total_population, :white,"
                " :black, :native_american, :asian, :pacific_islander, :other_race, :two_or_more)"
            ),
            demographics,
        )
        conn.execute(
            text("INSERT INTO housing_prices (geoid, year, zhvi_usd, zori_usd) VALUES (:geoid, :year, :zhvi, :zori)"),
            housing,
        )


@pytest.fixture()
def client(engine, seeded):
    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
