// Thin client for the FastAPI backend (proxied at /api by Vite in dev).

/** An HTTP error from the API; `status` 0 means the server couldn't be reached. */
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function getJSON(path, signal) {
  let res;
  try {
    res = await fetch(path, { signal });
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    throw new ApiError('Could not reach the API', 0);
  }
  // Vite's dev proxy answers 500/502/504 itself when FastAPI isn't running.
  if (!res.ok) {
    let detail = `API responded ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* not JSON */
    }
    throw new ApiError(detail, res.status);
  }
  return res.json();
}

/**
 * GET /api/metrics?dataset=&year=
 * -> { dataset, requested_year, data_year, values: { "06001": { metric: value } }, domains: { metric: [lo, hi] | null } }
 */
export function fetchMetrics(dataset, year, signal) {
  const params = new URLSearchParams({ dataset, year: String(year) });
  return getJSON(`/api/metrics?${params}`, signal);
}

/** GET /api/metadata -> { year_min, year_max, years_with_data, datasets } */
export function fetchMetadata(signal) {
  return getJSON('/api/metadata', signal);
}

export async function fetchGeoJSON(path, signal) {
  const res = await fetch(path, { signal });
  if (!res.ok) throw new Error(`Could not load ${path} (${res.status})`);
  return res.json();
}
