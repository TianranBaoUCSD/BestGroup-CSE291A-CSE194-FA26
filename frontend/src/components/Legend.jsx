import { DATASETS } from '../constants.js';
import { paletteGradient } from '../lib/colors.js';
import { dataYearNote, formatValue } from '../lib/format.js';

export const STATUS_NOTES = {
  loading: 'Loading data…',
  offline: 'Can’t reach the API. Retrying automatically; check that FastAPI is running on port 8000.',
  'db-down': 'The API can’t reach the database. Retrying automatically; check that PostgreSQL is running and DATABASE_URL is set.',
  empty: 'The database has no data yet. Retrying automatically; run backend/scripts/load_data.py to load it.',
  error: 'The API returned an error.',
};

export default function Legend({ dataset, metrics, metric, onMetricChange, domain, hasValues, year, dataYear, status }) {
  const def = DATASETS[dataset];
  const hasDomain = status === 'ok' && domain && domain[0] != null;

  return (
    <div className="legend map-panel">
      <label className="legend__select">
        <span className="sr-only">Color the map by</span>
        <select value={metric.key} onChange={(e) => onMetricChange(e.target.value)}>
          {metrics.map((m) => (
            <option key={m.key} value={m.key}>
              {m.label}
            </option>
          ))}
        </select>
        <span className="legend__year">· {year}</span>
      </label>
      <span className="legend__ramp" style={{ background: paletteGradient(def.palette) }} aria-hidden="true" />
      <div className="legend__ends">
        <span>{hasDomain ? formatValue(domain[0], metric.format, { compact: true }) : 'Low'}</span>
        <span>{hasDomain ? formatValue(domain[1], metric.format, { compact: true }) : 'High'}</span>
      </div>
      {status !== 'ok' && <p className="legend__note">{STATUS_NOTES[status]}</p>}
      {status === 'ok' && !hasValues && <p className="legend__note">No data for this metric yet.</p>}
      {status === 'ok' && hasValues && dataYear !== year && (
        <p className="legend__note">{dataYearNote(year, dataYear)}</p>
      )}
    </div>
  );
}
