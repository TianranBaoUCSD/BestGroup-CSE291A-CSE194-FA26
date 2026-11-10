import { useEffect, useRef, useState } from 'react';
import { timelineGaps, timelineStops } from '../lib/years.js';

/** Width of an element in px, kept up to date as it resizes. */
function useWidth(ref) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return undefined;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(el);
    return () => observer.disconnect();
  }, [ref]);
  return width;
}

/**
 * Year slider limited to `years` (the selected metric's years with data). Each stop is
 * one of those years, evenly spaced, so the handle can't land on a year without data.
 */
export default function YearControl({ year, years, ready, onChange, playing, onTogglePlay }) {
  const ticksRef = useRef(null);
  const width = useWidth(ticksRef);
  const stops = timelineStops(years, width);
  const disabled = !ready || years.length === 0;
  const index = Math.max(0, years.indexOf(year));

  return (
    <>
      <div className="year">
        <button
          type="button"
          className="play-btn"
          onClick={onTogglePlay}
          disabled={disabled}
          aria-label={playing ? 'Pause timeline' : 'Play timeline'}
        >
          {playing ? (
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
              <rect x="3.5" y="3" width="3.5" height="12" rx="1" fill="currentColor" />
              <rect x="11" y="3" width="3.5" height="12" rx="1" fill="currentColor" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
              <path d="M5 3.2 L15 9 L5 14.8 Z" fill="currentColor" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
            </svg>
          )}
        </button>
        <div className="field">
          <span className="field__label">Year</span>
          <output htmlFor="year-range" className="year__value">
            {year}
          </output>
        </div>
      </div>

      <div className="timeline">
        <label htmlFor="year-range" className="sr-only">
          Timeline year
        </label>
        <input
          id="year-range"
          className="timeline__range"
          type="range"
          min={0}
          max={Math.max(0, years.length - 1)}
          step={1}
          value={index}
          disabled={disabled}
          aria-valuetext={String(year)}
          onChange={(e) => onChange(years[Number(e.target.value)])}
        />
        <div className="timeline__ticks" ref={ticksRef} aria-hidden="true">
          {disabled ? (
            <span className="timeline__status">{ready ? 'No years with data' : 'Loading available years…'}</span>
          ) : (
            <>
              {stops.map((s) => (
                <span key={s.year} className="timeline__stop" style={{ left: `${s.pct}%` }}>
                  <span className="timeline__dot" />
                  {s.labeled && <span className={`timeline__tick${s.year === year ? ' is-current' : ''}`}>{s.year}</span>}
                </span>
              ))}
              {timelineGaps(years).map((g) => (
                <span
                  key={g.from}
                  className="timeline__gap"
                  style={{ left: `${g.pct}%` }}
                  title={g.from === g.to ? `No data for ${g.from}` : `No data for ${g.from}–${g.to}`}
                >
                  //
                </span>
              ))}
            </>
          )}
        </div>
      </div>
    </>
  );
}
