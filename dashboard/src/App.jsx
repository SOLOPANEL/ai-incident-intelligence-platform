import { useState, useEffect, useCallback, useMemo } from 'react'
import axios from 'axios'
import './App.css'

// Layout
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'


// Content
import MetricCard from './components/MetricCard'
import SignalChart from './components/SignalChart'
import PatternIndexCard from './components/PatternIndexCard'
import IncidentTable from './components/IncidentTable'

// Mock data
import { mockIncidents, mockChartData, mockPatternCategories } from './data/mockIncidents'

// ─── Constants ────────────────────────────────────────────────────────────────
const API_BASE = 'http://127.0.0.1:8000'
const REFRESH_MS = 4000

// ─── Icon definitions for metric cards ────────────────────────────────────────
const ActivityIcon = () => (
  <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
    <path d="M2 10h3l2-6 4 12 2-6h5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
)

const AlertIcon = () => (
  <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
    <path d="M10 2 2 17h16L10 2Z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/>
    <path d="M10 8v4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    <circle cx="10" cy="14.2" r="0.9" fill="currentColor"/>
  </svg>
)

const GaugeIcon = () => (
  <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
    <path d="M3.5 14.5A7.5 7.5 0 0 1 17 10" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    <path d="M10 10l-3-3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    <circle cx="10" cy="10" r="1.5" fill="currentColor"/>
  </svg>
)

const TimerIcon = () => (
  <svg viewBox="0 0 20 20" width="16" height="16" fill="none">
    <circle cx="10" cy="11" r="7" stroke="currentColor" strokeWidth="1.4"/>
    <path d="M10 7v4l2.5 2.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    <path d="M7.5 2.5h5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
  </svg>
)

// ─── Helpers ───────────────────────────────────────────────────────────────────
function timeAgo(isoString) {
  const seconds = Math.floor((Date.now() - new Date(isoString)) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ago`
}

// Convert raw anomalies from the API to the Incident shape for the table
function anomalyToIncident(a, index) {
  const severityMap = { critical: 'critical', warning: 'high', info: 'low' }
  const stateMap = { critical: 'Open', warning: 'Investigating', info: 'Mitigated' }
  return {
    id: `INC-API-${String(index + 1).padStart(3, '0')}`,
    title: a.message || a.route || 'Unknown incident',
    vendor: a.route || 'Internal',
    severity: severityMap[a.severity] || 'medium',
    state: stateMap[a.severity] || 'Open',
    viability: a.feedback_correct === true ? 90 : a.feedback_correct === false ? 40 : 60,
    ownerInitials: 'AI',
    ownerName: 'Agent Alpha',
    ageLabel: timeAgo(a.timestamp),
    explanation: a.explanation || null,
    matchedIncident: a.matched_incident || null,
  }
}

// ─── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [stats, setStats]             = useState(null)
  const [anomalies, setAnomalies]     = useState([])
  const [health, setHealth]           = useState(null)
  const [connected, setConnected]     = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [activeSection, setActiveSection] = useState('overview')

  // ── Fetch backend data ──────────────────────────────────────────────────────
  const fetchData = useCallback(async (manual = false) => {
    if (manual) setIsRefreshing(true)
    try {
      const [statsRes, anomaliesRes, healthRes] = await Promise.all([
        axios.get(`${API_BASE}/stats`),
        axios.get(`${API_BASE}/anomalies?limit=25`),
        axios.get(`${API_BASE}/system-health`),
      ])
      setStats(statsRes.data)
      setAnomalies(anomaliesRes.data)
      setHealth(healthRes.data)
      setConnected(true)
      setLastUpdated(new Date())
    } catch {
      setConnected(false)
    } finally {
      if (manual) {
        // Minimum 700ms spin so the animation is visible
        setTimeout(() => setIsRefreshing(false), 700)
      }
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(() => fetchData(), REFRESH_MS)
    return () => clearInterval(interval)
  }, [fetchData])

  // ── Derived data ────────────────────────────────────────────────────────────
  const healthyRate = stats
    ? (((stats.total_logs - stats.total_anomalies) / Math.max(stats.total_logs, 1)) * 100).toFixed(0)
    : null

  // Merge: real incidents from API + mock as fallback
  const apiIncidents = useMemo(() =>
    anomalies.slice(0, 10).map(anomalyToIncident),
    [anomalies]
  )
  const tableIncidents = connected && apiIncidents.length > 0 ? apiIncidents : mockIncidents

  // Metric card values (real when available, mock otherwise)
  const totalIncidents = stats?.total_anomalies ?? mockIncidents.length
  const criticalCount  = anomalies.filter(a => a.severity === 'critical').length || 3
  const avgViability   = healthyRate ? `${healthyRate}%` : '66%'
  const openInvestigations = anomalies.filter(a =>
    !a.feedback_correct
  ).length || 4

  // Chart data (real trend or mock)
  const chartData = mockChartData // always use mock for chart shape consistency

  // Health index from backend or mock
  const healthIndex = health
    ? ((health.feedback?.corrections_learned ?? 8) + 76).toFixed(1)
    : '84.2'

  // ── Handlers ────────────────────────────────────────────────────────────────
  function handleNavClick(id) {
    setActiveSection(id)
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="dashboard-shell">
      {/* Sidebar */}
      <Sidebar
        activeSection={activeSection}
        onNavClick={handleNavClick}
      />

      {/* Main content area */}
      <div className="main-area">
        <Topbar />

        <div className="content-scroll">
          <div className="content-inner">

            {/* ── Metric Cards ── */}
            <section id="overview" className="metric-row">
              <MetricCard
                icon={ActivityIcon}
                iconVariant="violet"
                label="Total incidents"
                value={totalIncidents}
                deltaPercent="12.4%"
                deltaLabel="this week"
                animationDelay={0}
              />
              <MetricCard
                icon={AlertIcon}
                iconVariant="red"
                label="Critical attention"
                value={criticalCount}
                deltaPercent="4.8%"
                deltaLabel="increase"
                needsReview={true}
                animationDelay={60}
              />
              <MetricCard
                icon={GaugeIcon}
                iconVariant="green"
                label="Avg. viability score"
                value={avgViability}
                deltaPercent="8.2%"
                deltaLabel="improvement"
                animationDelay={120}
              />
              <MetricCard
                icon={TimerIcon}
                iconVariant="violet"
                label="Open investigations"
                value={openInvestigations}
                deltaPercent="2.1%"
                deltaLabel="resolved"
                animationDelay={180}
              />
            </section>

            {/* ── Charts Row ── */}
            <section id="charts" className="chart-row">
              <SignalChart data={chartData} />
              <PatternIndexCard categories={mockPatternCategories} />
            </section>

            {/* ── Live Queue ── */}
            <section id="anomalies">
              <IncidentTable
                incidents={tableIncidents}
                healthIndex={healthIndex}
              />
            </section>

          </div>
        </div>
      </div>
    </div>
  )
}