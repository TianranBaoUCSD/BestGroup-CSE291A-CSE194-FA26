import { useCallback, useEffect, useRef } from 'react';
import { GeoJSON, MapContainer, Pane, TileLayer, ZoomControl, useMap } from 'react-leaflet';
import { BAY_BOUNDS, TILE_ATTRIBUTION, TILE_BASE, TILE_LABELS } from '../constants.js';
import { NO_DATA_COLOR } from '../lib/colors.js';
import { formatValue } from '../lib/format.js';
import { escapeHtml } from '../lib/geo.js';

const OUTLINE = '#6B4423';
const OUTLINE_HOVER = '#2A1C14';

/** Flies the map to `target.bounds` whenever a new target object is passed. */
function FitBounds({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target?.bounds) map.flyToBounds(target.bounds, { padding: [40, 40], duration: 0.6 });
  }, [map, target]);
  return null;
}

/**
 * The nine counties, each shaded by its value for `metric` (the heatmap).
 * values: { "06001": { median_home_value: 950000, … } } from GET /api/metrics.
 */
export default function BayMap({ counties, values, metric, colorScale, countyId, onPickCounty, fitTarget, children }) {
  const layerRef = useRef(null);

  const styleCounty = useCallback(
    (feature) => {
      const geoid = feature.properties.geoid;
      const v = values?.[geoid]?.[metric.key];
      const selected = geoid === countyId;
      return {
        fillColor: v == null || !colorScale ? NO_DATA_COLOR : colorScale(v),
        fillOpacity: selected ? 0.85 : countyId ? 0.3 : 0.7,
        color: OUTLINE,
        weight: selected ? 3.5 : 1.6,
        opacity: 0.9,
      };
    },
    [values, metric, colorScale, countyId],
  );

  const tooltipFor = useCallback(
    (feature) => {
      const p = feature.properties;
      const v = values?.[p.geoid]?.[metric.key];
      return `<strong>${escapeHtml(p.name)} County</strong><br/>${escapeHtml(metric.label)}: ${escapeHtml(
        formatValue(v, metric.format),
      )}`;
    },
    [values, metric],
  );

  // Leaflet layers are created once; keep handlers pointed at the latest props.
  const latest = useRef({});
  latest.current = { onPickCounty, styleCounty };

  const onEachCounty = useCallback((feature, layer) => {
    layer.bindTooltip('', { sticky: true, direction: 'top', className: 'map-tip', opacity: 1 });
    layer.on({
      click: () => latest.current.onPickCounty(feature.properties.geoid),
      mouseover: () => {
        layer.setStyle({ weight: 3, color: OUTLINE_HOVER });
        layer.bringToFront();
      },
      mouseout: () => layer.setStyle(latest.current.styleCounty(feature)),
    });
  }, []);

  // Restyle in place when data, metric, year or selection changes (no layer rebuild).
  useEffect(() => {
    layerRef.current?.eachLayer((layer) => {
      layer.setStyle(styleCounty(layer.feature));
      layer.setTooltipContent(tooltipFor(layer.feature));
      if (layer.feature.properties.geoid === countyId) layer.bringToFront();
    });
  }, [styleCounty, tooltipFor, countyId, counties]);

  return (
    <section className="map-wrap" aria-label="Map of Bay Area counties">
      <MapContainer bounds={BAY_BOUNDS} zoomControl={false} className="map" scrollWheelZoom>
        <TileLayer url={TILE_BASE} attribution={TILE_ATTRIBUTION} subdomains="abcd" />
        {counties && <GeoJSON ref={layerRef} data={counties} style={styleCounty} onEachFeature={onEachCounty} />}
        <Pane name="labels" style={{ zIndex: 430, pointerEvents: 'none' }}>
          <TileLayer url={TILE_LABELS} subdomains="abcd" />
        </Pane>
        <ZoomControl position="bottomright" />
        <FitBounds target={fitTarget} />
      </MapContainer>
      {children}
    </section>
  );
}
