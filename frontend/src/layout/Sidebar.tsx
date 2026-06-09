import { motion } from 'framer-motion'
import {
  BarChart3,
  FileText,
  Globe2,
  LayoutDashboard,
  Radar,
  Search,
  Settings,
  Sparkles,
  Star,
  Users,
} from 'lucide-react'
import { useApp } from '../context/AppContext'
import { useSystemHealth } from '../hooks/useSystemHealth'
import type { AppView } from '../types/player'
import './Sidebar.css'

const NAV: {
  id: AppView
  title: string
  description: string
  icon: typeof Search
}[] = [
  { id: 'search', title: 'Search Players', description: 'Recherche globale', icon: Search },
  { id: 'dashboard', title: 'Dashboard', description: 'Analyse joueur', icon: LayoutDashboard },
  { id: 'globe', title: '3D Globe Intelligence', description: 'Cartographie', icon: Globe2 },
  { id: 'reports', title: 'AI Reports', description: 'Rapports scouting', icon: FileText },
  { id: 'watchlist', title: 'Watchlist', description: 'Joueurs suivis', icon: Star },
  { id: 'compare', title: 'Compare Players', description: 'Comparaison', icon: Users },
  { id: 'talent', title: 'Talent Discovery', description: 'Base de données', icon: Radar },
  { id: 'documents', title: 'Document Analysis', description: 'Centre documentaire', icon: BarChart3 },
  { id: 'settings', title: 'Settings', description: 'Configuration', icon: Settings },
]

export default function Sidebar() {
  const { activeView, setActiveView, watchlistIds } = useApp()
  const { data: health } = useSystemHealth()

  return (
    <aside className="sidebar glass">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Globe2 size={22} />
        </div>
        <div>
          <strong>X-SCOUT AI</strong>
          <span>Football Intelligence OS</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV.map((item) => {
          const Icon = item.icon
          const active = activeView === item.id
          return (
            <motion.button
              key={item.id}
              type="button"
              className={`nav-item ${active ? 'active' : ''}`}
              whileHover={{ x: 4 }}
              onClick={() => setActiveView(item.id)}
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
