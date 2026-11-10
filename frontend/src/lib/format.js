const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
const usdCompact = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  notation: 'compact',
  maximumFractionDigits: 1,
});
const int = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });

/** Which year's data is showing. The API uses the latest year at or before the one selected. */
export function dataYearNote(year, dataYear) {
  if (dataYear === year) return `Showing ${dataYear} data.`;
  if (dataYear < year) return `Showing ${dataYear} data, the latest available as of ${year}.`;
  return `Showing ${dataYear} data, the earliest available.`;
}

export function formatValue(value, format, { compact = false } = {}) {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  switch (format) {
    case 'usd':
      return compact ? usdCompact.format(value) : usd.format(value);
    case 'pct':
      return `${value.toFixed(1)}%`;
    case 'years':
      return `${value.toFixed(1)} yrs`;
    case 'int':
    default:
      return int.format(value);
  }
}
