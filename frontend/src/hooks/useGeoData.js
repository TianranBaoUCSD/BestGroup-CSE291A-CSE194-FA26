import { useEffect, useState } from 'react';
import { fetchGeoJSON } from '../lib/api.js';

/** Loads the nine county outlines from /public/data. */
export function useGeoData() {
  const [geo, setGeo] = useState({ counties: null, error: null });

  useEffect(() => {
    const ctrl = new AbortController();
    fetchGeoJSON('/data/counties.geojson', ctrl.signal)
      .then((counties) => setGeo({ counties, error: null }))
      .catch((err) => {
        if (err.name !== 'AbortError') setGeo({ counties: null, error: err.message });
      });
    return () => ctrl.abort();
  }, []);

  return geo;
}
