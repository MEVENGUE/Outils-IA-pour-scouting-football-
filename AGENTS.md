# AGENTS.md

## Cursor Cloud specific instructions

### Vue d'ensemble

X-SCOUT AI est une application full-stack monorepo (`backend/` + `frontend/`) pour le scouting football augmenté par IA. Deux processus locaux sont nécessaires pour le développement.

| Service | Port | Commande |
|---------|------|----------|
| Backend FastAPI | 8000 | `cd backend && python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000` |
| Frontend Vite | 5173 | `cd frontend && npm run dev` |

SQLite (`data/players.db`) est créée automatiquement au premier démarrage du backend. Pas de Docker ni docker-compose.

### Variables d'environnement

- `OPENAI_API_KEY` : lue depuis `.env` à la racine (copier `.env.example`). L'app démarre sans clé valide, mais les rapports IA et le copilot renvoient des erreurs.
- `VITE_API_URL` : optionnel dans `frontend/.env.local` ; défaut `http://127.0.0.1:8000` dans `frontend/src/api/config.ts`.

### Commandes utiles

Voir `README.md` pour le démarrage complet. Résumé :

```bash
# Lint frontend
cd frontend && npm run lint

# Build frontend
cd frontend && npm run build

# Health check backend
curl http://127.0.0.1:8000/health
```

Il n'y a pas de suite de tests automatisés ni de hooks pre-commit configurés dans ce dépôt.

### Pièges connus

- Après `pip install`, les binaires (`uvicorn`) sont dans `~/.local/bin` — préférer `python3 -m uvicorn` ou ajouter ce répertoire au `PATH`.
- Le scraping Transfermarkt peut être lent ou limité ; réessayer après quelques secondes si timeout.
- Sans joueurs en base, une recherche UI échoue jusqu'à un premier `POST /scrape-player` ou scrape via l'interface.
