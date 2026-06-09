import { useEffect, useState } from 'react'
import type { AiStatus, Player } from '../App'
import './AIScoutingAssistant.css'

interface AIScoutingAssistantProps {
  player: Player | null
  onPlayerRequest: (playerName: string) => void
  loading: boolean
  aiStatus: AiStatus
}

interface PlayerSummary {
  name: string
  club: string
  nationality: string
  market_value: string
  age: number | null
  position: string | null
  height: string | null
  goals: number
  assists: number
  appearances: number
  stats_available: boolean
  stats_season?: string
  image_url: string | null
  scouting_report?: string
}

function buildPlayerSummary(player: Player): string {
  const summary: PlayerSummary = {
    name: player.name,
    club: player.current_club || 'N/A',
    nationality: player.nationality || 'N/A',
    market_value: player.market_value || 'N/A',
    age: player.age ?? null,
    position: player.position ?? null,
    height: player.height ?? null,
    goals: player.goals ?? 0,
    assists: player.assists ?? 0,
    appearances: player.appearances ?? 0,
    stats_available: player.stats_available ?? false,
    stats_season: player.stats_season,
    image_url: player.image_url ?? null,
  }

  if (player.scouting_report) {
    summary.scouting_report = player.scouting_report
  }

  const lines = [
    `Profil trouvé pour ${summary.name}.`,
    `Club: ${summary.club}`,
    `Nationalité: ${summary.nationality}`,
    `Poste: ${summary.position || 'N/A'}`,
    `Âge: ${summary.age ?? 'N/A'}`,
    `Valeur marchande: ${summary.market_value}`,
  ]

  if (summary.stats_available) {
    const seasonLabel = summary.stats_season ? ` (${summary.stats_season})` : ''
    lines.push(
      `Stats${seasonLabel}: ${summary.goals} buts, ${summary.assists} passes, ${summary.appearances} matchs.`,
    )
  } else {
    lines.push('Stats saison: indisponibles pour le moment.')
  }

  if (summary.scouting_report) {
    lines.push('', 'Rapport IA:', summary.scouting_report)
  }

  return lines.join('\n')
}

export default function AIScoutingAssistant({
  player,
  onPlayerRequest,
  loading,
  aiStatus,
}: AIScoutingAssistantProps) {
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'ai'; content: string }>>([])

  useEffect(() => {
    if (player) {
      setMessages([
        { role: 'user', content: player.name },
        { role: 'ai', content: buildPlayerSummary(player) },
      ])
    }
  }, [player])

  const handleSend = () => {
    if (!inputValue.trim() || loading) return

    const playerName = inputValue.trim()
    setInputValue('')
    setMessages((prev) => [...prev, { role: 'user', content: playerName }])
    onPlayerRequest(playerName)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="ai-assistant">
      <h2>IA Scouting Assistant</h2>

      {aiStatus === 'unconfigured' && (
        <p className="ai-status-banner">
          Mode sans IA : configurez OPENAI_API_KEY pour les rapports avancés.
        </p>
      )}

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-chat">
            <p>Demandez un rapport sur un joueur</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-label">{msg.role === 'user' ? 'Vous:' : 'Agent IA:'}</div>
            <div className="message-content">
              <p className="message-text">{msg.content}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="message ai">
            <div className="message-label">Agent IA:</div>
            <div className="message-content">
              <p>Analyse en cours...</p>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-container">
        <input
          type="text"
          className="chat-input"
          placeholder="Rechercher un joueur..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className="send-button"
          onClick={handleSend}
          disabled={loading || !inputValue.trim()}
        >
          ENVOYER
        </button>
      </div>
    </div>
  )
}
