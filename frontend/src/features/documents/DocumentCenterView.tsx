import { useMemo, useState } from 'react'
import { Upload } from 'lucide-react'
import { analyzeDocumentText } from '../../api/ai'
import { useApp } from '../../context/AppContext'
import { extractTextFromFile, saveStoredDocuments } from '../../utils/storage'
import type { StoredDocument } from '../../types/player'

export default function DocumentCenterView() {
  const { documents, setDocuments, pushActivity } = useApp()
  const [query, setQuery] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const filtered = useMemo(() => {
    if (!query.trim()) return documents
    return documents.filter((doc) => doc.name.toLowerCase().includes(query.toLowerCase()))
  }, [documents, query])

  const onUpload = async (files: FileList | null) => {
    if (!files?.length) return
    setBusy(true)
    setError(null)

    for (const file of Array.from(files)) {
      const doc: StoredDocument = {
        id: `${Date.now()}-${file.name}`,
        name: file.name,
        type: file.type || file.name.split('.').pop() || 'unknown',
        size: file.size,
        uploadedAt: Date.now(),
        status: 'analyzing',
      }

      setDocuments((prev) => {
        const next = [doc, ...prev]
        saveStoredDocuments(next)
        return next
      })

      try {
        const text = await extractTextFromFile(file)
        const analysis = await analyzeDocumentText(file.name, text)
        setDocuments((prev) => {
          const next = prev.map((item) =>
            item.id === doc.id
              ? {
                  ...item,
                  status: 'complete' as const,
                  summary: analysis.summary,
                  insights: analysis.insights,
                }
              : item,
          )
          saveStoredDocuments(next)
          return next
        })
        pushActivity('Document analyzed', file.name)
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Analysis failed'
        setDocuments((prev) => {
          const next = prev.map((item) =>
            item.id === doc.id ? { ...item, status: 'error' as const, error: message } : item,
          )
          saveStoredDocuments(next)
          return next
        })
        setError(message)
      }
    }

    setBusy(false)
  }

  return (
    <div className="card view-card--compact">
      <div className="view-header">
        <div>
          <h2>Document Analysis Center</h2>
          <p>
            Upload TXT, CSV, MD, or PDF. Analysis runs through the existing `/ai` backend proxy.
          </p>
        </div>
        <div className="view-actions">
          <label className="btn btn-primary" style={{ cursor: 'pointer' }}>
            <Upload size={16} /> Upload
            <input
              type="file"
              hidden
              multiple
              accept=".txt,.csv,.md,.json,.pdf"
              onChange={(e) => onUpload(e.target.files)}
              disabled={busy}
            />
          </label>
        </div>
      </div>

      <input
        className="input"
        style={{ marginTop: '1rem' }}
        placeholder="Search documents..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />

      {error && <div className="error-banner" style={{ marginTop: '1rem' }}>{error}</div>}

      <div className="list-stack">
        {filtered.length === 0 ? (
          <div className="empty-state">No documents uploaded yet.</div>
        ) : (
          filtered.map((doc) => (
            <div key={doc.id} className="card" style={{ padding: '0.85rem' }}>
              <div className="view-header" style={{ marginBottom: 0 }}>
                <strong style={{ wordBreak: 'break-word' }}>{doc.name}</strong>
                <span className={`badge ${doc.status === 'complete' ? 'success' : doc.status === 'error' ? 'warning' : ''}`}>
                  {doc.status}
                </span>
              </div>
              <div style={{ color: 'var(--muted)', fontSize: '0.78rem', marginTop: '0.35rem' }}>
                {new Date(doc.uploadedAt).toLocaleString()} · {(doc.size / 1024).toFixed(1)} KB
              </div>
              {doc.summary && <p style={{ marginTop: '0.65rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{doc.summary}</p>}
              {doc.insights && doc.insights.length > 0 && (
                <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.1rem' }}>
                  {doc.insights.map((insight) => (
                    <li key={insight}>{insight}</li>
                  ))}
                </ul>
              )}
              {doc.error && <div className="error-banner" style={{ marginTop: '0.65rem' }}>{doc.error}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
