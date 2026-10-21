import { useState, useMemo } from 'react'
import IncidentRow from './IncidentRow'
import Button from './Button'
import PulsingDot from './PulsingDot'

const SearchIcon = () => (
  <svg viewBox="0 0 20 20" width="14" height="14" fill="none">
    <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" strokeWidth="1.4"/>
    <path d="m17 17-3.5-3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
  </svg>
)

const FilterIcon = () => (
  <svg viewBox="0 0 20 20" width="14" height="14" fill="none">
    <path d="M3 5h14M6 10h8M9 15h2" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
  </svg>
)

const ShieldIcon = () => (
  <svg viewBox="0 0 20 20" width="14" height="14" fill="none">
    <path d="M10 2l7 3v5c0 4-3 7-7 8-4-1-7-4-7-8V5l7-3Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
    <path d="M7 10l2 2 4-4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const SEVERITY_OPTIONS = ['All', 'Critical', 'High', 'Medium', 'Low']
const STATE_OPTIONS = ['All', 'Open', 'Investigating', 'Mitigated', 'Resolved', 'Pending Review']

export default function IncidentTable({ incidents, healthIndex = '84.2' }) {
  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState('All')
  const [stateFilter, setStateFilter] = useState('All')

  const filtered = useMemo(() => {
    return incidents.filter((inc) => {
      const matchesSeverity = severityFilter === 'All' || inc.severity === severityFilter.toLowerCase()
      const matchesState = stateFilter === 'All' || inc.state === stateFilter
      const q = search.toLowerCase().trim()
      const matchesSearch = !q ||
        inc.title.toLowerCase().includes(q) ||
        inc.vendor.toLowerCase().includes(q) ||
        inc.id.toLowerCase().includes(q)
      return matchesSeverity && matchesState && matchesSearch
    })
  }, [incidents, search, severityFilter, stateFilter])

  return (
    <div className="queue-card">
      {/* Header */}
      <div className="queue-header">
        <div className="queue-title-row">
          <div className="eyebrow" style={{ marginRight: 4 }}>Live Queue</div>
          <span className="queue-title">Recent incidents</span>
          <span className="queue-count-badge">{incidents.length}</span>
        </div>

        <div className="queue-controls">
          {/* Search */}
          <label className="queue-search">
            <SearchIcon />
            <input
              type="text"
              placeholder="Search incidents, vendors..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search incidents"
            />
          </label>

          {/* Severity filter */}
          <select
            className="queue-select"
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            aria-label="Filter by severity"
          >
            {SEVERITY_OPTIONS.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>

          {/* State filter */}
          <select
            className="queue-select"
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            aria-label="Filter by state"
          >
            {STATE_OPTIONS.map((o) => (
              <option key={o} value={o}>{o}</option>
            ))}
          </select>

          {/* Filter button */}
          <Button variant="primary" icon={FilterIcon} style={{ padding: '8px 14px', fontSize: 13 }}>
            Filter
          </Button>
        </div>
      </div>

      {/* Table */}
      <div className="queue-table-wrap">
        <table className="queue-table">
          <thead>
            <tr>
              <th style={{ width: 4, padding: 0 }} />
              <th>Incident</th>
              <th>Severity</th>
              <th>State</th>
              <th>Viability</th>
              <th>Owner</th>
              <th>Age</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length > 0 ? (
              filtered.map((inc) => (
                <IncidentRow key={inc.id} incident={inc} />
              ))
            ) : (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '32px 0', color: 'var(--text-tertiary)', fontSize: 14 }}>
                  No incidents match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="queue-footer">
        <div className="queue-footer-left">
          <span className="health-shield"><ShieldIcon /></span>
          <span className="health-label">Procurement health index</span>
          <span className="health-value">{healthIndex}</span>
        </div>
        <div className="queue-footer-right">
          <span className="all-systems">All systems operational</span>
          <PulsingDot size={7} />
        </div>
      </div>
    </div>
  )
}
