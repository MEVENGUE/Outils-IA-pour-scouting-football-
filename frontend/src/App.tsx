import { useState } from 'react'
import Globe from './components/Globe'
import PlayerDossier from './components/PlayerDossier'
import AIScoutingAssistant from './components/AIScoutingAssistant'
import './App.css'

const API_URL = 'http://127.0.0.1:8000'

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
}

function App() {
  const [player, setPlayer] = useState<Player | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchPlayer = async (playerName: string) => {
    if (!playerName.trim()) {
      setError('Veuillez entrer un nom de joueur')
      return
    }

    setLoading(true)
    setError(null)
    setPlayer(null)

    try {
      // D'abord, on essaie de scraper le joueur
      const scrapeResponse = await fetch(`${API_URL}/scrape-player`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ player_name: playerName }),
      })

      if (!scrapeResponse.ok) {
        const errorData = await scrapeResponse.json().catch(() => ({}))
        const errorMessage = errorData.detail || `Erreur ${scrapeResponse.status}: ${scrapeResponse.statusText}`
        
        // Si le scraping échoue (404), on essaie de récupérer depuis la DB
        if (scrapeResponse.status === 404) {
          try {
            const dbResponse = await fetch(`${API_URL}/player-by-name/${encodeURIComponent(playerName)}`)
            if (dbResponse.ok) {
              const dbData = await dbResponse.json()
              setPlayer(dbData.player)
              return
            }
          } catch (dbErr) {
            console.warn('Erreur lors de la récupération depuis la DB:', dbErr)
          }
        }
        
        throw new Error(errorMessage)
      } else {
        const scrapeData = await scrapeResponse.json()
        if (scrapeData.player) {
          setPlayer(scrapeData.player)
        } else {
          throw new Error('Données du joueur invalides')
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur lors de la récupération du joueur'
      setError(errorMessage)
      console.error('Erreur:', err)
    } finally {
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
          <PlayerDossier player={player} loading={loading} error={error} />
        </div>
        <div className="center-panel">
          <Globe player={player} />
        </div>
        <div className="right-panel">
          <AIScoutingAssistant 
            player={player} 
            onPlayerRequest={fetchPlayer}
            loading={loading}
          />
        </div>
      </div>
    </div>
  )
}

export default App

