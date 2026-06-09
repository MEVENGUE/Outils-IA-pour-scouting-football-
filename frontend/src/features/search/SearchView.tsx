import { useApp } from '../../context/AppContext'

export default function SearchView() {
  const { searchPlayer, loading } = useApp()

  return (
    <div className="card" style={{ padding: '1.25rem' }}>
      <h2>Search Players</h2>
      <p style={{ color: 'var(--muted)' }}>
        Use the top search bar or enter a player name below to scrape live data from Transfermarkt,
        Wikidata, and stats services.
      </p>
      <form
        onSubmit={async (e) => {
          e.preventDefault()
          const form = e.target as HTMLFormElement
          const input = form.elements.namedItem('name') as HTMLInputElement
          await searchPlayer(input.value)
        }}
        style={{ display: 'flex', gap: '0.75rem', marginTop: '1rem' }}
      >
        <input className="input" name="name" placeholder="Kylian Mbappé" />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          Analyze
        </button>
      </form>
    </div>
  )
}
