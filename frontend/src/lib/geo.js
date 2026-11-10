/** [[south, west], [north, east]] bounds of a GeoJSON feature, for Leaflet's fitBounds. */
export function featureBounds(feature) {
  let minLat = Infinity;
  let minLon = Infinity;
  let maxLat = -Infinity;
  let maxLon = -Infinity;
  const walk = (coords) => {
    if (typeof coords[0] === 'number') {
      const [lon, lat] = coords;
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
    } else {
      coords.forEach(walk);
    }
  };
  walk(feature.geometry.coordinates);
  return [
    [minLat, minLon],
    [maxLat, maxLon],
  ];
}

export function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}
