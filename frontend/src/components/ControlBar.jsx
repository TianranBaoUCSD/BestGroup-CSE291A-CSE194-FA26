import DatasetToggle from './DatasetToggle.jsx';
import YearControl from './YearControl.jsx';

export default function ControlBar({ dataset, onDatasetChange, year, years, yearsReady, onYearChange, playing, onTogglePlay }) {
  return (
    <section className="card controls" aria-label="Dataset and year">
      <DatasetToggle value={dataset} onChange={onDatasetChange} />
      <YearControl
        year={year}
        years={years}
        ready={yearsReady}
        onChange={onYearChange}
        playing={playing}
        onTogglePlay={onTogglePlay}
      />
    </section>
  );
}
