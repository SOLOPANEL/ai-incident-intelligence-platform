import { useState, useEffect, useRef } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

const RANGES = ['24H', '7D', '30D', '1Y']

const ExternalLinkIcon = () => (
  <svg viewBox="0 0 16 16" width="11" height="11" fill="none">
    <path d="M7 3H3v10h10V9M10 2h4v4M14 2l-6 6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-strong)',
      borderRadius: 8,
      padding: '10px 14px',
      fontSize: 12,
    }}>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 600 }}>{label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.stroke, margin: '2px 0' }}>
          {p.name}: <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  )
}

export default function SignalChart({ data }) {
  const [activeRange, setActiveRange] = useState('7D')
  const [animated, setAnimated] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => setAnimated(true), 100)
    return () => clearTimeout(t)
  }, [])

  return (
    <div className="signal-chart-card">
      {/* Header */}
      <div className="signal-chart-header">
        <div>
          <div className="eyebrow">Signal Over Time</div>
          <div className="signal-chart-title">Incident activity</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flexDirection: 'column', alignItems: 'flex-end' }}>
          {/* Range selector */}
          <div className="range-selector">
            {RANGES.map((r) => (
              <button
                key={r}
                className={`range-btn ${activeRange === r ? 'active' : ''}`}
                onClick={() => setActiveRange(r)}
              >
                {r}
              </button>
            ))}
          </div>
          {/* Meta */}
          <div className="signal-chart-meta">
            10 total signals&nbsp;
            <ExternalLinkIcon />
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="chart-legend">
        <span className="legend-item">
          <span className="legend-dot detected" />
          Detected
        </span>
        <span className="legend-item">
          <span className="legend-dot resolved" />
          Resolved
        </span>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ left: -10, right: 10, top: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="gradDetected" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--chart-line-detected)" stopOpacity={0.25} />
              <stop offset="100%" stopColor="var(--chart-line-detected)" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradResolved" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--chart-line-resolved)" stopOpacity={0.2} />
              <stop offset="100%" stopColor="var(--chart-line-resolved)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="4 4"
            stroke="var(--border-subtle)"
            vertical={false}
          />
          <XAxis
            dataKey="day"
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
          />
          <YAxis
            axisLine={false}
            tickLine={false}
            tick={{ fill: 'var(--text-tertiary)', fontSize: 11 }}
            ticks={[0, 2, 4, 6, 8]}
            width={24}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--border-strong)', strokeWidth: 1, strokeDasharray: '4 4' }} />
          <Area
            type="monotone"
            dataKey="detected"
            stroke="var(--chart-line-detected)"
            strokeWidth={2}
            fill="url(#gradDetected)"
            dot={false}
            activeDot={{ r: 4, fill: 'var(--chart-line-detected)', stroke: 'var(--bg-card)', strokeWidth: 2 }}
            isAnimationActive={animated}
            animationDuration={800}
            animationEasing="ease-out"
          />
          <Area
            type="monotone"
            dataKey="resolved"
            stroke="var(--chart-line-resolved)"
            strokeWidth={2}
            fill="url(#gradResolved)"
            dot={false}
            activeDot={{ r: 4, fill: 'var(--chart-line-resolved)', stroke: 'var(--bg-card)', strokeWidth: 2 }}
            isAnimationActive={animated}
            animationDuration={800}
            animationEasing="ease-out"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
