import { useState } from 'react'
import PulsingDot from './PulsingDot'
import Button from './Button'

const RefreshIcon = () => (
  <svg viewBox="0 0 20 20" width="14" height="14" fill="none">
    <path d="M16 10a6 6 0 1 1-1.8-4.3M16 3v4h-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const SparkleIcon = () => (
  <svg viewBox="0 0 24 24" width="22" height="22" fill="none">
    <path d="M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4L12 2Z" fill="var(--accent-primary)" opacity="0.9"/>
    <path d="M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4L12 2Z" stroke="var(--accent-primary)" strokeWidth="0.5"/>
  </svg>
)

export default function DashboardHeader({ onRefresh, isRefreshing }) {
  const today = new Date()
  const dateLabel = today.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).toUpperCase()

  return (
    <div className="dashboard-header">
      <div className="dh-left">
        {/* Eyebrow */}
        <div className="dh-eyebrow">
          <PulsingDot />
          <span className="dh-eyebrow-text">
            System Intelligence / {dateLabel}
          </span>
        </div>

        {/* H1 */}
        <h1 className="dh-h1">
          Good morning, Jordan
          <SparkleIcon />
        </h1>

        {/* Subtext */}
        <p className="dh-sub">
          Here's what needs your attention across the procurement network.
        </p>
      </div>

      {/* Refresh button */}
      <Button
        variant="primary"
        icon={RefreshIcon}
        loading={isRefreshing}
        onClick={onRefresh}
      >
        Refresh feed
      </Button>
    </div>
  )
}
