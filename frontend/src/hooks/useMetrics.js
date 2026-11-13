import { useEffect, useState } from 'react';
import { loadWithRetry } from '../lib/retry.js';
import { getMetrics, hasData } from './metricsCache.js';

/** Maps an API failure to a status the UI explains. */
export function statusForError(err) {
  if (err.status === 0 || err.status === 502 || err.status === 504) return 'offline';
  if (err.status === 503) return 'db-down';
  return 'error';
}

/**
 * Every county's values for (dataset, year), from GET /api/metrics.
 * status: 'loading' | 'ok' | 'empty' (no rows in the database) | 'offline' | 'db-down' | 'error'
 * Keeps retrying while the API is unreachable, failing or has no data, and updates when that clears.
 */
export function useMetrics(dataset, year) {
  const [state, setState] = useState({ status: 'loading', data: null, error: null });

  useEffect(() => {
    // Keep showing the previous year's data while the next one loads.
    setState((s) => (s.data ? s : { ...s, status: 'loading' }));
    return loadWithRetry(() => getMetrics(dataset, year), {
      isReady: hasData,
      onResult: (data) => setState({ status: hasData(data) ? 'ok' : 'empty', data, error: null }),
      onError: (err) => setState({ status: statusForError(err), data: null, error: err.message }),
    });
  }, [dataset, year]);

  return state;
}
