const STATE_CLASS = {
  'Open': 'open',
  'Investigating': 'investigating',
  'Mitigated': 'mitigated',
  'Resolved': 'resolved',
  'Pending Review': 'pending',
}

export default function StateDot({ state }) {
  const cls = STATE_CLASS[state] || 'open'
  return (
    <span className="state-dot-wrap">
      <span className={`state-dot ${cls}`} />
      <span className="state-label">{state}</span>
    </span>
  )
}
