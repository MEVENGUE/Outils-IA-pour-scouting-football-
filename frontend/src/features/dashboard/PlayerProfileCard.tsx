import type { Player } from '../../types/player'
import { countryCodeFromName, getInitials } from '../../utils/storage'
import './PlayerProfileCard.css'

interface Props {
  player: Player | null
  loading?: boolean
  onToggleWatchlist?: () => void
  inWatchlist?: boolean
}

export default function PlayerProfileCard({
  player,
  loading,
  onToggleWatchlist,
  inWatchlist,
}: Props) {
  if (loading && !player) {
    return (
      <div className="player-profile card">
        <div className="skeleton" style={{ height: 280 }} />
      </div>
    )
  }

  if (!player) {
    return (
      <div className="player-profile card empty-state">
        Search a player to generate a live intelligence profile.
      </div>
    )
  }

  const flagCode = countryCodeFromName(player.nationality)

  return (
    <div className="player-profile card">
      <div className="profile-top">
        <div className="avatar-wrap">
          {player.image_url ? (
            <img src={player.image_url} alt={player.name} className="avatar-photo" />
          ) : (
            <div className="avatar-fallback">{getInitials(player.name)}</div>
          )}
        </div>
        <div className="profile-meta">
          <div className="profile-title">
            <h2>{player.name}</h2>
            {flagCode && (
              <img
                className="flag"
                src={`https://flagcdn.com/w40/${flagCode}.png`}
                alt={player.nationality ?? ''}
              />
            )}
          </div>
          <div className="profile-tags">
            {player.nationality && <span className="badge">{player.nationality}</span>}
            {player.current_club && <span className="badge">{player.current_club}</span>}
            {player.position && <span className="badge">{player.position}</span>}
          </div>
          <div className="profile-grid">
            <Metric label="Age" value={player.age ? `${player.age} yrs` : '—'} />
            <Metric label="Height" value={player.height ?? '—'} />
            <Metric label="Weight" value={player.weight ?? '—'} />
            <Metric label="Market Value" value={player.market_value ?? '—'} highlight />
            <Metric label="Contract" value={player.contract_expires ?? '—'} />
            <Metric
              label="Season"
              value={player.stats_season ? player.stats_season : '—'}
            />
          </div>
          {onToggleWatchlist && player.id && (
            <button type="button" className="btn btn-primary" onClick={onToggleWatchlist}>
              {inWatchlist ? 'Remove from Watchlist' : 'Add to Watchlist'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function Metric({
  label,
  value,
  highlight,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div className={`metric ${highlight ? 'highlight' : ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}
