// Read the exported API snapshot from the site's static files.
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function getJSON(path, signal) {
  let res;
  try {
    res = await fetch(`${import.meta.env.BASE_URL}${path}`, { signal });
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    throw new ApiError('Could not load the exported data', 0);
  }
  if (!res.ok) throw new ApiError(`Could not load exported data (${res.status})`, res.status);
  try {
    return await res.json();
  } catch {
    throw new ApiError('The exported data is not valid JSON', res.status);
  }
}

export function fetchMetrics(dataset, year, signal) {
  return getJSON(`data/api/metrics/${encodeURIComponent(dataset)}/${encodeURIComponent(year)}.json`, signal);
}

export function fetchMetadata(signal) {
  return getJSON('data/api/metadata.json', signal);
}

export function fetchGeoJSON(path, signal) {
  return getJSON(path.replace(/^\//, ''), signal);
}
