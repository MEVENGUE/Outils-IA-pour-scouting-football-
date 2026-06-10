import { Send, Sparkles, X } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import './CopilotPanel.css'

const QUICK_ACTIONS = [
  'Génère un rapport scouting',
  'Analyse la valeur marchande',
  'Projection de carrière',
  'Risques contractuels',
  'Adéquation tactique',
]

interface CopilotPanelProps {
  open?: boolean
  onClose?: () => void
}

export default function CopilotPanel({ open = false, onClose }: CopilotPanelProps) {
  const { copilotMessages, sendCopilotMessage, copilotLoading, aiStatus, player } = useApp()
  const [input, setInput] = useState('')

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (!input.trim() || copilotLoading) return
    const value = input.trim()
    setInput('')
    await sendCopilotMessage(value)
  }

  return (
    <>
      {open && (
        <button
          type="button"
          className="copilot-overlay"
          aria-label="Fermer AI Copilot"
          onClick={onClose}
        />
      )}
      <aside className={`copilot glass ${open ? 'copilot--open' : ''}`}>
        <div className="copilot-header">
          <Sparkles size={18} />
          <div className="copilot-header-copy">
            <strong>AI Copilot</strong>
            <span>{player ? player.name : 'No player selected'}</span>
          </div>
          <span className={`badge ${aiStatus === 'ready' ? 'success' : 'warning'}`}>
            {aiStatus === 'ready' ? 'Online' : 'Limited'}
          </span>
          <button type="button" className="copilot-close" aria-label="Fermer" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="copilot-actions">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action}
              type="button"
              className="btn"
              onClick={() => sendCopilotMessage(action)}
              disabled={copilotLoading}
            >
              {action}
            </button>
          ))}
        </div>

        <div className="copilot-messages">
          {copilotMessages.map((message) => (
            <motion.div
              key={message.id}
              className={`copilot-message ${message.role}`}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
            >
              {message.thinking ? (
                <div className="thinking">
                  <span>Analyse en cours</span>
                  <div className="dots">
                    <i />
                    <i />
                    <i />
                  </div>
                </div>
              ) : (
                <>
                  <p>{message.content}</p>
                  {message.sources && message.sources.length > 0 && (
                    <div className="sources">
                      Sources: {message.sources.join(' · ')}
                    </div>
                  )}
                  {typeof message.confidence === 'number' && (
                    <div className="confidence">
                      Confidence: {Math.round(message.confidence * 100)}%
                    </div>
                  )}
                </>
              )}
            </motion.div>
          ))}
        </div>

        <form className="copilot-input" onSubmit={onSubmit}>
          <input
            className="input"
            placeholder="Ask about player, market, tactics..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={copilotLoading}
          />
          <button className="btn btn-primary" type="submit" disabled={copilotLoading || !input.trim()}>
            <Send size={16} />
          </button>
        </form>
      </aside>
    </>
  )
}
