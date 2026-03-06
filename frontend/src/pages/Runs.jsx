import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { dateStyle: 'medium' }) + ' ' + d.toLocaleTimeString(undefined, { timeStyle: 'short' })
}

function formatPace(minPerKm) {
  if (minPerKm == null) return '—'
  const m = Math.floor(minPerKm)
  const s = Math.round((minPerKm - m) * 60)
  return `${m}:${s.toString().padStart(2, '0')}/km`
}

function formatDuration(seconds) {
  if (seconds == null) return '—'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export default function Runs() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/runs')
      .then(setRuns)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-slate-400">Loading runs…</div>
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

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Runs</h1>
      <p className="text-slate-400 mb-8">All your recorded activities.</p>

      {runs.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-slate-400 mb-4">No runs yet.</p>
          <Link to="/upload" className="btn-primary">Upload a GPX file</Link>
        </div>
      ) : (
        <div className="space-y-3">
          {runs.map((run) => (
            <Link
              key={run.id}
              to={`/runs/${run.id}`}
              className="card block hover:border-brand-500/40 transition-colors"
            >
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <h2 className="font-semibold text-white">
                    {run.title || `Run ${run.id}`}
                  </h2>
                  <p className="text-slate-400 text-sm mt-0.5">{formatDate(run.started_at)}</p>
                </div>
                <div className="flex flex-wrap gap-6 text-sm">
                  <span className="text-slate-300">
                    <span className="text-slate-500">Distance:</span> {run.distance_km != null ? `${run.distance_km.toFixed(2)} km` : '—'}
                  </span>
                  <span className="text-slate-300">
                    <span className="text-slate-500">Pace:</span> {formatPace(run.avg_pace_min_per_km)}
                  </span>
                  <span className="text-slate-300">
                    <span className="text-slate-500">Time:</span> {formatDuration(run.duration_seconds)}
                  </span>
                  {run.elevation_gain_m != null && (
                    <span className="text-slate-300">
                      <span className="text-slate-500">Elev:</span> +{run.elevation_gain_m.toFixed(0)} m
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
