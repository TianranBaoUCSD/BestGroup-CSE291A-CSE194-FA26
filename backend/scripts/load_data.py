"""Load /data into PostgreSQL. Replaces everything in the data tables.

Run from backend/ after `alembic upgrade head`:
    python scripts/load_data.py
    python scripts/load_data.py --dry-run      # load and validate, then roll back

Everything runs in one transaction, so a failed check leaves the database as it was.

Demographics come from demographic_raw/, not demographic_processed/. The processed
files are missing the 2020 Census, leave Asian residents out of the 2000 totals,
double-count multiracial residents in ACS OTHER, and have no GEOIDs.

  Source               Level        Stored year
  Census 2000          subdivision  2000 (summed to county)
  ACS5 2005-2009       subdivision  2009 (summed to county)
  ACS1 2010-19, 21-25  county       the survey year
  ACS5 2010-14 / 15-19 subdivision  2014, 2019
  Census 2020          subdivision  2020 (summed to county)
  ACS5 2020-24         subdivision  2024

An ACS 5-year span is a single data point, stored under its end year. County totals
are summed from subdivisions only for 2000, 2009 and 2020, where ACS1 has no figure.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Connection, text

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

DEFAULT_DATA_DIR = BACKEND.parent / "data" / "BestGroup-CSE291A-CSE194-FA26"
HOUSING_DIR = "bay_area_county_housing_notebook/cleaned_outputs"

STATE = "06"
COUNTIES = {
    "001": "Alameda",
    "013": "Contra Costa",
    "041": "Marin",
    "055": "Napa",
    "075": "San Francisco",
    "081": "San Mateo",
    "085": "Santa Clara",
    "095": "Solano",
    "097": "Sonoma",
}

RACE_COLUMNS = ("white", "black", "native_american", "asian", "pacific_islander", "other_race", "two_or_more")

EXPECTED_ROWS = {"regions": 69, "demographics": 446, "housing_prices": 234, "housing_prices_monthly": 2808}


@dataclass(frozen=True)
class DemographicSource:
    path: str
    year: int
    period_label: str
    source: str
    variables: str  # column prefix for NHGIS tables, e.g. "AUO7E" gives AUO7E001, AUO7E002, …
    county_sum: bool = False  # add county totals by summing the subdivisions


# NHGIS names each year's table differently, so the column prefix is listed per file.
SUBDIVISION_SOURCES = [
    DemographicSource("demographic_raw/census/2000_census.csv", 2000, "2000", "census2000", "GQO", county_sum=True),
    DemographicSource("demographic_raw/acs5/2005-2009_subcounty.csv", 2009, "2005-2009", "acs5", "RLAE", county_sum=True),
    DemographicSource("demographic_raw/acs5/2010-2014_subcounty.csv", 2014, "2010-2014", "acs5", "ABA2E"),
    DemographicSource("demographic_raw/acs5/2015-2019_subcounty.csv", 2019, "2015-2019", "acs5", "ALUCE"),
    DemographicSource("demographic_raw/census/2020_census.csv", 2020, "2020", "census2020", "U7J", county_sum=True),
    DemographicSource("demographic_raw/acs5/2020-2024_subcounty.csv", 2024, "2020-2024", "acs5", "AUO7E"),
]
ACS1_PREFIXES = {
    2010: "IHYE", 2011: "LJCE", 2012: "OJFE", 2013: "SBME", 2014: "AAA6E", 2015: "ACK3E", 2016: "AE2CE",
    2017: "AGXGE", 2018: "AIUXE", 2019: "AKSME", 2021: "ANLTE", 2022: "APKGE", 2023: "ARKSE", 2024: "ATLPE",
}


class ValidationError(Exception):
    pass


# ----------------------------------------------------------------------------- reading
def read_csv(path: Path) -> list[dict[str, str]]:
    raw = path.read_bytes()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("latin-1")
    return list(csv.DictReader(content.splitlines()))


def _optional_float(value: str | None) -> float | None:
    return float(value) if value not in (None, "") else None


def _optional_int(value: str | None) -> int | None:
    return int(float(value)) if value not in (None, "") else None


def _race_counts(row: dict[str, str], prefix: str) -> dict[str, int]:
    """Total and the seven mutually exclusive race groups. Subtotals of 'two or more' are ignored."""
    if prefix == "GQO":  # Census 2000 publishes no total, and its columns start at White
        counts = {name: int(row[f"GQO{i:03d}"]) for i, name in enumerate(RACE_COLUMNS, start=1)}
        return {"total_population": sum(counts.values()), **counts}
    names = ("total_population", *RACE_COLUMNS)
    return {name: int(row[f"{prefix}{i:03d}"]) for i, name in enumerate(names, start=1)}


def read_subdivisions(data_dir: Path, src: DemographicSource) -> Iterator[tuple[str, str, str, dict[str, int]]]:
    """(geoid, county code, name, counts) for each Bay Area subdivision in a file."""
    for row in read_csv(data_dir / src.path):
        county = row["COUNTYA"]
        if row["STATEA"] != STATE or county not in COUNTIES:
            continue
        code = row.get("COUSUBA") or row["CTY_SUBA"]
        name = (row.get("COUSUB") or row["CTY_SUB"]).removesuffix(" CCD")
        yield f"{STATE}{county}{code}", county, name, _race_counts(row, src.variables)


def read_acs1_county(data_dir: Path, year: int) -> Iterator[tuple[str, dict[str, int]]]:
    """(county geoid, counts) from one ACS 1-year file."""
    for row in read_csv(data_dir / f"demographic_raw/acs1/{year}_county.csv"):
        if row["STATEA"] == STATE and row["COUNTYA"] in COUNTIES:
            yield f"{STATE}{row['COUNTYA']}", _race_counts(row, ACS1_PREFIXES[year])


def read_acs1_2025(data_dir: Path) -> Iterator[tuple[str, dict[str, int]]]:
    """The 2025 file comes straight from the Census Bureau, with different columns from NHGIS."""
    names = ("total_population", *RACE_COLUMNS)
    for row in read_csv(data_dir / "demographic_raw/acs1/2025_county.csv"):
        geo_id = row["GEO_ID"]
        if not geo_id.startswith("0500000US"):  # skips the file's second header row
            continue
        geoid = geo_id[-5:]
        if geoid[:2] == STATE and geoid[2:] in COUNTIES:
            yield geoid, {name: int(row[f"B02001_{i:03d}E"]) for i, name in enumerate(names, start=1)}


def build_demographics(data_dir: Path) -> tuple[list[dict], list[dict]]:
    regions = {
        f"{STATE}{code}": {"geoid": f"{STATE}{code}", "name": name, "level": "county", "county_geoid": None}
        for code, name in COUNTIES.items()
    }
    rows: list[dict] = []

    # In date order, so a subdivision keeps the name from its latest vintage.
    for src in SUBDIVISION_SOURCES:
        county_totals: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for geoid, county, name, counts in read_subdivisions(data_dir, src):
            county_geoid = f"{STATE}{county}"
            regions[geoid] = {"geoid": geoid, "name": name, "level": "subdivision", "county_geoid": county_geoid}
            rows.append({"geoid": geoid, "year": src.year, "source": src.source, "period_label": src.period_label, **counts})
            for column, value in counts.items():
                county_totals[county_geoid][column] += value
        if src.county_sum:
            rows += [
                {"geoid": geoid, "year": src.year, "source": f"{src.source}_ccd_sum", "period_label": src.period_label, **totals}
                for geoid, totals in county_totals.items()
            ]

    for year in ACS1_PREFIXES:
        rows += [
            {"geoid": geoid, "year": year, "source": "acs1", "period_label": str(year), **counts}
            for geoid, counts in read_acs1_county(data_dir, year)
        ]
    rows += [
        {"geoid": geoid, "year": 2025, "source": "acs1", "period_label": "2025", **counts}
        for geoid, counts in read_acs1_2025(data_dir)
    ]
    return list(regions.values()), rows


def build_housing(data_dir: Path) -> tuple[list[dict], list[dict]]:
    housing = data_dir / HOUSING_DIR
    annual = [
        {
            "geoid": row["COUNTY_FIPS"],
            "year": int(row["YEAR"]),
            "zillow_region_id": _optional_int(row["ZILLOW_REGION_ID"]),
            "zhvi_usd": _optional_float(row["ZHVI_AVAILABLE_MONTH_MEAN_USD"]),
            "zhvi_months_observed": _optional_int(row["ZHVI_MONTHS_OBSERVED"]),
            "zori_usd": _optional_float(row["ZORI_AVAILABLE_MONTH_MEAN_USD"]),
            "zori_months_observed": _optional_int(row["ZORI_MONTHS_OBSERVED"]),
            "fhfa_annual_change_pct": _optional_float(row["FHFA_ANNUAL_CHANGE_PCT"]),
            "fhfa_hpi_native": _optional_float(row["FHFA_HPI_NATIVE"]),
            "fhfa_hpi_1990_base": _optional_float(row["FHFA_HPI_1990_BASE"]),
            "fhfa_hpi_2000_base": _optional_float(row["FHFA_HPI_2000_BASE"]),
        }
        for row in read_csv(housing / "bay_area_county_housing_combined_2000_2025.csv")
    ]

    # ZORI starts in 2015, so every month has a ZHVI row and some have a ZORI value.
    monthly: dict[tuple[str, int, int], dict] = {}
    for row in read_csv(housing / "bay_area_county_zhvi_monthly_2000_2025.csv"):
        key = (row["COUNTY_FIPS"], int(row["YEAR"]), int(row["MONTH"]))
        monthly[key] = {
            "geoid": key[0], "year": key[1], "month": key[2],
            "zhvi_usd": _optional_float(row["ZHVI_USD"]), "zori_usd": None,
        }
    for row in read_csv(housing / "bay_area_county_zori_monthly.csv"):
        key = (row["COUNTY_FIPS"], int(row["YEAR"]), int(row["MONTH"]))
        monthly[key]["zori_usd"] = _optional_float(row["ZORI_USD_PER_MONTH"])
    return annual, list(monthly.values())


# ----------------------------------------------------------------------------- writing
def _insert(conn: Connection, table: str, rows: list[dict]) -> None:
    columns = list(rows[0])
    names = ", ".join(columns)
    params = ", ".join(f":{c}" for c in columns)
    conn.execute(text(f"INSERT INTO {table} ({names}) VALUES ({params})"), rows)


def load(conn: Connection, data_dir: Path) -> dict[str, int]:
    """Replace all data tables and validate them. The caller owns the transaction."""
    regions, demographics = build_demographics(data_dir)
    annual, monthly = build_housing(data_dir)

    conn.execute(text("TRUNCATE regions, demographics, housing_prices, housing_prices_monthly"))
    # Counties first, because subdivisions reference them.
    _insert(conn, "regions", sorted(regions, key=lambda r: r["level"] != "county"))
    _insert(conn, "demographics", demographics)
    _insert(conn, "housing_prices", annual)
    _insert(conn, "housing_prices_monthly", monthly)
    return validate(conn)


# ----------------------------------------------------------------------------- checks
def validate(conn: Connection) -> dict[str, int]:
    """Raise ValidationError listing every failed check. Returns the row counts."""
    problems: list[str] = []

    def scalar(sql: str, **params):
        return conn.execute(text(sql), params).scalar()

    counts = {table: scalar(f"SELECT count(*) FROM {table}") for table in EXPECTED_ROWS}
    for table, expected in EXPECTED_ROWS.items():
        if counts[table] != expected:
            problems.append(f"{table}: expected {expected} rows, found {counts[table]}")

    race_sum = " + ".join(RACE_COLUMNS)
    bad = scalar(f"SELECT count(*) FROM demographics WHERE {race_sum} <> total_population")
    if bad:
        problems.append(f"demographics: race groups don't add up to the total in {bad} rows")

    bad = scalar(
        "SELECT count(*) FROM (SELECT d.geoid FROM demographics d JOIN regions r USING (geoid)"
        " WHERE r.level = 'county' GROUP BY d.geoid HAVING count(*) <> 18) AS c"
    )
    if bad:
        problems.append(f"demographics: {bad} counties don't have all 18 data years")

    bad = scalar("SELECT count(*) FROM housing_prices WHERE zhvi_usd IS NULL")
    if bad:
        problems.append(f"housing_prices: {bad} rows have no ZHVI value")

    known = [
        ("San Francisco 2000 population", 776733,
         "SELECT total_population FROM demographics WHERE geoid = '06075' AND year = 2000"),
        ("Alameda 2020 population", 1682353,
         "SELECT total_population FROM demographics WHERE geoid = '06001' AND year = 2020"),
        ("Alameda 2000 ZHVI", 294741.32,
         "SELECT zhvi_usd FROM housing_prices WHERE geoid = '06001' AND year = 2000"),
        ("Contra Costa 2007 ZHVI months", 11,
         "SELECT zhvi_months_observed FROM housing_prices WHERE geoid = '06013' AND year = 2007"),
        ("San Francisco 2020 ZORI months", 10,
         "SELECT zori_months_observed FROM housing_prices WHERE geoid = '06075' AND year = 2020"),
        ("Napa 2015 ZORI", None,
         "SELECT zori_usd FROM housing_prices WHERE geoid = '06055' AND year = 2015"),
        ("Contra Costa Feb 2007 monthly ZHVI", None,
         "SELECT zhvi_usd FROM housing_prices_monthly WHERE geoid = '06013' AND year = 2007 AND month = 2"),
    ]
    for label, expected, sql in known:
        found = scalar(sql)
        if found != expected:
            problems.append(f"{label}: expected {expected}, found {found}")

    if problems:
        raise ValidationError("\n".join(f"  - {p}" for p in problems))
    return counts


def main() -> None:
    from app.db import engine

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR, help="the data repository folder")
    ap.add_argument("--dry-run", action="store_true", help="load and validate, then roll back")
    args = ap.parse_args()

    with engine.connect() as conn:  # closing without a commit rolls back
        transaction = conn.begin()
        try:
            counts = load(conn, args.data_dir)
        except ValidationError as exc:
            sys.exit(f"Validation failed, nothing was changed:\n{exc}")
        if args.dry_run:
            transaction.rollback()
        else:
            transaction.commit()

    for table, count in counts.items():
        print(f"  {table}: {count} rows")
    print("Validation passed." + (" Dry run: nothing was changed." if args.dry_run else " Data loaded."))


if __name__ == "__main__":
    main()
