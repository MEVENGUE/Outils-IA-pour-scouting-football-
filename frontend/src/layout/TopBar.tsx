import { Menu, Search, Sparkles } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useApp } from '../context/AppContext'
import { fetchPlayers } from '../api/players'
import './TopBar.css'

interface TopBarProps {
  onMenuClick?: () => void
  onCopilotClick?: () => void
}

export default function TopBar({ onMenuClick, onCopilotClick }: TopBarProps) {
  const { searchPlayer, loading, setActiveView } = useApp()
  const [query, setQuery] = useState('')
  const { data: playersData } = useQuery({
    queryKey: ['players-count'],
    queryFn: () => fetchPlayers(),
  })

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    await searchPlayer(query)
    setActiveView('dashboard')
  }

  return (
    <header className="topbar glass">
      <button
        type="button"
        className="topbar-menu-btn"
        aria-label="Ouvrir le menu"
        onClick={onMenuClick}
      >
        <Menu size={20} />
      </button>
      <form className="topbar-search" onSubmit={onSubmit}>
        <Search size={18} className="topbar-search-icon" />
        <input
          className="input topbar-input"
          placeholder="Search players, clubs, leagues..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <kbd className="topbar-kbd">⌘ K</kbd>
        <button className="btn btn-primary topbar-submit" type="submit" disabled={loading}>
          <Search size={16} className="topbar-submit-icon" aria-hidden />
          <span className="topbar-submit-label">Search</span>
        </button>
      </form>
      <div className="topbar-meta">
        <span>
          Real-time database:{' '}
          <strong>{playersData?.players.length ?? '—'}</strong> players indexed
        </span>
      </div>
      <button
        type="button"
        className="topbar-copilot-btn"
        aria-label="Ouvrir AI Copilot"
        onClick={onCopilotClick}
      >
        <Sparkles size={18} />
      </button>
    </header>
  )
}
