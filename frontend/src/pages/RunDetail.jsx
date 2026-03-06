import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api } from '../api'

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
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

export default function RunDetail() {
  const { id } = useParams()
  const [run, setRun] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get(`/api/runs/${id}`)
      .then(setRun)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-slate-400">Loading run…</div>
      </div>
    )
  }
  if (error || !run) {
    return (
      <div className="card border-red-500/30">
        <p className="text-red-400">{error || 'Run not found'}</p>
        <Link to="/runs" className="btn-secondary mt-4 inline-block">Back to runs</Link>
      </div>
    )
  }

  return (
    <div>
      <Link to="/runs" className="text-slate-400 hover:text-slate-200 text-sm mb-4 inline-block">← Back to runs</Link>
      <h1 className="text-2xl font-bold text-white mb-2">{run.title || `Run ${run.id}`}</h1>
      <p className="text-slate-400 mb-8">{formatDate(run.started_at)}</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="card">
          <p className="text-slate-400 text-sm">Distance</p>
          <p className="text-xl font-bold text-white mt-1">{run.distance_km != null ? `${run.distance_km.toFixed(2)} km` : '—'}</p>
        </div>
        <div className="card">
          <p className="text-slate-400 text-sm">Duration</p>
          <p className="text-xl font-bold text-white mt-1">{formatDuration(run.duration_seconds)}</p>
        </div>
        <div className="card">
          <p className="text-slate-400 text-sm">Avg pace</p>
          <p className="text-xl font-bold text-white mt-1">{formatPace(run.avg_pace_min_per_km)}</p>
        </div>
        <div className="card">
          <p className="text-slate-400 text-sm">Elevation gain</p>
          <p className="text-xl font-bold text-white mt-1">{run.elevation_gain_m != null ? `+${run.elevation_gain_m.toFixed(0)} m` : '—'}</p>
        </div>
      </div>

      {run.splits && run.splits.length > 0 && (
        <div className="card mb-8">
          <h2 className="text-lg font-semibold text-white mb-4">Splits (per km)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="text-left py-2 pr-4">#</th>
                  <th className="text-left py-2 pr-4">Distance</th>
                  <th className="text-left py-2 pr-4">Time</th>
                  <th className="text-left py-2">Pace</th>
                </tr>
              </thead>
              <tbody>
                {run.splits.map((s) => (
                  <tr key={s.id} className="border-b border-slate-800 last:border-0">
                    <td className="py-3 pr-4 text-slate-300">{s.split_index}</td>
                    <td className="py-3 pr-4 text-slate-300">{s.distance_km.toFixed(2)} km</td>
                    <td className="py-3 pr-4 text-slate-300">{formatDuration(s.duration_seconds)}</td>
                    <td className="py-3 text-brand-400">{formatPace(s.pace_min_per_km)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {run.source_file && (
        <p className="text-slate-500 text-sm">Source: {run.source_file}</p>
      )}
    </div>
  )
}
