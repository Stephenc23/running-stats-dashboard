import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

function formatDuration(seconds) {
  if (seconds == null || seconds === 0) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function formatPace(minPerKm) {
  if (minPerKm == null) return '—'
  const m = Math.floor(minPerKm)
  const s = Math.round((minPerKm - m) * 60)
  return `${m}:${s.toString().padStart(2, '0')}/km`
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/runs/dashboard')
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-slate-400">Loading dashboard…</div>
      </div>
    )
  }
  if (error) {
    return (
      <div className="card border-red-500/30">
        <p className="text-red-400">{error}</p>
      </div>
    )
  }

  const cards = [
    { label: 'Total runs', value: stats.total_runs, unit: '', icon: '📊' },
    { label: 'Total distance', value: stats.total_distance_km?.toFixed(1), unit: 'km', icon: '🛤️' },
    { label: 'Total time', value: formatDuration(stats.total_duration_seconds), unit: '', icon: '⏱️' },
    { label: 'Avg pace', value: formatPace(stats.avg_pace_min_per_km), unit: '', icon: '⚡' },
    { label: 'Elevation gain', value: stats.total_elevation_gain_m?.toFixed(0), unit: 'm', icon: '⛰️' },
    { label: 'Runs this week', value: stats.runs_this_week, unit: '', icon: '📅' },
    { label: 'Runs this month', value: stats.runs_this_month, unit: '', icon: '🗓️' },
  ]

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Dashboard</h1>
      <p className="text-slate-400 mb-8">Your running overview at a glance.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {cards.map(({ label, value, unit, icon }) => (
          <div key={label} className="card flex items-start gap-4">
            <span className="text-2xl" aria-hidden>{icon}</span>
            <div>
              <p className="text-slate-400 text-sm font-medium">{label}</p>
              <p className="text-xl font-bold text-white mt-0.5">
                {value != null ? value : '—'} {unit}
              </p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 flex gap-4">
        <Link to="/upload" className="btn-primary">
          Upload GPX
        </Link>
        <Link to="/runs" className="btn-secondary">
          View all runs
        </Link>
      </div>
    </div>
  )
}
