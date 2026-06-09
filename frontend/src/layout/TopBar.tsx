import { Search } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useApp } from '../context/AppContext'
import { fetchPlayers } from '../api/players'
import './TopBar.css'

export default function TopBar() {
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
      <form className="topbar-search" onSubmit={onSubmit}>
        <Search size={18} />
        <input
          className="input topbar-input"
          placeholder="Search players, clubs, leagues..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <kbd>⌘ K</kbd>
        <button className="btn btn-primary" type="submit" disabled={loading}>
          Search
        </button>
      </form>
      <div className="topbar-meta">
        <span>
          Real-time database:{' '}
          <strong>{playersData?.players.length ?? '—'}</strong> players indexed
        </span>
      </div>
    </header>
  )
}
