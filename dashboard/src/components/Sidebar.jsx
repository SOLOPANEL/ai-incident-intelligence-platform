import PulsingDot from './PulsingDot'

/* ---------- Inline SVG icons ---------- */
const Icons = {
  overview: () => (
    <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
      <rect x="2" y="2" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.4"/>
      <rect x="11" y="2" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.4"/>
      <rect x="2" y="11" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.4"/>
      <rect x="11" y="11" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.4"/>
    </svg>
  ),
  charts: () => (
    <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
      <path d="M3 17V9M9 17V3M15 17v-5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  ),
  pipeline: () => (
    <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
      <circle cx="4" cy="10" r="2" stroke="currentColor" strokeWidth="1.4"/>
      <circle cx="16" cy="10" r="2" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M6 10h8" stroke="currentColor" strokeWidth="1.4"/>
    </svg>
  ),
  anomalies: () => (
    <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
      <path d="M10 2 2 17h16L10 2Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
      <path d="M10 8v4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
      <circle cx="10" cy="14.2" r="0.9" fill="currentColor"/>
    </svg>
  ),
  memory: () => (
    <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
      <ellipse cx="10" cy="5" rx="7" ry="2.5" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M3 5v10c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5V5" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M3 10c0 1.4 3.1 2.5 7 2.5s7-1.1 7-2.5" stroke="currentColor" strokeWidth="1.4"/>
    </svg>
  ),
  logoMark: () => (
    <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
      <path d="M4 10h12M10 4v12" stroke="white" strokeWidth="2" strokeLinecap="round"/>
      <circle cx="10" cy="10" r="3" stroke="white" strokeWidth="1.4"/>
    </svg>
  ),
}

const MONITOR_NAV = [
  { id: 'overview',  label: 'Overview',         icon: 'overview' },
  { id: 'charts',   label: 'Charts',            icon: 'charts' },
  { id: 'pipeline', label: 'Pipeline',          icon: 'pipeline' },
  { id: 'anomalies',label: 'Anomalies',         icon: 'anomalies' },
]

const WORKSPACE_NAV = [
  { id: 'memory',   label: 'Memory & feedback', icon: 'memory', badge: '8' },
]

export default function Sidebar({ activeSection, onNavClick }) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-tile">
          <Icons.logoMark />
        </div>
        <span className="sidebar-wordmark">
          <span className="wm-incident">incident</span>
          <span className="wm-intelligent">-intelligent</span>
        </span>
      </div>

      {/* Workspace Switcher */}
      <div className="sidebar-workspace" role="button" tabIndex={0}>
        <div className="ws-avatar">AC</div>
        <div className="ws-info">
          <div className="ws-name">AcmeCorp</div>
          <div className="ws-sub">Operations workspace</div>
        </div>
        <span className="ws-chevron">›</span>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        {/* MONITOR group */}
        <div className="sidebar-nav-group">
          <span className="sidebar-group-label">Monitor</span>
          {MONITOR_NAV.map((item) => {
            const IconCmp = Icons[item.icon]
            return (
              <button
                key={item.id}
                className={`nav-item ${activeSection === item.id ? 'active' : ''}`}
                onClick={() => onNavClick(item.id)}
                title={item.label}
              >
                <IconCmp />
                <span>{item.label}</span>
              </button>
            )
          })}
        </div>

        {/* WORKSPACE group */}
        <div className="sidebar-nav-group">
          <span className="sidebar-group-label">Workspace</span>
          {WORKSPACE_NAV.map((item) => {
            const IconCmp = Icons[item.icon]
            return (
              <button
                key={item.id}
                className={`nav-item ${activeSection === item.id ? 'active' : ''}`}
                onClick={() => onNavClick(item.id)}
                title={item.label}
              >
                <IconCmp />
                <span>{item.label}</span>
                {item.badge && (
                  <span className="nav-item-badge">{item.badge}</span>
                )}
              </button>
            )
          })}
        </div>
      </nav>

      {/* Bottom */}
      <div className="sidebar-bottom">
        {/* Live status */}
        <div className="sidebar-live-status">
          <span className="sidebar-live-dot">
            <PulsingDot />
          </span>
          <div className="sidebar-live-text">
            <span className="sidebar-live-label">Live data stream</span>
            <span className="sidebar-live-sub">Last updated just now</span>
          </div>
        </div>

        {/* User */}
        <div className="sidebar-user" role="button" tabIndex={0}>
          <div className="user-avatar">JD</div>
          <div className="user-info">
            <div className="user-name">Jordan Davis</div>
            <div className="user-role">Incident lead</div>
          </div>
          <span className="user-menu">···</span>
        </div>
      </div>
    </aside>
  )
}
