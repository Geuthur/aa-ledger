interface ExtractorProgressProps {
  progress: number;
}

function ExtractorProgress({ progress }: ExtractorProgressProps) {
  const percent = Math.min(100, Math.max(0, progress));

  return (
    <div className="lg-progress-container">
      <div
        className="lg-progress-track"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <div className="lg-progress-fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="lg-progress-label">{percent.toFixed(1)}%</div>
    </div>
  );
}

export default ExtractorProgress;
