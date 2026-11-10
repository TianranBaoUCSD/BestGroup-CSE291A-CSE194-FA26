import { useEffect, useState } from 'react';
import { YEAR_MAX, YEAR_MIN } from '../constants.js';
import { loadWithRetry } from '../lib/retry.js';
import { yearsByMetric } from '../lib/years.js';
import { getMetadata, getMetrics, hasData } from './metricsCache.js';

const NONE = {};

/**
 * Which years each metric in `dataset` has data for, worked out from the API:
 * asks /api/metrics once for every year in /api/metadata's years_with_data (cached)
 * and keeps the years the database really has, not ones it falls back from.
 * status: 'loading' until the API answers with data, then 'ok'.
 */
export function useAvailableYears(dataset, metrics) {
  const [state, setState] = useState({ dataset, status: 'loading', years: NONE });
  const signature = metrics.map((m) => (m.share ? `${m.key}=${m.share.count}/${m.share.total}` : m.key)).join(',');

  useEffect(() => {
    setState({ dataset, status: 'loading', years: NONE });

    const load = async () => {
      const meta = await getMetadata();
      const candidates = (meta.years_with_data ?? []).filter((y) => y >= YEAR_MIN && y <= YEAR_MAX);
      const bodies = await Promise.all(candidates.map((y) => getMetrics(dataset, y)));
      return bodies.filter((b) => hasData(b) && b.data_year === b.requested_year);
    };

    // useMetrics already reports API problems, so there's no error to show here.
    return loadWithRetry(load, {
      isReady: (bodies) => bodies.length > 0,
      onResult: (bodies) => {
        if (bodies.length > 0) setState({ dataset, status: 'ok', years: yearsByMetric(bodies, metrics) });
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataset, signature]);

  // Right after a dataset switch, don't hand out the previous dataset's years.
  return state.dataset === dataset ? state : { dataset, status: 'loading', years: NONE };
}
