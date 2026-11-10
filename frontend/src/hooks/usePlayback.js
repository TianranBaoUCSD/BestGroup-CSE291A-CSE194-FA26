import { useCallback, useEffect, useState } from 'react';
import { nextYear } from '../lib/years.js';

/** Steps through `years` (only years with data) on a timer, stopping at the last one. */
export function usePlayback(year, setYear, years, speedMs = 800) {
  const [playing, setPlaying] = useState(false);
  const last = years[years.length - 1];

  useEffect(() => {
    if (!playing) return undefined;
    const id = setInterval(() => setYear((y) => nextYear(years, y) ?? y), speedMs);
    return () => clearInterval(id);
  }, [playing, setYear, speedMs, years]);

  useEffect(() => {
    if (playing && (years.length === 0 || year >= last)) setPlaying(false);
  }, [playing, year, last, years.length]);

  const toggle = useCallback(() => {
    if (years.length === 0) return;
    if (!playing && year >= last) setYear(years[0]);
    setPlaying(!playing);
  }, [playing, year, last, years, setYear]);

  const stop = useCallback(() => setPlaying(false), []);

  return { playing, toggle, stop };
}
