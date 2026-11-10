import { useState } from 'react';

/** Google-Maps-style floating controls drawn on top of the map. */
export default function MapOverlay({ countyOptions, onSearchPick, countyName, onGoBayArea, onRecenter, legend }) {
  const [query, setQuery] = useState('');
  const [notFound, setNotFound] = useState(false);

  const submit = (e) => {
    e.preventDefault();
    const q = query.trim().toLowerCase().replace(/\s+county$/, '');
    if (!q) return;
    const hit =
      countyOptions.find((o) => o.name.toLowerCase() === q) ??
      countyOptions.find((o) => o.name.toLowerCase().includes(q));
    setNotFound(!hit);
    if (hit) {
      onSearchPick(hit.geoid);
      setQuery(`${hit.name} County`);
    }
  };

  return (
    <>
      <div className="overlay overlay--top-left">
        <form className="search map-panel" role="search" onSubmit={submit}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6E6258" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <circle cx="11" cy="11" r="6.5" />
            <path d="m16 16 4.5 4.5" />
          </svg>
          <label htmlFor="map-search" className="sr-only">
            Search a county
          </label>
          <input
            id="map-search"
            type="search"
            list="map-search-options"
            placeholder="Search a county"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setNotFound(false);
            }}
          />
          <datalist id="map-search-options">
            {countyOptions.map((o) => (
              <option key={o.geoid} value={`${o.name} County`} />
            ))}
          </datalist>
        </form>
        {notFound && <p className="search__miss map-panel">No county matches “{query}”.</p>}

        <nav className="crumbs" aria-label="Map location">
          <button type="button" className="chip map-panel" onClick={onGoBayArea}>
            Bay Area
          </button>
          {countyName && <span className="chip chip--active">› {countyName} County</span>}
        </nav>
      </div>

      <div className="overlay overlay--recenter">
        <button type="button" className="icon-btn map-panel" onClick={onRecenter} aria-label="Recenter map">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#5F5248" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <circle cx="12" cy="12" r="6" />
            <circle cx="12" cy="12" r="1.5" fill="#5F5248" />
            <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
          </svg>
        </button>
      </div>

      <div className="overlay overlay--bottom-left">{legend}</div>
    </>
  );
}
