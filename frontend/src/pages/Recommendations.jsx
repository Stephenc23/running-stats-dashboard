import { useState, useEffect } from 'react'
import { api } from '../api'

function formatPace(minPerKm) {
  if (minPerKm == null) return null
  const m = Math.floor(minPerKm)
  const s = Math.round((minPerKm - m) * 60)
  return `${m}:${s.toString().padStart(2, '0')}/km`
}

export default function Recommendations() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/recommendations')
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-slate-400">Loading recommendations…</div>
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

  const priorityColor = {
    high: 'bg-brand-500/20 text-brand-400 border-brand-500/40',
    medium: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    low: 'bg-slate-600/30 text-slate-400 border-slate-500/30',
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Recommendations</h1>
      <p className="text-slate-400 mb-8">Personalized training suggestions based on your recent runs.</p>

      {data?.summary && (
        <div className="card mb-8 border-brand-500/20 bg-brand-500/5">
          <p className="text-slate-200">{data.summary}</p>
        </div>
      )}

      <div className="space-y-4">
        {data?.recommendations?.map((rec, i) => (
          <div key={i} className="card">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <h2 className="font-semibold text-white">{rec.title}</h2>
              <span className={`px-2 py-0.5 rounded text-xs font-medium border ${priorityColor[rec.priority] || priorityColor.low}`}>
                {rec.priority}
              </span>
            </div>
            <p className="text-slate-300 text-sm mb-3">{rec.description}</p>
            {rec.reason && (
              <p className="text-slate-500 text-xs mb-3">Why: {rec.reason}</p>
            )}
            <div className="flex flex-wrap gap-4 text-sm text-slate-400">
              {rec.suggested_pace_min_per_km != null && (
                <span>Pace: {formatPace(rec.suggested_pace_min_per_km)}</span>
              )}
              {rec.suggested_distance_km != null && (
                <span>Distance: {rec.suggested_distance_km} km</span>
              )}
              {rec.suggested_duration_minutes != null && (
                <span>Duration: {rec.suggested_duration_minutes} min</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {(!data?.recommendations || data.recommendations.length === 0) && (
        <div className="card text-center py-12 text-slate-400">
          Upload some runs to get personalized recommendations.
        </div>
      )}
    </div>
  )
}
