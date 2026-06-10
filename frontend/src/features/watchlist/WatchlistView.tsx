import { useQuery } from '@tanstack/react-query'
import { fetchPlayers } from '../../api/players'
import { useApp } from '../../context/AppContext'

export default function WatchlistView() {
  const { watchlistIds, toggleWatchlist, searchPlayer } = useApp()
  const { data, isLoading } = useQuery({
    queryKey: ['watchlist', watchlistIds],
    queryFn: () => fetchPlayers(),
  })

  const players = (data?.players ?? []).filter((p) => p.id && watchlistIds.includes(p.id))

  if (isLoading) return <div className="skeleton" style={{ height: 240 }} />

  if (watchlistIds.length === 0) {
    return (
      <div className="card empty-state">
        Your watchlist is empty. Add players from the dashboard after searching.
      </div>
    )
  }

  return (
    <div className="card view-card--compact">
      <h2>Watchlist</h2>
      <div className="list-stack">
        {players.map((p) => (
          <div key={p.id} className="card list-row list-row--grid">
            <div className="list-row__main">
              <strong>{p.name}</strong>
              <div className="list-row__meta">
                {p.current_club ?? '—'} · {p.position ?? '—'} · {p.market_value ?? '—'}
              </div>
            </div>
            <span className="badge">
              {p.stats_available ? `${p.goals ?? 0}G / ${p.appearances ?? 0}MJ` : 'Stats N/A'}
            </span>
            <div className="list-row__actions">
              <button type="button" className="btn" onClick={() => searchPlayer(p.name)}>
                Open
              </button>
              <button type="button" className="btn" onClick={() => p.id && toggleWatchlist(p.id)}>
                Remove
              </button>
            </div>
          </div>
        ))}
        {players.length === 0 && (
          <div className="empty-state">Saved IDs not found in database yet. Re-search those players.</div>
        )}
      </div>
    </div>
  )
}
