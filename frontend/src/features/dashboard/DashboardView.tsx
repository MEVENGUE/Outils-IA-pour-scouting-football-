import { useApp } from '../../context/AppContext'
import PlayerProfileCard from './PlayerProfileCard'
import PerformanceCharts from './PerformanceCharts'
import './DashboardView.css'

export default function DashboardView() {
  const { player, loading, error, watchlistIds, toggleWatchlist } = useApp()

  return (
    <div className="dashboard-view">
      {error && <div className="error-banner">{error}</div>}
      <PlayerProfileCard
        player={player}
        loading={loading}
        inWatchlist={player?.id ? watchlistIds.includes(player.id) : false}
        onToggleWatchlist={
          player?.id ? () => toggleWatchlist(player.id!) : undefined
        }
      />
      <PerformanceCharts player={player} />
      {player?.scouting_report && (
        <div className="card report-preview">
          <h3>AI Scouting Preview</h3>
          <p>{player.scouting_report.slice(0, 600)}{player.scouting_report.length > 600 ? '…' : ''}</p>
        </div>
      )}
    </div>
  )
}
