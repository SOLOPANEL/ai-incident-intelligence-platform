import { useEffect, useState } from 'react'

export default function PatternIndexCard({ categories }) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    // Delay to trigger CSS transition after mount
    const t = setTimeout(() => setMounted(true), 80)
    return () => clearTimeout(t)
  }, [])

  return (
    <div className="pattern-card">
      {/* Header */}
      <div className="pattern-card-header">
        <div>
          <div className="eyebrow">Pattern Index</div>
          <div className="pattern-card-title">By category</div>
        </div>
        <button className="pattern-overflow-btn" aria-label="More options" title="More options">
          ···
        </button>
      </div>

      {/* Category bars */}
      <div className="pattern-list">
        {categories.map((cat, i) => (
          <div key={cat.label} className="pattern-row">
            <span className="pattern-label">{cat.label}</span>
            <div className="pattern-bar-track">
              <div
                className="pattern-bar-fill"
                style={{
                  width: mounted ? `${cat.percent}%` : '0%',
                  transitionDelay: `${i * 60}ms`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
