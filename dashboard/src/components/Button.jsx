export default function Button({
  children,
  variant = 'primary',
  loading = false,
  icon: Icon,
  onClick,
  type = 'button',
  style,
}) {
  return (
    <button
      type={type}
      className={`btn btn-${variant}`}
      onClick={onClick}
      disabled={loading}
      style={style}
    >
      {Icon && (
        <span className={loading ? 'btn-icon-spin' : ''} style={{ display: 'flex' }}>
          <Icon />
        </span>
      )}
      {children}
    </button>
  )
}
