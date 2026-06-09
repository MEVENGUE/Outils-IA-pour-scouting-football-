import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { scrapePlayer } from '../../api/players'
import { useApp } from '../../context/AppContext'
import type { Player } from '../../types/player'

export default function CompareView() {
  const { compareA, compareB, setCompareA, setCompareB, player } = useApp()
  const [nameA, setNameA] = useState(compareA?.name ?? player?.name ?? '')
  const [nameB, setNameB] = useState(compareB?.name ?? '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runCompare = async () => {
    setLoading(true)
    setError(null)
    try {
      const [a, b] = await Promise.all([scrapePlayer(nameA), scrapePlayer(nameB)])
      setCompareA(a.player)
      setCompareB(b.player)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Compare failed')
    } finally {
      setLoading(false)
    }
  }

  const chartData = buildCompareChart(compareA, compareB)

  return (
    <div className="card" style={{ padding: '1rem' }}>
      <h2>Compare Players</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '0.75rem', marginTop: '1rem' }}>
        <input className="input" value={nameA} onChange={(e) => setNameA(e.target.value)} placeholder="Player A" />
        <input className="input" value={nameB} onChange={(e) => setNameB(e.target.value)} placeholder="Player B" />
        <button type="button" className="btn btn-primary" onClick={runCompare} disabled={loading}>
          Compare
        </button>
      </div>
      {error && <div className="error-banner" style={{ marginTop: '1rem' }}>{error}</div>}

      {compareA && compareB && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
            <PlayerCompareCard player={compareA} />
            <PlayerCompareCard player={compareB} />
          </div>
          <div style={{ height: 280, marginTop: '1rem' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="metric" stroke="#888" />
                <YAxis stroke="#888" allowDecimals={false} />
                <Tooltip />
                <Legend />
                <Bar dataKey={compareA.name} fill="#FF2D2D" radius={[6, 6, 0, 0]} />
                <Bar dataKey={compareB.name} fill="#FF8A8A" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )
}

function PlayerCompareCard({ player }: { player: Player }) {
  return (
    <div className="card" style={{ padding: '0.85rem' }}>
      <strong>{player.name}</strong>
      <div style={{ color: 'var(--muted)', fontSize: '0.82rem', marginTop: '0.35rem' }}>
        {player.current_club ?? '—'} · {player.market_value ?? '—'}
      </div>
      <div style={{ marginTop: '0.65rem', display: 'grid', gap: '0.35rem', fontSize: '0.85rem' }}>
        <span>Goals: {player.goals ?? 0}</span>
        <span>Assists: {player.assists ?? 0}</span>
        <span>Appearances: {player.appearances ?? 0}</span>
        <span>Age: {player.age ?? '—'}</span>
      </div>
    </div>
  )
}

function buildCompareChart(a: Player | null, b: Player | null) {
  if (!a || !b) return []
  return [
    { metric: 'Goals', [a.name]: a.goals ?? 0, [b.name]: b.goals ?? 0 },
    { metric: 'Assists', [a.name]: a.assists ?? 0, [b.name]: b.assists ?? 0 },
    { metric: 'Apps', [a.name]: a.appearances ?? 0, [b.name]: b.appearances ?? 0 },
  ]
}
