import json

import pytest

from app.db.session import get_db
from app.main import app
from scripts import export_api


def test_export_calls_api_and_replaces_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(export_api, 'county_geoids', lambda: ['06001', '06041'])
    monkeypatch.setattr('app.main.queries.years_with_data', lambda db: [2020])
    monkeypatch.setattr('app.main.queries.data_year_for', lambda db, dataset, year: 2020)
    monkeypatch.setattr('app.main.queries.domains', lambda db, dataset: {})
    monkeypatch.setattr('app.main.queries.values_for', lambda db, dataset, year: {'06001': {'population': 1}})
    monkeypatch.setattr('app.main.queries.is_county', lambda db, geoid: True)
    monkeypatch.setattr('app.main.queries.series', lambda db, dataset, column, geoid: [{'year': 2020, 'value': 1}])
    app.dependency_overrides[get_db] = lambda: None
    output = tmp_path / 'api'
    output.mkdir()
    (output / 'stale.json').write_text('{}')
    try:
        count = export_api.export(output)
    finally:
        app.dependency_overrides.clear()
    metadata = json.loads((output / 'metadata.json').read_text())
    metric_names = {metric for ds in metadata['datasets'].values() for metric in ds['metrics']}
    assert count == 2 + len(metadata['datasets']) * (metadata['year_max'] - metadata['year_min'] + 1) + 2 * len(metric_names)
    assert json.loads((output / 'metrics/housing/2000.json').read_text())['requested_year'] == 2000
    assert json.loads((output / 'series/06041/population.json').read_text())['geoid'] == '06041'
    assert json.loads((output / 'series/06001/median_age.json').read_text())['points'] == []
    assert not (output / 'stale.json').exists()


def test_failed_export_preserves_old_snapshot(tmp_path, monkeypatch):
    output = tmp_path / 'api'
    output.mkdir()
    (output / 'old.json').write_text('{}')
    monkeypatch.setattr('app.main.queries.years_with_data', lambda db: (_ for _ in ()).throw(RuntimeError('database error')))
    app.dependency_overrides[get_db] = lambda: None
    try:
        with pytest.raises(RuntimeError, match='database error'):
            export_api.export(output)
    finally:
        app.dependency_overrides.clear()
    assert (output / 'old.json').read_text() == '{}'
