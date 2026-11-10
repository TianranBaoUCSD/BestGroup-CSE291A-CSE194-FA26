// Pure helpers for limiting the timeline to years that have data.

import { shareOf } from './metrics.js';

/**
 * { metricKey: [sorted years] } — the years in which at least one county has a value.
 * bodies: /api/metrics responses whose data_year is the year that was asked for.
 */
export function yearsByMetric(bodies, metrics) {
  const found = Object.fromEntries(metrics.map((m) => [m.key, new Set()]));
  for (const body of bodies) {
    for (const countyValues of Object.values(body.values ?? {})) {
      for (const m of metrics) {
        const v = m.share ? shareOf(countyValues, m.share) : countyValues[m.key];
        if (v != null) found[m.key].add(body.data_year);
      }
    }
  }
  return Object.fromEntries(Object.entries(found).map(([key, set]) => [key, [...set].sort((a, b) => a - b)]));
}

/** Keeps `year` if it has data, otherwise the earliest year that does. */
export function pickYear(year, years) {
  if (years.length === 0 || years.includes(year)) return year;
  return years[0];
}

/** The next year with data after `year`, or null at the end. */
export function nextYear(years, year) {
  return years.find((y) => y > year) ?? null;
}

/**
 * One stop per year, evenly spaced. Labels go to the first and last year, the first
 * year after a gap (e.g. 2009 after 2000), then multiples of 5, skipping any label
 * that would sit closer than `minPx` to one already placed.
 */
export function timelineStops(years, trackPx, minPx = 44) {
  const n = years.length;
  const stops = years.map((year, i) => ({ year, pct: n <= 1 ? 50 : (i / (n - 1)) * 100, labeled: false }));
  if (n === 0) return stops;

  const indexes = years.map((_, i) => i);
  const priority = [
    0,
    n - 1,
    ...indexes.filter((i) => i > 0 && years[i] - years[i - 1] > 1),
    ...indexes.filter((i) => years[i] % 5 === 0),
  ];
  const minPct = trackPx > 0 ? (minPx / trackPx) * 100 : 8;
  const chosen = [];
  for (const i of priority) {
    if (!chosen.includes(i) && chosen.every((j) => Math.abs(stops[j].pct - stops[i].pct) >= minPct)) chosen.push(i);
  }
  for (const i of chosen) stops[i].labeled = true;
  return stops;
}

/** Break marks halfway between stops that skip years, e.g. between 2000 and 2009. */
export function timelineGaps(years) {
  const n = years.length;
  const gaps = [];
  for (let i = 1; i < n; i++) {
    if (years[i] - years[i - 1] > 1) {
      gaps.push({ pct: ((i - 0.5) / (n - 1)) * 100, from: years[i - 1] + 1, to: years[i] - 1 });
    }
  }
  return gaps;
}
