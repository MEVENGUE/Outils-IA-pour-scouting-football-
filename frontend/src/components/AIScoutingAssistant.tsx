import { useState, useEffect } from 'react'
import type { Player } from '../App'
import './AIScoutingAssistant.css'

interface AIScoutingAssistantProps {
  player: Player | null
  onPlayerRequest: (playerName: string) => void
  loading: boolean
}

export default function AIScoutingAssistant({ player, onPlayerRequest, loading }: AIScoutingAssistantProps) {
  const [inputValue, setInputValue] = useState('')
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'ai', content: string }>>([])

  useEffect(() => {
    if (player) {
      // Affiche les données du joueur comme message de l'IA
      const playerData: any = {
        name: player.name || 'N/A',
        club: player.current_club || 'N/A',
        market_value: player.market_value || 'N/A',
        image_url: player.image_url || null,
        goals: player.goals || 0,
        assists: player.assists || 0,
        appearances: player.appearances || 0,
        age: player.age || null,
        position: player.position || null,
        height: player.height || null
      }
      
      // Ajoute les champs optionnels seulement s'ils existent
      // Toujours afficher la nationalité si disponible, même si c'est "Unknown"
      if (player.nationality) {
        playerData.nationality = player.nationality
      } else {
        // Affiche "Unknown" si la nationalité n'est pas disponible
        playerData.nationality = "Unknown"
      }
      if (player.age) {
        playerData.age = player.age
      }
      if (player.position) {
        playerData.position = player.position
      }
      if (player.height) {
        playerData.height = player.height
      }
      if (player.scouting_report) {
        playerData.scouting_report = player.scouting_report
      }
      
      setMessages([
        { role: 'user', content: player.name },
        { role: 'ai', content: JSON.stringify(playerData, null, 2) }
      ])
    }
  }, [player])

  const handleSend = async () => {
    if (!inputValue.trim()) return

    const playerName = inputValue.trim()
    setInputValue('')
    setMessages(prev => [...prev, { role: 'user', content: playerName }])
    
    // Appelle la fonction de recherche de joueur
    onPlayerRequest(playerName)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="ai-assistant">
      <h2>IA Scouting Assistant</h2>
      
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="empty-chat">
            <p>Demandez un rapport sur un joueur</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-label">
              {msg.role === 'user' ? 'Vous:' : 'Agent IA:'}
            </div>
            <div className="message-content">
              {msg.role === 'ai' && msg.content.startsWith('{') ? (
                <pre>{msg.content}</pre>
              ) : (
                <p>{msg.content}</p>
              )}
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
          placeholder="Demandez un rapport sur"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
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

