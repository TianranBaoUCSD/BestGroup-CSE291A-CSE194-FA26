"""FastAPI backend for the Bay Area Housing & Demographics Explorer.

Run from the backend/ folder:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from . import queries
from .db.session import get_db
from .metrics_config import DATASETS, YEAR_MAX, YEAR_MIN, find_metric

app = FastAPI(title="Bay Area Housing & Demographics API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(OperationalError)
def database_unavailable(_: Request, __: OperationalError) -> JSONResponse:
    return JSONResponse({"detail": "Database unavailable"}, status_code=503)


def _dataset(name: str) -> dict:
    if name not in DATASETS:
        raise HTTPException(404, f"Unknown dataset '{name}'. Options: {', '.join(DATASETS)}")
    return DATASETS[name]


@app.get("/api/health")
def health(db: Session = Depends(get_db)) -> dict:
    return {"status": "ok", "years_loaded": queries.years_with_data(db)}


@app.get("/api/metadata")
def metadata(db: Session = Depends(get_db)) -> dict:
    return {
        "year_min": YEAR_MIN,
        "year_max": YEAR_MAX,
        "years_with_data": queries.years_with_data(db),
        "datasets": DATASETS,
    }


@app.get("/api/metrics")
def metrics(
    dataset: str = Query("housing"),
    year: int = Query(..., ge=YEAR_MIN, le=YEAR_MAX),
    db: Session = Depends(get_db),
) -> dict:
    """Every county's values for one dataset, from the latest year with data at or before `year`."""
    keys = list(_dataset(dataset)["metrics"])
    data_year = queries.data_year_for(db, dataset, year)
    found_domains = queries.domains(db, dataset)
    return {
        "dataset": dataset,
        "requested_year": year,
        "data_year": data_year,
        "values": queries.values_for(db, dataset, data_year) if data_year is not None else {},
        "domains": {key: found_domains.get(key) for key in keys},
    }


@app.get("/api/series")
def series(geoid: str, metric: str, db: Session = Depends(get_db)) -> dict:
    """One county's values over time, e.g. for a line chart."""
    found = find_metric(metric)
    if found is None:
        raise HTTPException(404, f"Unknown metric '{metric}'")
    if not queries.is_county(db, geoid):
        raise HTTPException(404, f"Unknown county '{geoid}'. Use a 5-digit county GEOID, e.g. 06001.")
    dataset, column = found
    points = queries.series(db, dataset, column, geoid) if column else []
    return {"geoid": geoid, "metric": metric, "points": points}
