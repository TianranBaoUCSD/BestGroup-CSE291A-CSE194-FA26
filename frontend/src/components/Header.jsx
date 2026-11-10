export default function Header() {
  return (
    <header className="header">
      <div className="header__titles">
        <p className="eyebrow">Bay Area, 2000–2026</p>
        <h1 className="header__title">Bay Area Housing &amp; Demographics Explorer</h1>
      </div>
      <p className="header__intro">
        Choose a dataset and a year, then click a county to zoom in and see how it has changed.
      </p>
    </header>
  );
}
