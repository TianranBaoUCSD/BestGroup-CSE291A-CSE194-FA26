"""Runs the real loader against the real /data files, when they're available."""

import os
from pathlib import Path

import pytest
from sqlalchemy import text

from scripts.load_data import DEFAULT_DATA_DIR, EXPECTED_ROWS, ValidationError, load, validate

DATA_DIR = Path(os.environ.get("DATA_DIR", DEFAULT_DATA_DIR))


@pytest.fixture()
def loaded(engine):
    if not DATA_DIR.exists():
        pytest.skip(f"{DATA_DIR} is not available")
    conn = engine.connect()
    transaction = conn.begin()
    counts = load(conn, DATA_DIR)
    yield conn, counts
    transaction.rollback()
    conn.close()


def test_row_counts(loaded):
    _, counts = loaded
    assert counts == EXPECTED_ROWS


def test_2000_total_includes_asian_residents(loaded):
    conn, _ = loaded
    row = conn.execute(
        text("SELECT total_population, asian FROM demographics WHERE geoid = '06075' AND year = 2000")
    ).one()
    assert row.total_population == 776733
    assert row.asian == 239938


def test_2020_census_is_loaded(loaded):
    conn, _ = loaded
    count = conn.execute(
        text("SELECT count(*) FROM demographics WHERE year = 2020 AND source = 'census2020'")
    ).scalar()
    assert count == 52


def test_validation_catches_bad_data(loaded):
    conn, _ = loaded
    conn.execute(text("UPDATE demographics SET white = white + 1 WHERE geoid = '06001' AND year = 2012"))
    with pytest.raises(ValidationError, match="add up"):
        validate(conn)
