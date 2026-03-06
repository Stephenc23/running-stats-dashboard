import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { setToken } from '../api'

export default function Layout() {
  const navigate = useNavigate()

  const handleLogout = () => {
    setToken(null)
    navigate('/login')
  }

  const navClass = ({ isActive }) =>
    `px-4 py-2 rounded-lg font-medium transition-colors ${isActive ? 'bg-brand-500/20 text-brand-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'}`

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-800 bg-surface-900/50 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
          <NavLink to="/" className="flex items-center gap-2 font-bold text-lg text-white">
            <span className="text-2xl" aria-hidden>🏃</span>
            Running Stats
          </NavLink>
          <nav className="flex items-center gap-1">
            <NavLink to="/" end className={navClass}>Dashboard</NavLink>
            <NavLink to="/runs" className={navClass}>Runs</NavLink>
            <NavLink to="/upload" className={navClass}>Upload</NavLink>
            <NavLink to="/recommendations" className={navClass}>Recommendations</NavLink>
            <button onClick={handleLogout} className="ml-4 px-4 py-2 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 font-medium transition-colors">
              Log out
            </button>
          </nav>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}
