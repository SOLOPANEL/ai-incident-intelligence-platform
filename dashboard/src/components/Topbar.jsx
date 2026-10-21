const HelpIcon = () => (
  <svg viewBox="0 0 20 20" width="14" height="14" fill="none">
    <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.4"/>
    <path d="M8 8c0-1.1.9-2 2-2s2 .9 2 2c0 .8-.4 1.4-1 1.8L10 10.5V12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    <circle cx="10" cy="14" r="0.7" fill="currentColor"/>
  </svg>
)

const BellIcon = () => (
  <svg viewBox="0 0 20 20" width="14" height="14" fill="none">
    <path d="M10 2a6 6 0 0 0-6 6v3l-1.5 2h15L16 11V8a6 6 0 0 0-6-6Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
    <path d="M8.5 16.5a1.5 1.5 0 0 0 3 0" stroke="currentColor" strokeWidth="1.4"/>
  </svg>
)

const ChevronDownIcon = () => (
  <svg viewBox="0 0 12 12" width="10" height="10" fill="none">
    <path d="M3 4.5l3 3 3-3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

export default function Topbar() {
  return (
    <header className="topbar">
      {/* Breadcrumb */}
      <div className="topbar-breadcrumb">
        <span className="breadcrumb-parent">Operations</span>
        <span className="breadcrumb-sep">›</span>
        <span className="breadcrumb-current">Overview</span>
      </div>

    
    </header>
  )
}
