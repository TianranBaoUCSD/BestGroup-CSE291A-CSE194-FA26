import { formatValue } from '../lib/format.js';

const GROUPS = [
  { key: 'white_population', label: 'White alone', color: '#8b5e3c' },
  { key: 'black_population', label: 'Black or African American alone', color: '#c27a42' },
  { key: 'native_american_population', label: 'American Indian and Alaska Native alone', color: '#d8a85e' },
  { key: 'asian_population', label: 'Asian alone', color: '#668c87' },
  { key: 'pacific_islander_population', label: 'Native Hawaiian and Other Pacific Islander alone', color: '#54718b' },
  { key: 'other_race_population', label: 'Some other race alone', color: '#a77991' },
  { key: 'two_or_more_races_population', label: 'Two or more races', color: '#9b8c6b' },
];

function slicePath(start, end) {
  const radius = 92;
  const center = 100;
  const point = (angle) => [center + radius * Math.cos(angle), center + radius * Math.sin(angle)];
  const [startX, startY] = point(start);
  const [endX, endY] = point(end);
  const largeArc = end - start > Math.PI ? 1 : 0;
  return `M ${center} ${center} L ${startX} ${startY} A ${radius} ${radius} 0 ${largeArc} 1 ${endX} ${endY} Z`;
}

export default function RaceBreakdown({ countyName, countyValues }) {
  const total = countyValues?.population;
  const hasData =
    Number.isFinite(total) &&
    total > 0 &&
    GROUPS.every(({ key }) => Number.isFinite(countyValues[key]) && countyValues[key] >= 0);

  if (!hasData) {
    return (
      <section className="card race-card" aria-labelledby="race-breakdown-title">
        <h3 id="race-breakdown-title" className="race-card__title">Race breakdown</h3>
        <p className="race-card__empty">Race data isn’t available for this county and year.</p>
      </section>
    );
  }

  let angle = -Math.PI / 2;
  const slices = GROUPS.map((group) => {
    const count = countyValues[group.key];
    const start = angle;
    angle += (count / total) * Math.PI * 2;
    return { ...group, count, start, end: angle, share: (count / total) * 100 };
  });

  return (
    <section className="card race-card" aria-labelledby="race-breakdown-title">
      <h3 id="race-breakdown-title" className="race-card__title">Race breakdown</h3>
      <div className="race-card__content">
        <svg
          className="race-card__chart"
          viewBox="0 0 200 200"
          role="img"
          aria-label={`Race breakdown of ${formatValue(total, 'int')} people in ${countyName} County`}
        >
          {slices.filter((slice) => slice.count > 0).map((slice) =>
            slice.share >= 100 ? (
              <circle key={slice.key} cx="100" cy="100" r="92" fill={slice.color} stroke="var(--card)" strokeWidth="2" />
            ) : (
              <path
                key={slice.key}
                d={slicePath(slice.start, slice.end)}
                fill={slice.color}
                stroke="var(--card)"
                strokeWidth="2"
              />
            ),
          )}
        </svg>
        <ul className="race-card__legend">
          {slices.map((slice) => (
            <li className="race-card__item" key={slice.key}>
              <span className="race-card__swatch" style={{ backgroundColor: slice.color }} aria-hidden="true" />
              <span className="race-card__label">{slice.label}</span>
              <span className="race-card__value">
                {slice.share.toFixed(1)}% <span className="race-card__count">({formatValue(slice.count, 'int')})</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
      <p className="race-card__note">Race categories shown; Hispanic or Latino origin is not distinguished.</p>
    </section>
  );
}
