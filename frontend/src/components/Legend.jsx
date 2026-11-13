import { DATASETS } from '../constants.js';
import { paletteGradient } from '../lib/colors.js';
import { dataYearNote, formatValue } from '../lib/format.js';

export const STATUS_NOTES = {
  loading: 'Loading data…',
  offline: 'Can’t load the exported data. Retrying automatically.',
  'db-down': 'The exported data is unavailable. Retrying automatically.',
  empty: 'The exported snapshot has no data for this selection.',
  error: 'Could not load the exported data. Run the exporter and check that the files are published.',
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
