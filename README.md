# Bay Area Housing & Demographics Explorer (CSE 194)

Explore how housing prices and demographics changed across the nine Bay Area
counties from 2000 to 2026.

```
cse194/
├── frontend/   React (Vite) + Leaflet map, year slider, Housing/Demographics switch
└── backend/    FastAPI + PostgreSQL service that serves metrics by county and year
```

## Run it

**1. Database and backend** (Python 3.10+)

```bash
cp .env.example .env                 # the backend and Alembic read DATABASE_URL from here
docker compose up -d db              # or point DATABASE_URL at any PostgreSQL

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head                 # create the tables
python scripts/load_data.py          # load /data into them
python scripts/export_api.py         # write the snapshot into frontend/public/data/api
```

**2. Frontend** (Node 18+), in a second terminal

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

The frontend reads static JSON from `frontend/public/data/api/`; it does not require a running API or database. Run the exporter after loading data and commit the generated files before building and deploying the site. See `backend/EXPORT.md` for details.

The map shows the nine counties, shaded by the metric picked in the legend
(red for Housing, brown for Demographics). Click a county to zoom in and see its
figures in the side panel.

The year slider only offers years the database has for the metric coloring the map
(worked out from the exported metrics at startup). Years with no data are skipped (a `//` mark
shows where), switching to a metric without the current year jumps to its earliest
year, and metrics with no data at all are hidden.

**Choosing metrics:** the list lives in `frontend/src/constants.js` (`DATASETS`).
A metric can also be a percent of another, e.g. a race group as a share of the
population; its color range is computed in the browser from every year:

```js
{ key: 'asian_pct', label: 'Asian alone', format: 'pct',
  share: { count: 'asian_population', total: 'population' } }
```

## Database (PostgreSQL)

The schema is defined with SQLAlchemy in `backend/app/db/models.py` and created by
Alembic migrations in `backend/migrations/`.

| Table | Holds |
| --- | --- |
| `regions` | each county (5-digit GEOID) and county subdivision (10-digit GEOID), with its parent county |
| `demographics` | population by race, one row per region and year |
| `housing_prices` | annual county values: Zillow ZHVI and ZORI, FHFA house price index |
| `housing_prices_monthly` | monthly county Zillow ZHVI and ZORI |

Subdivision rows are stored in `regions` and `demographics`, but the API doesn't serve them for now.

**Loading data:** `python scripts/load_data.py` replaces everything in these tables
from `data/BestGroup-CSE291A-CSE194-FA26`. It runs in one transaction and checks row
counts, race totals and known values, so a failed check changes nothing. Add
`--dry-run` to validate without saving. Demographics are read from `demographic_raw/`
because `demographic_processed/` has known errors, listed at the top of the script.

| Demographic source | Level | Stored year |
| --- | --- | --- |
| Census 2000 | subdivision, summed to county | 2000 |
| ACS 5-year 2005–2009 | subdivision, summed to county | 2009 |
| ACS 1-year | county | 2010–2019, 2021–2025 |
| ACS 5-year 2010–2014, 2015–2019, 2020–2024 | subdivision | 2014, 2019, 2024 |
| Census 2020 | subdivision, summed to county | 2020 |

**Starting over:** `docker compose down -v` deletes the local database. Then run
`docker compose up -d db`, `alembic upgrade head` and the loader again.

**Run the whole stack in Docker:** `docker compose up -d --build` (the API container
applies migrations on start). Load the data from your machine, because `/data` isn't
in the image.

**Managed Postgres in production:** set `DATABASE_URL` to the provider's connection
string (`postgresql+psycopg://…?sslmode=require`) and run `alembic upgrade head` once per deploy.

**Changing the schema:** edit `models.py`, then
`alembic revision --autogenerate -m "describe change"` and review the file it writes.

## API

All endpoints return county-level data only.

| Endpoint | What it returns |
| --- | --- |
| `GET /api/health` | status + which years have data |
| `GET /api/metadata` | datasets, metrics, year range |
| `GET /api/metrics?dataset=housing&year=2015` | every county's values for that dataset, from the latest year with data at or before the requested one, plus a color-scale domain per metric |
| `GET /api/series?geoid=06001&metric=median_home_value` | one county over time (404 for anything but a county GEOID) |

**What the metrics mean**

* `median_home_value` is Zillow's ZHVI, a typical home value rather than a true median price. An annual figure is the mean of the months available.
* `median_gross_rent` is Zillow's ZORI, a typical market rent rather than Census gross rent. It starts in 2015.
* `owner_occupied_pct`, `vacancy_rate_pct`, `median_household_income`, `median_age` and `bachelors_pct` have no source in `/data` yet, so they return no values.

**Tests** need a throwaway PostgreSQL database, because their tables are dropped and recreated:

```bash
cd backend
TEST_DATABASE_URL=postgresql+psycopg://bayarea:change-me@localhost:5432/bayarea_test pytest
```

Without `TEST_DATABASE_URL` the tests are skipped.

## Map heatmap

* **Housing** is shaded red (light → dark red = low → high).
* **Demographics** is shaded in cappuccino browns.
* Pick which metric drives the colors from the legend in the map's lower-left corner.
* The color scale is fixed across all years, so playing the timeline shows real change.
