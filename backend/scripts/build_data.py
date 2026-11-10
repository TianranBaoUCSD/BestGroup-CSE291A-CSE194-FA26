"""Download official Census boundaries and data for the nine Bay Area counties.

Writes:
  frontend/public/data/counties.geojson      county outlines (Census cartographic boundaries)
  frontend/public/data/subdivisions.geojson  county subdivisions (Census "CCDs")
  backend/data/metrics.csv                   housing + demographic metrics by GEOID and year

The API no longer reads metrics.csv: it queries PostgreSQL, loaded by scripts/load_data.py.
Only the boundary files are still used, so run this with --skip-data.

Run from the project root (needs internet):
    python backend/scripts/build_data.py
    python backend/scripts/build_data.py --skip-geo      # data only
    python backend/scripts/build_data.py --years 2015 2020 2023

A free Census API key (https://api.census.gov/data/key_signup.html) raises rate
limits: export CENSUS_API_KEY=... before running. It works without one for light use.

Data coverage notes:
  * ACS 5-year estimates exist for county subdivisions from 2009 onward. "2015"
    means the 2011–2015 five-year estimate.
  * 2000 comes from the Decennial Census (SF1/SF3). Subdivision codes changed
    after 2000, so some 2000 values may not line up with today's boundaries.
  * 2001–2008 have no subdivision-level data; the API serves the nearest year.
  * Dollar values are nominal (not adjusted for inflation).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

try:
    import shapefile  # pyshp
except ImportError:  # pragma: no cover
    shapefile = None

ROOT = Path(__file__).resolve().parents[2]
GEO_OUT = ROOT / "frontend" / "public" / "data"
CSV_OUT = ROOT / "backend" / "data" / "metrics.csv"

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
GEO_VINTAGE = 2023
COUSUB_URL = f"https://www2.census.gov/geo/tiger/GENZ{GEO_VINTAGE}/shp/cb_{GEO_VINTAGE}_{STATE}_cousub_500k.zip"
COUNTY_URL = f"https://www2.census.gov/geo/tiger/GENZ{GEO_VINTAGE}/shp/cb_{GEO_VINTAGE}_us_county_500k.zip"

ACS_YEARS = list(range(2009, 2025))  # 5-year ACS; extend when new releases come out
ACS_VARS = [
    "B25077_001E",  # median home value
    "B25064_001E",  # median gross rent
    "B25003_001E", "B25003_002E",  # occupied units, owner-occupied
    "B25002_001E", "B25002_003E",  # housing units, vacant
    "B01003_001E",  # total population
    "B19013_001E",  # median household income
    "B01002_001E",  # median age
    "B15003_001E", "B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E",  # education (2012+)
]


# ----------------------------------------------------------------------------- helpers
def http_get(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "cse194-bay-area-explorer"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def census_api(dataset: str, year: int, variables: list[str], for_: str, in_: str | None) -> list[dict]:
    params = {"get": ",".join(["NAME", *variables]), "for": for_}
    if in_:
        params["in"] = in_
    if key := os.environ.get("CENSUS_API_KEY"):
        params["key"] = key
    url = f"https://api.census.gov/data/{year}/{dataset}?{urllib.parse.urlencode(params)}"
    rows = json.loads(http_get(url))
    header, *body = rows
    return [dict(zip(header, r)) for r in body]


def num(row: dict, var: str) -> float | None:
    try:
        v = float(row.get(var))
    except (TypeError, ValueError):
        return None
    return None if v < 0 else v  # Census uses large negative sentinels for "no estimate"


def pct(part: float | None, whole: float | None) -> float | None:
    return round(100 * part / whole, 2) if part is not None and whole else None


def geoid_of(row: dict) -> str:
    if "county subdivision" in row:
        return row["state"] + row["county"] + row["county subdivision"]
    return row["state"] + row["county"]


def round_coords(obj):
    if isinstance(obj, float):
        return round(obj, 5)
    if isinstance(obj, (list, tuple)):
        return [round_coords(x) for x in obj]
    return obj


# ----------------------------------------------------------------------------- boundaries
def read_zipped_shapefile(url: str):
    if shapefile is None:
        sys.exit("pyshp is missing: pip install -r backend/requirements.txt")
    print(f"  downloading {url}")
    z = zipfile.ZipFile(io.BytesIO(http_get(url, timeout=300)))
    name = next(n[:-4] for n in z.namelist() if n.endswith(".shp"))
    reader = shapefile.Reader(
        shp=io.BytesIO(z.read(name + ".shp")),
        shx=io.BytesIO(z.read(name + ".shx")),
        dbf=io.BytesIO(z.read(name + ".dbf")),
    )
    fields = [f[0] for f in reader.fields[1:]]
    for sr in reader.iterShapeRecords():
        yield dict(zip(fields, sr.record)), sr.shape.__geo_interface__


def build_geo() -> None:
    GEO_OUT.mkdir(parents=True, exist_ok=True)

    counties = []
    for props, geom in read_zipped_shapefile(COUNTY_URL):
        if props["STATEFP"] == STATE and props["COUNTYFP"] in COUNTIES:
            counties.append({
                "type": "Feature",
                "properties": {"geoid": props["GEOID"], "name": COUNTIES[props["COUNTYFP"]]},
                "geometry": {"type": geom["type"], "coordinates": round_coords(geom["coordinates"])},
            })

    subs = []
    for props, geom in read_zipped_shapefile(COUSUB_URL):
        if props["COUNTYFP"] in COUNTIES:
            subs.append({
                "type": "Feature",
                "properties": {
                    "geoid": props["GEOID"],
                    "name": props["NAME"],
                    "county": COUNTIES[props["COUNTYFP"]],
                    "county_geoid": STATE + props["COUNTYFP"],
                    "approximate": False,
                },
                "geometry": {"type": geom["type"], "coordinates": round_coords(geom["coordinates"])},
            })

    for fname, feats in (("counties.geojson", counties), ("subdivisions.geojson", subs)):
        path = GEO_OUT / fname
        path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")))
        print(f"  wrote {path.relative_to(ROOT)} ({len(feats)} features)")


# ----------------------------------------------------------------------------- metrics
def acs_metrics(row: dict) -> dict[str, float | None]:
    edu = [num(row, v) for v in ("B15003_022E", "B15003_023E", "B15003_024E", "B15003_025E")]
    return {
        "median_home_value": num(row, "B25077_001E"),
        "median_gross_rent": num(row, "B25064_001E"),
        "owner_occupied_pct": pct(num(row, "B25003_002E"), num(row, "B25003_001E")),
        "vacancy_rate_pct": pct(num(row, "B25002_003E"), num(row, "B25002_001E")),
        "population": num(row, "B01003_001E"),
        "median_household_income": num(row, "B19013_001E"),
        "median_age": num(row, "B01002_001E"),
        "bachelors_pct": pct(sum(edu), num(row, "B15003_001E")) if None not in edu else None,
    }


def fetch_acs(year: int) -> list[tuple[str, int, str, float]]:
    # B15003 starts in 2012; ask only for variables that exist that year.
    variables = [v for v in ACS_VARS if year >= 2012 or not v.startswith("B15003")]
    county_list = ",".join(COUNTIES)
    rows = census_api("acs/acs5", year, variables, f"county:{county_list}", f"state:{STATE}")
    for code in COUNTIES:
        rows += census_api("acs/acs5", year, variables, "county subdivision:*", f"state:{STATE} county:{code}")
    out = []
    for r in rows:
        for metric, value in acs_metrics(r).items():
            if value is not None:
                out.append((geoid_of(r), year, metric, value))
    return out


def fetch_2000() -> list[tuple[str, int, str, float]]:
    """Decennial 2000 (best effort: variable names follow the 2000 SF1/SF3 tables)."""
    sf1_vars = ["P001001", "P013001", "H003001", "H003003", "H004001", "H004002"]
    sf3_vars = ["H085001", "H063001", "P053001"]
    county_list = ",".join(COUNTIES)
    merged: dict[str, dict] = {}
    for dataset, variables in (("dec/sf1", sf1_vars), ("dec/sf3", sf3_vars)):
        rows = census_api(dataset, 2000, variables, f"county:{county_list}", f"state:{STATE}")
        for code in COUNTIES:
            rows += census_api(dataset, 2000, variables, "county subdivision:*", f"state:{STATE} county:{code}")
        for r in rows:
            merged.setdefault(geoid_of(r), {}).update(r)
    out = []
    for geoid, r in merged.items():
        metrics = {
            "population": num(r, "P001001"),
            "median_age": num(r, "P013001"),
            "vacancy_rate_pct": pct(num(r, "H003003"), num(r, "H003001")),
            "owner_occupied_pct": pct(num(r, "H004002"), num(r, "H004001")),
            "median_home_value": num(r, "H085001"),
            "median_gross_rent": num(r, "H063001"),
            "median_household_income": num(r, "P053001"),
        }
        out += [(geoid, 2000, m, v) for m, v in metrics.items() if v is not None]
    return out


def build_metrics(years: list[int], include_2000: bool) -> None:
    records: list[tuple[str, int, str, float]] = []
    if include_2000:
        try:
            print("  Decennial 2000 …")
            records += fetch_2000()
        except Exception as exc:  # keep going; 2000 is a bonus
            print(f"    skipped 2000: {exc}")
    for year in years:
        try:
            print(f"  ACS 5-year {year} …")
            records += fetch_acs(year)
        except Exception as exc:
            print(f"    skipped {year}: {exc}")

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["geoid", "year", "metric", "value"])
        w.writerows(sorted(records))
    print(f"  wrote {CSV_OUT.relative_to(ROOT)} ({len(records)} rows)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-geo", action="store_true", help="don't re-download boundaries")
    ap.add_argument("--skip-data", action="store_true", help="don't download metrics")
    ap.add_argument("--years", type=int, nargs="*", default=ACS_YEARS, help="ACS 5-year end years")
    ap.add_argument("--no-2000", action="store_true", help="skip the Decennial 2000 pull")
    args = ap.parse_args()

    if not args.skip_geo:
        print("Boundaries")
        build_geo()
    if not args.skip_data:
        print("Metrics")
        build_metrics(args.years, include_2000=not args.no_2000)
    print("Done.")


if __name__ == "__main__":
    main()
