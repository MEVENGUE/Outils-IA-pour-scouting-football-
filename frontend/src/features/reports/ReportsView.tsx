import { jsPDF } from 'jspdf'
import { Download } from 'lucide-react'
import { useApp } from '../../context/AppContext'

export default function ReportsView() {
  const { player, aiStatus } = useApp()

  const exportPdf = () => {
    if (!player?.scouting_report) return
    const doc = new jsPDF()
    const lines = doc.splitTextToSize(player.scouting_report, 180)
    doc.setFontSize(16)
    doc.text(`X-SCOUT Report — ${player.name}`, 14, 20)
    doc.setFontSize(11)
    doc.text(lines, 14, 32)
    doc.save(`xscout-${player.name.replace(/\s+/g, '-').toLowerCase()}.pdf`)
  }

  if (!player) {
    return <div className="card empty-state">Search a player to generate an AI scouting report.</div>
  }

  return (
    <div className="card view-card">
      <div className="view-header">
        <div>
          <h2>AI Scouting Report — {player.name}</h2>
          <p>
            Source: backend OpenAI integration {aiStatus === 'ready' ? '(active)' : '(limited)'}
          </p>
        </div>
        <div className="view-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={exportPdf}
            disabled={!player.scouting_report}
          >
            <Download size={16} /> Export PDF
          </button>
        </div>
      </div>

      {player.scouting_report ? (
        <article style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6, marginTop: '1rem', wordBreak: 'break-word' }}>
          {player.scouting_report}
        </article>
      ) : (
        <div className="empty-state" style={{ marginTop: '1rem' }}>
          {aiStatus === 'unconfigured'
            ? 'Configure OPENAI_API_KEY on the backend to generate reports.'
            : 'Report unavailable for this player. Ask the AI Copilot to generate one.'}
        </div>
      )}
    </div>
  )
}
