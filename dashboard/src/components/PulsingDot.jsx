export default function PulsingDot({ color = 'var(--success-green)', size = 8 }) {
  return (
    <span
      className="pulsing-dot-wrap"
      style={{ width: size, height: size }}
    >
      <span
        className="pulsing-dot-ring"
        style={{ background: color }}
      />
      <span
        className="pulsing-dot-core"
        style={{ background: color, width: size, height: size }}
      />
    </span>
  )
}
