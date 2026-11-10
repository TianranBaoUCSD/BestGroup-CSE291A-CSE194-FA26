// Pure helpers for turning API responses into what the map draws.

export const isShare = (metric) => Boolean(metric.share);

/** Percent of `total` that `count` is, or null when either is missing. */
export function shareOf(countyValues, { count, total }) {
  const c = countyValues?.[count];
  const t = countyValues?.[total];
  if (c == null || t == null || t <= 0) return null;
  return (100 * c) / t;
}

/**
 * Adds derived (percent-of-population) metrics to the API's per-county values.
 * values: { "06001": { population: 1600000, asian_population: 500000 } }
 */
export function deriveValues(values, metrics) {
  if (!values) return values;
  const shares = metrics.filter(isShare);
  if (shares.length === 0) return values;
  const out = {};
  for (const [geoid, countyValues] of Object.entries(values)) {
    const extra = {};
    for (const m of shares) {
      const v = shareOf(countyValues, m.share);
      if (v != null) extra[m.key] = v;
    }
    out[geoid] = { ...countyValues, ...extra };
  }
  return out;
}

/** Same method as Postgres percentile_cont: linear interpolation between ranks. */
export function percentile(sorted, q) {
  if (sorted.length === 0) return null;
  const k = (sorted.length - 1) * q;
  const lo = Math.floor(k);
  const hi = Math.min(lo + 1, sorted.length - 1);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (k - lo);
}

/**
 * Color ranges for derived metrics, using every year's county values, so the colors
 * mean the same thing in every year (matching the backend's 2nd–98th percentile).
 * responses: /api/metrics bodies, one per distinct data year.
 */
export function shareDomains(responses, metrics) {
  const result = {};
  for (const m of metrics.filter(isShare)) {
    const all = [];
    for (const body of responses) {
      for (const countyValues of Object.values(body.values ?? {})) {
        const v = shareOf(countyValues, m.share);
        if (v != null) all.push(v);
      }
    }
    all.sort((a, b) => a - b);
    result[m.key] = all.length ? [percentile(all, 0.02), percentile(all, 0.98)] : null;
  }
  return result;
}
