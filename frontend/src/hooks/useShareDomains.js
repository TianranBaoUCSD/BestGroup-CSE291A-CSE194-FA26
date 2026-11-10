import { useEffect, useState } from 'react';
import { YEAR_MAX, YEAR_MIN } from '../constants.js';
import { isShare, shareDomains } from '../lib/metrics.js';
import { loadWithRetry } from '../lib/retry.js';
import { getMetadata, getMetrics, hasData } from './metricsCache.js';

/**
 * Color ranges for percent-of-population metrics, computed once per dataset from
 * every year that has data. Returns {} when the dataset has no such metrics, and
 * until the API has data. Keeps retrying until then.
 */
export function useShareDomains(dataset, metrics) {
  const [domains, setDomains] = useState({});
  const wanted = metrics.filter(isShare);
  const signature = wanted.map((m) => `${m.key}=${m.share.count}/${m.share.total}`).join(',');

  useEffect(() => {
    setDomains({});
    if (wanted.length === 0) return undefined;

    const loadResponses = async () => {
      const meta = await getMetadata();
      const years = (meta.years_with_data ?? []).filter((y) => y >= YEAR_MIN && y <= YEAR_MAX);
      const bodies = await Promise.all(years.map((y) => getMetrics(dataset, y)));
      // Several requested years can map to the same data year; count each once.
      return [...new Map(bodies.filter(hasData).map((b) => [b.data_year, b])).values()];
    };

    // useMetrics already reports API problems, so there's no error to show here.
    return loadWithRetry(loadResponses, {
      isReady: (responses) => responses.length > 0,
      onResult: (responses) => {
        if (responses.length > 0) setDomains(shareDomains(responses, wanted));
      },
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataset, signature]);

  return domains;
}
