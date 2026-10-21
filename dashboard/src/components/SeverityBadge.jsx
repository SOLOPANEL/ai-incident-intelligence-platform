export default function SeverityBadge({ level }) {
  return (
    <span className={`severity-badge ${level}`}>
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </span>
  )
}
