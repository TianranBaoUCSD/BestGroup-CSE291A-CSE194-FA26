import { useCallback, useEffect, useMemo, useState } from 'react';
import Header from './components/Header.jsx';
import ControlBar from './components/ControlBar.jsx';
import BayMap from './components/BayMap.jsx';
import MapOverlay from './components/MapOverlay.jsx';
import Legend from './components/Legend.jsx';
import DetailsPanel from './components/DetailsPanel.jsx';
import { BAY_BOUNDS, DATASETS, YEAR_MIN } from './constants.js';
import { useAvailableYears } from './hooks/useAvailableYears.js';
import { useGeoData } from './hooks/useGeoData.js';
import { useMetrics } from './hooks/useMetrics.js';
import { usePlayback } from './hooks/usePlayback.js';
import { useShareDomains } from './hooks/useShareDomains.js';
import { makeColorScale } from './lib/colors.js';
import { featureBounds } from './lib/geo.js';
import { deriveValues } from './lib/metrics.js';
import { pickYear } from './lib/years.js';

export default function App() {
  const [year, setYear] = useState(YEAR_MIN);
  const [dataset, setDataset] = useState('housing');
  const [colorMetric, setColorMetric] = useState({
    housing: DATASETS.housing.defaultMetric,
    demographics: DATASETS.demographics.defaultMetric,
  });
  const [countyId, setCountyId] = useState(null);
  const [fitTarget, setFitTarget] = useState(null);

  const geo = useGeoData();
  const metrics = useMetrics(dataset, year);

  const def = DATASETS[dataset];
  const available = useAvailableYears(dataset, def.metrics);
  const yearsReady = available.status === 'ok';

  // Metrics with no years of data are hidden once we know which years exist.
  const visibleMetrics = useMemo(
    () => (yearsReady ? def.metrics.filter((m) => available.years[m.key]?.length > 0) : def.metrics),
    [yearsReady, available.years, def.metrics],
  );
  const metric = visibleMetrics.find((m) => m.key === colorMetric[dataset]) ?? visibleMetrics[0] ?? def.metrics[0];

  // The slider only offers the years the map's metric has data for.
  const years = useMemo(
    () => (yearsReady ? (available.years[metric.key] ?? []) : []),
    [yearsReady, available.years, metric.key],
  );
  useEffect(() => {
    setYear((y) => pickYear(y, years)); // not available for this metric -> its earliest year
  }, [years]);

  const { playing, toggle: togglePlay, stop } = usePlayback(year, setYear, years);
  const shareRanges = useShareDomains(dataset, def.metrics);

  // values: { "06001": { metric: value } }, with percent-of-population metrics added.
  const values = useMemo(() => deriveValues(metrics.data?.values ?? null, def.metrics), [metrics.data, def.metrics]);
  const domain = metric.share ? (shareRanges[metric.key] ?? null) : (metrics.data?.domains?.[metric.key] ?? null);
  const colorScale = useMemo(() => makeColorScale(def.palette, domain), [def.palette, domain]);
  const hasValues = Boolean(values && Object.values(values).some((v) => v[metric.key] != null));

  // ---- Counties -------------------------------------------------------------
  const countyFeatures = useMemo(() => geo.counties?.features ?? [], [geo.counties]);
  const county = countyFeatures.find((f) => f.properties.geoid === countyId) ?? null;
  const countyOptions = useMemo(
    () =>
      countyFeatures
        .map((f) => ({ geoid: f.properties.geoid, name: f.properties.name }))
        .sort((a, b) => a.name.localeCompare(b.name)),
    [countyFeatures],
  );

  const pickCounty = useCallback(
    (geoid) => {
      const f = countyFeatures.find((c) => c.properties.geoid === geoid);
      setCountyId(geoid);
      if (f) setFitTarget({ bounds: featureBounds(f) });
    },
    [countyFeatures],
  );

  const goBayArea = () => {
    setCountyId(null);
    setFitTarget({ bounds: BAY_BOUNDS });
  };

  const recenter = () => setFitTarget({ bounds: county ? featureBounds(county) : BAY_BOUNDS });

  return (
    <div className="page">
      <div className="container">
        <Header />

        <ControlBar
          dataset={dataset}
          onDatasetChange={setDataset}
          year={year}
          years={years}
          yearsReady={yearsReady}
          onYearChange={(y) => {
            stop();
            setYear(y);
          }}
          playing={playing}
          onTogglePlay={togglePlay}
        />

        {geo.error && <p className="error">Could not load the county map: {geo.error}</p>}

        <div className="main">
          <BayMap
            counties={geo.counties}
            values={values}
            metric={metric}
            colorScale={colorScale}
            countyId={countyId}
            onPickCounty={pickCounty}
            fitTarget={fitTarget}
          >
            <MapOverlay
              countyOptions={countyOptions}
              onSearchPick={pickCounty}
              countyName={county?.properties.name ?? null}
              onGoBayArea={goBayArea}
              onRecenter={recenter}
              legend={
                <Legend
                  dataset={dataset}
                  metrics={visibleMetrics}
                  metric={metric}
                  onMetricChange={(key) => setColorMetric((m) => ({ ...m, [dataset]: key }))}
                  domain={domain}
                  hasValues={hasValues}
                  year={year}
                  dataYear={metrics.data?.data_year ?? null}
                  status={metrics.status}
                />
              }
            />
          </BayMap>

          <DetailsPanel
            dataset={dataset}
            metrics={visibleMetrics}
            year={year}
            dataYear={metrics.data?.data_year ?? null}
            status={metrics.status}
            countyValues={countyId ? values?.[countyId] : null}
            countyName={county?.properties.name ?? null}
            counties={countyOptions.map((c) => ({ ...c, active: c.geoid === countyId, onClick: () => pickCounty(c.geoid) }))}
            onBack={goBayArea}
          />
        </div>
      </div>
    </div>
  );
}
