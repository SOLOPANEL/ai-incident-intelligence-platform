export default function OwnerChip({ initials, name }) {
  return (
    <span className="owner-chip">
      <span className="owner-avatar">{initials}</span>
      <span className="owner-name">{name}</span>
    </span>
  )
}
