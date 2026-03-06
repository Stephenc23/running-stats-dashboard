import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

export default function Upload() {
  const navigate = useNavigate()
  const fileInput = useRef(null)
  const [file, setFile] = useState(null)
  const [title, setTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a GPX file.')
      return
    }
    setError('')
    setLoading(true)
    const form = new FormData()
    form.append('file', file)
    if (title.trim()) form.append('title', title.trim())
    try {
      const run = await api.postForm('/api/runs/upload-gpx', form)
      navigate(`/runs/${run.id}`)
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Upload GPX</h1>
      <p className="text-slate-400 mb-8">Import a run from a GPX file. We'll compute distance, pace, and splits.</p>

      <form onSubmit={handleSubmit} className="card max-w-lg space-y-5">
        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {error}
          </div>
        )}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">GPX file</label>
          <input
            ref={fileInput}
            type="file"
            accept=".gpx"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-slate-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-slate-700 file:text-slate-200 file:font-medium hover:file:bg-slate-600"
          />
          {file && <p className="mt-1.5 text-slate-500 text-sm">{file.name}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">Title (optional)</label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input"
            placeholder="e.g. Morning 5K"
          />
        </div>
        <div className="flex gap-3">
          <button type="submit" disabled={loading || !file} className="btn-primary">
            {loading ? 'Uploading…' : 'Upload'}
          </button>
          <button
            type="button"
            onClick={() => { fileInput.current?.click(); setError(''); }}
            className="btn-secondary"
          >
            Choose file
          </button>
        </div>
      </form>
    </div>
  )
}
