import { scaleSequential } from 'd3-scale';
import { interpolateReds } from 'd3-scale-chromatic';
import { interpolateRgbBasis } from 'd3-interpolate';

export const NO_DATA_COLOR = '#D9D3CA';

// Housing: red heatmap. The lightest 12% of d3's Reds is skipped so low values
// still read as "red" on top of the basemap.
const reds = (t) => interpolateReds(0.12 + 0.88 * t);

// Demographics: cappuccino browns.
const coffee = interpolateRgbBasis(['#F3E6D6', '#E0C3A0', '#C69C72', '#9C6B45', '#6B4423', '#4B3324']);

export const PALETTES = { reds, coffee };

/** Build a color scale for a metric's [min, max] domain, or null if there's no data. */
export function makeColorScale(paletteName, domain) {
  if (!domain || domain.length !== 2 || domain.some((d) => d === null || d === undefined)) return null;
  const [lo, hi] = domain;
  const interp = PALETTES[paletteName] ?? reds;
  return scaleSequential(interp).domain(lo === hi ? [lo, lo + 1] : [lo, hi]).clamp(true);
}

/** CSS gradient string for a legend bar. */
export function paletteGradient(paletteName, stops = 7) {
  const interp = PALETTES[paletteName] ?? reds;
  const colors = Array.from({ length: stops }, (_, i) => interp(i / (stops - 1)));
  return `linear-gradient(90deg, ${colors.join(', ')})`;
}
