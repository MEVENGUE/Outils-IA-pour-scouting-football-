import { useState } from 'react'
import Globe from './components/Globe'
import PlayerDossier from './components/PlayerDossier'
import AIScoutingAssistant from './components/AIScoutingAssistant'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const REQUEST_TIMEOUT_MS = 90_000

export interface Player {
  id?: number
  name: string
  age?: number
  nationality?: string
  current_club?: string
  position?: string
  height?: string
  market_value?: string
  goals?: number
  assists?: number
  appearances?: number
  image_url?: string
  scouting_report?: string
  stats_available?: boolean
  stats_season?: string
  stats_source?: string
}

export type AiStatus = 'ready' | 'unconfigured' | 'report_unavailable'

function parseApiError(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail.map((item) => String(item)).join('; ')
  }
  return fallback
}

function App() {
  const [player, setPlayer] = useState<Player | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [aiStatus, setAiStatus] = useState<AiStatus>('unconfigured')

  const fetchPlayer = async (playerName: string) => {
    if (!playerName.trim()) {
      setError('Veuillez entrer un nom de joueur')
      return
    }

    setLoading(true)
    setError(null)

    const controller = new AbortController()
    const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

    try {
      const scrapeResponse = await fetch(`${API_URL}/scrape-player`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ player_name: playerName }),
        signal: controller.signal,
      })

      if (!scrapeResponse.ok) {
        const errorData = await scrapeResponse.json().catch(() => ({}))
        const errorMessage = parseApiError(
          errorData.detail,
          `Erreur ${scrapeResponse.status}: ${scrapeResponse.statusText}`,
        )

        if (scrapeResponse.status === 404 || scrapeResponse.status >= 500) {
          try {
            const dbResponse = await fetch(
              `${API_URL}/player-by-name/${encodeURIComponent(playerName)}`,
            )
            if (dbResponse.ok) {
              const dbData = await dbResponse.json()
              setPlayer(dbData.player)
              setAiStatus('unconfigured')
              return
            }
          } catch (dbErr) {
            console.warn('Erreur lors de la récupération depuis la DB:', dbErr)
          }
        }

        throw new Error(errorMessage)
      }

      const scrapeData = await scrapeResponse.json()
      if (scrapeData.player) {
        setPlayer(scrapeData.player)
        setAiStatus(scrapeData.ai_status ?? 'unconfigured')
      } else {
        throw new Error('Données du joueur invalides')
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setError('La recherche a pris trop de temps. Réessayez dans quelques instants.')
      } else {
        const errorMessage =
          err instanceof Error ? err.message : 'Erreur lors de la récupération du joueur'
        setError(errorMessage)
      }
      console.error('Erreur:', err)
    } finally {
      window.clearTimeout(timeoutId)
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <img src="/x-scout-logo.jpg" alt="X-scout Logo" className="app-logo" />
          <h1>X-scout</h1>
        </div>
      </header>
      <div className="app-layout">
        <div className="left-panel">
          <PlayerDossier player={player} loading={loading} error={error} aiStatus={aiStatus} />
        </div>
        <div className="center-panel">
          <Globe player={player} />
        </div>
        <div className="right-panel">
          <AIScoutingAssistant
            player={player}
            onPlayerRequest={fetchPlayer}
            loading={loading}
            aiStatus={aiStatus}
          />
        </div>
      </div>
    </div>
  )
}

export default App
