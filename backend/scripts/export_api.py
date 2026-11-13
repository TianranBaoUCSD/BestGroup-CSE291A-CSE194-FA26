"""Export FastAPI responses as static JSON. Run from backend/: python scripts/export_api.py."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import SessionLocal
from app.main import app


def county_geoids() -> list[str]:
    # The API has no county-list endpoint; include even counties with no data.
    with SessionLocal() as db:
        return list(db.execute(text("SELECT geoid FROM regions WHERE level = 'county' ORDER BY geoid")).scalars())


def export(output: Path) -> int:
    """Generate a complete snapshot in a temporary directory before replacing the old one."""
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with tempfile.TemporaryDirectory(prefix=".api-export-", dir=output.parent) as tmp:
        staging = Path(tmp) / "snapshot"
        staging.mkdir()
        with TestClient(app) as client:
            def save(url: str, relative: str, params: dict | None = None) -> dict:
                nonlocal count
                response = client.get(url, params=params)
                response.raise_for_status()
                body = response.json()
                path = staging / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                count += 1
                return body

            save('/api/health', 'health.json')
            metadata = save('/api/metadata', 'metadata.json')
            metrics = set()
            for dataset, config in metadata['datasets'].items():
                metrics.update(config['metrics'])
                for year in range(metadata['year_min'], metadata['year_max'] + 1):
                    save('/api/metrics', f'metrics/{dataset}/{year}.json', {'dataset': dataset, 'year': year})
            for geoid in county_geoids():
                for metric in sorted(metrics):
                    save('/api/series', f'series/{geoid}/{metric}.json', {'geoid': geoid, 'metric': metric})
        # Keep the previous snapshot if replacing it fails.
        backup = Path(tmp) / 'previous'
        if output.exists():
            output.rename(backup)
        try:
            staging.rename(output)
        except OSError:
            if backup.exists():
                backup.rename(output)
            raise
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=BACKEND.parent / 'frontend' / 'public' / 'data' / 'api', help='snapshot directory (default: frontend/public/data/api)')
    args = parser.parse_args()
    count = export(args.output)
    print(f'Exported {count} responses to {args.output}')


if __name__ == '__main__':
    main()
