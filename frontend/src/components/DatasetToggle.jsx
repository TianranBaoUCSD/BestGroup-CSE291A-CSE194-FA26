import { DATASETS } from '../constants.js';

const ICONS = {
  housing: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 10.5 12 3l9 7.5" />
      <path d="M5 9.5V21h14V9.5" />
      <path d="M10 21v-6h4v6" />
    </svg>
  ),
  demographics: (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20c.6-3.6 3.3-6 6.5-6s5.9 2.4 6.5 6" />
      <circle cx="17" cy="9" r="2.5" />
      <path d="M17 14c2.5 0 4.2 2 4.5 5" />
    </svg>
  ),
};

/** Two-option pill switch with a sliding thumb: Housing <-> Demographics. */
export default function DatasetToggle({ value, onChange }) {
  const keys = Object.keys(DATASETS);
  const index = keys.indexOf(value);
  return (
    <div className="field">
      <span className="field__label">Dataset</span>
      <div className="seg" role="group" aria-label="Dataset">
        <span
          className="seg__thumb"
          aria-hidden="true"
          style={{ transform: `translateX(${index * 100}%)`, width: `calc(${100 / keys.length}% - 4px)` }}
        />
        {keys.map((key) => (
          <button
            key={key}
            type="button"
            className={`seg__btn${key === value ? ' is-active' : ''}`}
            aria-pressed={key === value}
            onClick={() => onChange(key)}
          >
            {ICONS[key]}
            {DATASETS[key].label}
          </button>
        ))}
      </div>
    </div>
  );
}
