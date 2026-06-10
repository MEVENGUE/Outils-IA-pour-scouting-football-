import { Menu, Sparkles } from 'lucide-react'
import { MOBILE_NAV_ITEMS } from '../config/navigation'
import { useApp } from '../context/AppContext'
import './MobileNav.css'

interface MobileNavProps {
  onOpenMenu: () => void
  onOpenCopilot: () => void
}

export default function MobileNav({ onOpenMenu, onOpenCopilot }: MobileNavProps) {
  const { activeView, setActiveView, watchlistIds } = useApp()

  return (
    <nav className="mobile-nav glass" aria-label="Navigation mobile">
      {MOBILE_NAV_ITEMS.map((item) => {
        const Icon = item.icon
        const active = activeView === item.id
        return (
          <button
            key={item.id}
            type="button"
            className={`mobile-nav-item ${active ? 'active' : ''}`}
            onClick={() => setActiveView(item.id)}
            aria-current={active ? 'page' : undefined}
          >
            <Icon size={20} />
            <span>{item.mobileLabel ?? item.title}</span>
            {item.id === 'watchlist' && watchlistIds.length > 0 && (
              <span className="mobile-nav-badge">{watchlistIds.length}</span>
            )}
          </button>
        )
      })}
      <button type="button" className="mobile-nav-item" onClick={onOpenCopilot} aria-label="Ouvrir AI Copilot">
        <Sparkles size={20} />
        <span>Copilot</span>
      </button>
      <button type="button" className="mobile-nav-item" onClick={onOpenMenu} aria-label="Ouvrir le menu">
        <Menu size={20} />
        <span>Menu</span>
      </button>
    </nav>
  )
}
