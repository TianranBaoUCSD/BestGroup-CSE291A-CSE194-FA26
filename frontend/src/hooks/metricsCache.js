import { fetchMetadata, fetchMetrics } from '../lib/api.js';

// One cache for the whole app, so the timeline and the color-range loader
// never request the same (dataset, year) twice.
const metricsCache = new Map();
let metadataPromise = null;

/** False when the API is up but the database has no rows for this dataset yet. */
export const hasData = (body) => body.data_year != null;

// Failed and empty answers aren't kept, so the next attempt asks the API again.
export function getMetrics(dataset, year) {
  const key = `${dataset}:${year}`;
  if (!metricsCache.has(key)) {
    const p = fetchMetrics(dataset, year).then(
      (body) => {
        if (!hasData(body)) metricsCache.delete(key);
        return body;
      },
      (err) => {
        metricsCache.delete(key);
        throw err;
      },
    );
    metricsCache.set(key, p);
  }
  return metricsCache.get(key);
}

export function getMetadata() {
  if (!metadataPromise) {
    metadataPromise = fetchMetadata().then(
      (meta) => {
        if (!meta.years_with_data?.length) metadataPromise = null;
        return meta;
      },
      (err) => {
        metadataPromise = null;
        throw err;
      },
    );
  }
  return metadataPromise;
}
