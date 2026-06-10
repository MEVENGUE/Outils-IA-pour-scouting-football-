import { motion } from 'framer-motion'
import { Sparkles, X } from 'lucide-react'
import { useApp } from '../context/AppContext'
import { useSystemHealth } from '../hooks/useSystemHealth'
import { NAV_ITEMS } from '../config/navigation'
import './Sidebar.css'

interface SidebarProps {
  open?: boolean
  onNavigate?: () => void
}

export default function Sidebar({ open = false, onNavigate }: SidebarProps) {
  const { activeView, setActiveView, watchlistIds } = useApp()
  const { data: health } = useSystemHealth()

  const navigate = (view: typeof activeView) => {
    setActiveView(view)
    onNavigate?.()
  }

  return (
    <aside className={`sidebar glass ${open ? 'sidebar--open' : ''}`}>
      <div className="sidebar-brand">
        <div className="brand-icon brand-logo">
          <img src="/x-scout-logo.jpg" alt="X-SCOUT" />
        </div>
        <div className="sidebar-brand-copy">
          <strong>X-SCOUT AI</strong>
          <span>Football Intelligence OS</span>
        </div>
        <button
          type="button"
          className="sidebar-close"
          aria-label="Fermer le menu"
          onClick={onNavigate}
        >
          <X size={20} />
        </button>
      </div>

      <nav className="sidebar-nav" aria-label="Navigation principale">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          const active = activeView === item.id
          return (
            <motion.button
              key={item.id}
              type="button"
              className={`nav-item ${active ? 'active' : ''}`}
              whileHover={{ x: 4 }}
              onClick={() => navigate(item.id)}
            >
              <Icon size={18} />
              <div className="nav-copy">
                <span>{item.title}</span>
                <small>{item.description}</small>
              </div>
              {item.id === 'watchlist' && watchlistIds.length > 0 && (
                <span className="nav-badge">{watchlistIds.length}</span>
              )}
            </motion.button>
          )
        })}
      </nav>

      <div className="sidebar-status card">
        <div className="status-title">
          <Sparkles size={16} /> System Status
        </div>
        <StatusRow label="OpenAI" ok={health?.openai === 'configured'} />
        <StatusRow label="Database" ok={health?.database === 'connected'} />
        <StatusRow label="Scout Engine" ok={health?.status === 'healthy'} />
        <StatusRow label="Transfermarkt" ok={true} hint="via scraper" />
        <StatusRow label="Wikipedia" ok={true} hint="via scraper" />
      </div>
    </aside>
  )
}

function StatusRow({
  label,
  ok,
  hint,
}: {
  label: string
  ok: boolean
  hint?: string
}) {
  return (
    <div className="status-row">
      <span>{label}</span>
      <span className={`badge ${ok ? 'success' : 'warning'}`}>
        {ok ? 'Connected' : 'Pending'}
        {hint ? ` · ${hint}` : ''}
      </span>
    </div>
  )
}
