import { useApp } from '../../context/AppContext'

export default function SearchView() {
  const { searchPlayer, loading } = useApp()

  return (
    <div className="card view-card">
      <h2>Search Players</h2>
      <p style={{ color: 'var(--muted)' }}>
        Use the top search bar or enter a player name below to scrape live data from Transfermarkt,
        Wikidata, and stats services.
      </p>
      <form
        className="search-form-row"
        onSubmit={async (e) => {
          e.preventDefault()
          const form = e.target as HTMLFormElement
          const input = form.elements.namedItem('name') as HTMLInputElement
          await searchPlayer(input.value)
        }}
      >
        <input className="input" name="name" placeholder="Kylian Mbappé" />
        <button className="btn btn-primary" type="submit" disabled={loading}>
          Analyze
        </button>
      </form>
    </div>
  )
}
