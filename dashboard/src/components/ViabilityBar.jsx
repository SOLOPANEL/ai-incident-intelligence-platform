function getViabilityColor(pct) {
  if (pct >= 80) return 'var(--success-green)'
  if (pct >= 60) return '#a8e0a0'
  if (pct >= 40) return 'var(--severity-medium-text)'
  return 'var(--severity-high-text)'
}

export default function ViabilityBar({ percent }) {
  const color = getViabilityColor(percent)
  return (
    <div className="viability-wrap">
      <span className="viability-pct">{percent}%</span>
      <div className="viability-track">
        <div
          className="viability-fill"
          style={{ width: `${percent}%`, background: color }}
        />
      </div>
    </div>
  )
}
