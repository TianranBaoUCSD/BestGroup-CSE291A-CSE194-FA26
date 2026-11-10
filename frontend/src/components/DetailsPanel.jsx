import { DATASETS } from '../constants.js';
import { dataYearNote, formatValue } from '../lib/format.js';

export default function DetailsPanel({ dataset, metrics, year, dataYear, status, countyValues, countyName, counties, onBack }) {
  const def = DATASETS[dataset];
  const title = countyName ? `${countyName} County` : 'Bay Area';
  const crumb = countyName ? 'Bay Area' : 'Nine counties';
  const hint = countyName
    ? `${def.label} figures for ${countyName} County, ${year}.`
    : 'Click a county on the map to zoom in and see its figures.';

  let note = 'Figures appear once the API has data.';
  if (status === 'ok' && dataYear != null) {
    note = dataYearNote(year, dataYear);
  }

  return (
    <aside className="details" aria-label="Selection details">
      <div className="details__hero">
        <div className="details__tags">
          <span className="details__year">{year}</span>
          <span className="details__pill">{def.label}</span>
        </div>
        <span className="details__crumb">{crumb}</span>
        <h2 className="details__title">{title}</h2>
        <p className="details__hint">{hint}</p>
      </div>

      <div className="metric-grid">
        {metrics.map((m) => (
          <div key={m.key} className="metric card">
            <span className="metric__label">{m.label}</span>
            <span className="metric__value">{formatValue(countyValues?.[m.key], m.format)}</span>
          </div>
        ))}
      </div>
      <p className="details__note">{note}</p>

      <div className="card list-card">
        <div className="list-card__head">
          <h3>Counties</h3>
          {countyName && (
            <button type="button" className="list-card__back" onClick={onBack}>
              All counties
            </button>
          )}
        </div>
        <div className="list-card__grid">
          {counties.map((c) => (
            <button
              key={c.geoid}
              type="button"
              className={`list-btn${c.active ? ' is-active' : ''}`}
              aria-pressed={c.active}
              onClick={c.onClick}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
