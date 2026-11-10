// Shared configuration for the explorer.
// Metric keys must match backend/app/metrics_config.py.

export const YEAR_MIN = 2000;
export const YEAR_MAX = 2026;
export const YEAR_TICKS = [2000, 2005, 2010, 2015, 2020, 2026];

// Which metrics the app shows (legend dropdown + side-panel cards).
//
// A metric is either read straight from the API:
//   { key: 'median_home_value', label: 'Median home value', format: 'usd' }
// or derived as a percent of another metric (color range computed across all years):
//   { key: 'asian_pct', label: 'Asian alone', format: 'pct',
//     share: { count: 'asian_population', total: 'population' } }
// The count and total keys must be metrics the API returns for that dataset.
export const DATASETS = {
  housing: {
    label: 'Housing',
    palette: 'reds',
    defaultMetric: 'median_home_value',
    metrics: [
      { key: 'median_home_value', label: 'Median home value', format: 'usd' },
      { key: 'median_gross_rent', label: 'Median gross rent', format: 'usd' },
      { key: 'owner_occupied_pct', label: 'Homeownership rate', format: 'pct' },
      { key: 'vacancy_rate_pct', label: 'Vacancy rate', format: 'pct' },
    ],
  },
  demographics: {
    label: 'Demographics',
    palette: 'coffee',
    defaultMetric: 'population',
    metrics: [
      { key: 'population', label: 'Population', format: 'int' },
      { key: 'median_household_income', label: 'Median household income', format: 'usd' },
      { key: 'median_age', label: 'Median age', format: 'years' },
      { key: 'bachelors_pct', label: "Bachelor's degree or higher", format: 'pct' },
    ],
  },
};

// Initial map view: the nine-county Bay Area.
export const BAY_BOUNDS = [
  [36.89, -123.55],
  [38.87, -121.2],
];

// CARTO "Voyager" tiles: a clean, Google-Maps-like basemap (free, attribution required).
// Labels are a separate layer so they can sit above the heatmap.
export const TILE_BASE = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png';
export const TILE_LABELS = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png';
export const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
