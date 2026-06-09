import { API_URL } from '../../api/config'
import { useSystemHealth } from '../../hooks/useSystemHealth'

export default function SettingsView() {
  const { data: health, isLoading } = useSystemHealth()

  return (
    <div className="card" style={{ padding: '1rem' }}>
      <h2>Settings</h2>
      <div style={{ display: 'grid', gap: '0.75rem', marginTop: '1rem' }}>
        <SettingRow label="API URL" value={API_URL} />
        <SettingRow label="Health" value={isLoading ? 'Checking…' : health?.status ?? 'Unknown'} />
        <SettingRow label="Database" value={health?.database ?? '—'} />
        <SettingRow label="OpenAI" value={health?.openai ?? '—'} />
      </div>
      <p style={{ color: 'var(--muted)', marginTop: '1rem', fontSize: '0.85rem' }}>
        Configure `OPENAI_API_KEY` on Railway and `VITE_API_URL` on Vercel for production.
      </p>
    </div>
  )
}

function SettingRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="card" style={{ padding: '0.75rem', display: 'flex', justifyContent: 'space-between' }}>
      <span>{label}</span>
      <code>{value}</code>
    </div>
  )
}
