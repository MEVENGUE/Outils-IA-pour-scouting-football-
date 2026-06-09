import { Code2, ExternalLink } from 'lucide-react'
import './AuthorView.css'

const LOGO_SRC = '/x-scout-logo.jpg'
const GITHUB_URL = 'https://github.com/MEVENGUE/Outils-IA-pour-scouting-football-'

export default function AuthorView() {
  return (
    <div className="author-view">
      <section className="author-hero card">
        <div className="author-logo-wrap">
          <img src={LOGO_SRC} alt="Logo X-SCOUT" className="author-logo" />
        </div>
        <div className="author-hero-copy">
          <p className="author-kicker">Informations auteur</p>
          <h2>FRANCK MEVENGUE</h2>
          <p className="author-role">Créateur &amp; développeur — X-SCOUT AI</p>
          <p className="author-bio">
            Plateforme intelligente de scouting footballistique combinant web scraping,
            intelligence artificielle et visualisation 3D pour l&apos;analyse de joueurs.
          </p>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary author-github"
          >
            <Code2 size={16} />
            Voir le dépôt GitHub
            <ExternalLink size={14} />
          </a>
        </div>
      </section>

      <section className="author-details card">
        <h3>À propos du projet</h3>
        <ul className="author-list">
          <li>Recherche multi-sources (Transfermarkt, Wikipedia, Wikidata)</li>
          <li>Rapports de scouting générés par IA (OpenAI)</li>
          <li>Cartographie 3D des nationalités et statistiques de performance</li>
          <li>Watchlist, comparaison de joueurs et centre documentaire</li>
        </ul>
        <p className="author-note">
          Logo officiel du projet — source : dossier <code>Logo/</code> du dépôt GitHub.
        </p>
      </section>
    </div>
  )
}
