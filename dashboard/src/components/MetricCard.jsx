const TrendUpIcon = () => (
  <svg viewBox="0 0 16 16" width="12" height="12" fill="none">
    <path d="M2 12l4-4 3 3 5-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    <path d="M11 5h3v3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

export default function MetricCard({
  icon: IconCmp,
  iconVariant = 'violet',
  label,
  value,
  deltaPercent,
  deltaLabel,
  needsReview,
  animationDelay = 0,
}) {
  return (
    <div
      className="metric-card"
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      {/* Top row: icon + label */}
      <div className="metric-card-top">
        <div className={`metric-icon-tile ${iconVariant}`}>
          {IconCmp && <IconCmp />}
        </div>
        <span className="metric-label">{label}</span>
      </div>

      {/* Big stat */}
      <div className="metric-value">{value}</div>

      {/* Delta row */}
      {deltaPercent !== undefined && (
        <div className="metric-delta-row">
          <span className="metric-delta-pct">
            <TrendUpIcon />
            {deltaPercent}
          </span>
          {deltaLabel && (
            <span className="metric-delta-label">{deltaLabel}</span>
          )}
        </div>
      )}

      {needsReview && (
        <div className="metric-needs-review">⚠ Needs review</div>
      )}
    </div>
  )
}
