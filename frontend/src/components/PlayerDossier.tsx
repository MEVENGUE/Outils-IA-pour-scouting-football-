import type { AiStatus, Player } from '../App'
import './PlayerDossier.css'

interface PlayerDossierProps {
  player: Player | null
  loading: boolean
  error: string | null
  aiStatus: AiStatus
}

export default function PlayerDossier({ player, loading, error, aiStatus }: PlayerDossierProps) {
  if (!player && !loading && !error) {
    return (
      <div className="player-dossier">
        <h2>Dossier Joueur</h2>
        <div className="empty-state">
          <p style={{ color: '#888', fontSize: '1rem', marginTop: '2rem' }}>
            Recherchez un joueur pour afficher ses informations
          </p>
        </div>
      </div>
    )
  }

  if (error && !player) {
    return (
      <div className="player-dossier">
        <div className="error">{error}</div>
      </div>
    )
  }

  if (!player) {
    return (
      <div className="player-dossier">
        <div className="loading">Chargement des données du joueur...</div>
      </div>
    )
  }

  const statsAvailable = player.stats_available ?? false

  return (
    <div className="player-dossier">
      <h2>Dossier Joueur</h2>

      {loading && <div className="loading-banner">Mise à jour des données...</div>}
      {error && <div className="error-inline">{error}</div>}

      <div className="player-header">
        {player.image_url && (
          <img
            src={player.image_url}
            alt={player.name}
            className="player-image"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none'
            }}
          />
        )}
        <h3 className="player-name">{player.name}</h3>
      </div>

      <div className="player-info">
        <div className="info-item">
          <span className="info-label">Âge:</span>
          <span className="info-value">{player.age ?? 'N/A'} ans</span>
        </div>
        <div className="info-item">
          <span className="info-label">Nationalité:</span>
          <span className="info-value">{player.nationality || 'N/A'}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Club:</span>
          <span className="info-value">{player.current_club || 'N/A'}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Poste:</span>
          <span className="info-value">{player.position || 'N/A'}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Taille:</span>
          <span className="info-value">{player.height || 'N/A'}</span>
        </div>
        <div className="info-item">
          <span className="info-label">Valeur marchande:</span>
          <span className="info-value">{player.market_value || 'N/A'}</span>
        </div>
      </div>

      <div className="player-stats">
        <h3>Statistiques</h3>
        {!statsAvailable && (
          <p className="stats-unavailable">
            Statistiques saison en cours indisponibles pour le moment.
          </p>
        )}
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-value">{player.goals ?? 0}</span>
            <span className="stat-label">Buts</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{player.assists ?? 0}</span>
            <span className="stat-label">Passes décisives</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{player.appearances ?? 0}</span>
            <span className="stat-label">Matchs</span>
          </div>
        </div>

        {statsAvailable && player.appearances && player.appearances > 0 && (
          <div className="stats-charts">
            <div className="chart-item">
              <h4>Efficacité offensive</h4>
              <div className="progress-bar-container">
                <div className="progress-bar">
                  <div
                    className="progress-fill goals-progress"
                    style={{
                      width: `${Math.min(100, ((player.goals || 0) / player.appearances) * 100)}%`,
                    }}
                  >
                    <span>
                      Buts/match: {((player.goals || 0) / player.appearances).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="progress-bar-container">
                <div className="progress-bar">
                  <div
                    className="progress-fill assists-progress"
                    style={{
                      width: `${Math.min(100, ((player.assists || 0) / player.appearances) * 100)}%`,
                    }}
                  >
                    <span>
                      Passes/match: {((player.assists || 0) / player.appearances).toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="chart-item">
              <h4>Contribution totale</h4>
              <div className="contribution-circle">
                <div className="contribution-value">
                  {(player.goals || 0) + (player.assists || 0)}
                </div>
                <div className="contribution-label">Buts + Passes</div>
                <div className="contribution-per-match">
                  {(((player.goals || 0) + (player.assists || 0)) / player.appearances).toFixed(2)}{' '}
                  par match
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {player.scouting_report ? (
        <div className="scouting-report">
          <h3>Rapport de Scouting</h3>
          <div className="report-content">{player.scouting_report}</div>
        </div>
      ) : (
        <div className="scouting-report scouting-report-empty">
          <h3>Rapport de Scouting</h3>
          <p className="report-placeholder">
            {aiStatus === 'unconfigured'
              ? 'Configurez OPENAI_API_KEY pour générer un rapport IA détaillé.'
              : 'Rapport IA indisponible pour ce joueur.'}
          </p>
        </div>
      )}
    </div>
  )
}
