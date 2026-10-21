import { useState } from 'react'
import SeverityBadge from './SeverityBadge'
import StateDot from './StateDot'
import ViabilityBar from './ViabilityBar'
import OwnerChip from './OwnerChip'

const SparkleIcon = () => (
  <svg viewBox="0 0 16 16" width="14" height="14" fill="none">
    <path d="M8 1l1.5 4.5L14 7l-4.5 1.5L8 13l-1.5-4.5L2 7l4.5-1.5L8 1Z" fill="currentColor" opacity="0.9"/>
    <path d="M12.5 1l.75 2.25L15.5 4l-2.25.75L12.5 7l-.75-2.25L9.5 4l2.25-.75L12.5 1Z" fill="currentColor" opacity="0.5"/>
  </svg>
)

const LinkIcon = () => (
  <svg viewBox="0 0 16 16" width="13" height="13" fill="none">
    <path d="M6.5 9.5a3.5 3.5 0 0 0 5 0l2-2a3.5 3.5 0 0 0-5-5l-1 1" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
    <path d="M9.5 6.5a3.5 3.5 0 0 0-5 0l-2 2a3.5 3.5 0 0 0 5 5l1-1" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
  </svg>
)

const ChevronIcon = ({ expanded }) => (
  <svg
    viewBox="0 0 16 16"
    width="12"
    height="12"
    fill="none"
    className={`expand-chevron ${expanded ? 'expanded' : ''}`}
  >
    <path d="M6 4l4 4-4 4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

export default function IncidentRow({ incident }) {
  const { id, title, vendor, severity, state, viability, ownerInitials, ownerName, ageLabel, explanation, matchedIncident } = incident
  const [expanded, setExpanded] = useState(false)

  const hasDetails = explanation || matchedIncident

  return (
    <>
      <tr
        className={`incident-row ${hasDetails ? 'clickable' : ''} ${expanded ? 'row-expanded' : ''}`}
        onClick={() => hasDetails && setExpanded(!expanded)}
      >
        {/* Severity accent bar */}
        <td className="severity-bar-cell">
          <div className={`severity-bar ${severity}`} />
        </td>

        {/* Incident title + meta */}
        <td>
          <div className="incident-title-wrap">
            {hasDetails && <ChevronIcon expanded={expanded} />}
            <div>
              <div className="incident-title">{title}</div>
              <div className="incident-meta">{id} · {vendor}</div>
            </div>
          </div>
        </td>

        {/* Severity badge */}
        <td>
          <SeverityBadge level={severity} />
        </td>

        {/* State dot */}
        <td>
          <StateDot state={state} />
        </td>

        {/* Viability bar */}
        <td>
          <ViabilityBar percent={viability} />
        </td>

        {/* Owner chip */}
        <td>
          <OwnerChip initials={ownerInitials} name={ownerName} />
        </td>

        {/* Age */}
        <td>
          <span className="age-label">{ageLabel}</span>
        </td>
      </tr>

      {/* Expandable detail panel */}
      {hasDetails && (
        <tr className={`incident-detail-row ${expanded ? 'open' : ''}`}>
          <td colSpan={7} style={{ padding: 0, border: 'none' }}>
            <div className="detail-collapse-wrapper">
              <div className="incident-detail-panel">
                {explanation && (
                  <div className="detail-section">
                    <div className="detail-section-header">
                      <span className="detail-icon ai-icon"><SparkleIcon /></span>
                      <span className="eyebrow">AI Analysis</span>
                    </div>
                    <p className="detail-text">{explanation}</p>
                  </div>
                )}

                {matchedIncident && (
                  <div className="detail-section">
                    <div className="detail-section-header">
                      <span className="detail-icon link-icon"><LinkIcon /></span>
                      <span className="eyebrow">Matched Incident</span>
                    </div>
                    <p className="detail-text matched">{matchedIncident}</p>
                  </div>
                )}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}
