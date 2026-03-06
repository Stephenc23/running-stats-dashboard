const API_BASE = ''

function getToken() {
  return localStorage.getItem('token')
}

function setToken(token) {
  if (token) localStorage.setItem('token', token)
  else localStorage.removeItem('token')
}

async function request(method, path, body = null, formData = false) {
  const opts = {
    method,
    headers: {},
  }
  const token = getToken()
  if (token) opts.headers['Authorization'] = `Bearer ${token}`
  if (body && !formData) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  if (formData) opts.body = body
  const res = await fetch(`${API_BASE}${path}`, opts)
  if (res.status === 401) {
    setToken(null)
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(Array.isArray(err.detail) ? err.detail.map(d => d.msg || d).join(', ') : (err.detail || res.statusText))
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  delete: (path) => request('DELETE', path),
  postForm: (path, formData) => request('POST', path, formData, true),
}

export { getToken, setToken }
