# Export API responses

After loading the database, install the development dependencies (`pip install -r requirements-dev.txt`), set `DATABASE_URL` as usual, and run from `backend/`:

```sh
python scripts/export_api.py
# Optional: python scripts/export_api.py --output /path/to/api
```

The script calls the FastAPI application in-process and writes JSON responses under `frontend/public/data/api/` by default:

- `health.json` and `metadata.json`
- `metrics/<dataset>/<requested-year>.json`, for every year in the API's supported range
- `series/<county-geoid>/<metric>.json`, for every county and every metric in metadata

The county list is read from the database because the API does not expose one. A failed request stops the export and leaves any previous snapshot in place. Commit the generated `frontend/public/data/api/` directory so the files are included in the frontend build and deployed to GitHub Pages. Rerun the exporter after each data load. `health.json` describes the database at export time, not live service health.
