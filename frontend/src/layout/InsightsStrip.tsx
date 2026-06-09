import { motion } from 'framer-motion'
import { useApp } from '../context/AppContext'
import './InsightsStrip.css'

export default function InsightsStrip() {
  const { activities } = useApp()

  if (activities.length === 0) {
    return (
      <div className="insights-strip glass">
        <span className="insights-empty">Live intelligence feed — search a player to begin</span>
      </div>
    )
  }

  return (
    <div className="insights-strip glass">
      <div className="insights-track">
        {activities.map((event) => (
          <motion.div
            key={event.id}
            className="insight-chip"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <span>{event.label}</span>
            {event.playerName && <strong>{event.playerName}</strong>}
            <time>{new Date(event.timestamp).toLocaleTimeString()}</time>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
