import { useQuery } from '@tanstack/react-query'
import { fetchPlayerAnalytics } from '../../api/players'
import { useApp } from '../../context/AppContext'

export default function TalentDiscoveryView() {
  const { searchPlayer } = useApp()
  const { data, isLoading, error } = useQuery({
    queryKey: ['talent-analytics'],
    queryFn: () => fetchPlayerAnalytics({ min_goals: 1 }),
  })

  if (isLoading) return <div className="skeleton" style={{ height: 280 }} />
  if (error) return <div className="error-banner">Unable to load talent data from backend.</div>

  const players = data?.players ?? []

  return (
    <div className="card view-card--compact">
      <h2>Talent Discovery</h2>
      <p style={{ color: 'var(--muted)' }}>
        Live recommendations from `/analytics/player-stats` — {data?.total_players ?? 0} profiles
        matching filters.
      </p>
      {players.length === 0 ? (
        <div className="empty-state">No indexed players yet. Search players to populate the database.</div>
      ) : (
        <div className="list-stack">
          {players.slice(0, 20).map((p) => {
            const score = (p.goals ?? 0) + (p.assists ?? 0)
            return (
              <div key={p.id ?? p.name} className="card list-row">
                <div className="list-row__main">
                  <strong>{p.name}</strong>
                  <div className="list-row__meta">
                    {p.current_club ?? '—'} · {p.position ?? '—'} · {p.nationality ?? '—'}
                  </div>
                </div>
                <div className="list-row__actions">
                  <span className="badge success">{score} G+A index</span>
                  <button type="button" className="btn" onClick={() => searchPlayer(p.name)}>
                    Analyze
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
