import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Player } from '../../types/player'
import './PerformanceCharts.css'

export default function PerformanceCharts({ player }: { player: Player | null }) {
  if (!player) {
    return <div className="performance card empty-state">No performance data yet.</div>
  }

  if (!player.stats_available) {
    return (
      <div className="performance card empty-state">
        Season statistics unavailable from backend sources for this player.
      </div>
    )
  }

  const goals = player.goals ?? 0
  const assists = player.assists ?? 0
  const appearances = player.appearances ?? 0
  const barData = [
    { name: 'Goals', value: goals },
    { name: 'Assists', value: assists },
    { name: 'Apps', value: appearances },
  ]

  const pieData = [
    { name: 'Goals', value: goals },
    { name: 'Assists', value: assists },
  ]

  return (
    <div className="performance-grid">
      <div className="performance card">
        <h3>Performance Overview {player.stats_season ? `(${player.stats_season})` : ''}</h3>
        <div className="chart-box">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={barData}>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" stroke="#888" />
              <YAxis stroke="#888" allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                {barData.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={entry.name === 'Goals' ? '#FF2D2D' : entry.name === 'Assists' ? '#FF5C5C' : '#FF8A8A'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="performance card">
        <h3>Goal Contribution</h3>
        <div className="chart-box">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} dataKey="value" innerRadius={55} outerRadius={85} paddingAngle={3}>
                <Cell fill="#FF2D2D" />
                <Cell fill="#FF5C5C" />
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="contrib-total">{goals + assists} total G+A</div>
        </div>
      </div>
    </div>
  )
}
