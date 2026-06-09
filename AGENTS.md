# AGENTS.md

## Cursor Cloud specific instructions

X-scout is a football player scouting web app with two local services: a **FastAPI backend** (`backend/`) and a **React/Vite frontend** (`frontend/`). There is no Docker Compose, Makefile, or unified root test runner.

### Services

| Service | Command | URL |
|---------|---------|-----|
| Backend | `cd backend && python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000` | http://127.0.0.1:8000 |
| Frontend | `cd frontend && npm run dev -- --host 127.0.0.1 --port 5173` | http://127.0.0.1:5173 |

SQLite (`data/players.db`) is created automatically on first backend use; no separate DB process is needed.

### Environment variables

- Copy `.env.example` to `.env` at the repo root (or export in the shell) and set `OPENAI_API_KEY` for AI scouting reports and name normalization.
- The backend loads `.env` via `python-dotenv` from the **backend working directory**. Either run uvicorn from `backend/` with a `backend/.env`, or export `OPENAI_API_KEY` before starting the server.
- Optional frontend override: `VITE_API_URL` (defaults to `http://127.0.0.1:8000` in `frontend/src/App.tsx`).

Without `OPENAI_API_KEY`, the app still starts and scraping works; AI reports and enrichment are degraded.

### Lint / test / build

| Component | Lint | Test | Build |
|-----------|------|------|-------|
| Frontend | `cd frontend && npm run lint` | Not configured | `cd frontend && npm run build` |
| Backend | Not configured | Not configured | N/A (interpreted Python) |

Frontend lint currently reports 5 pre-existing `@typescript-eslint/no-explicit-any` errors in `Globe.tsx` and `AIScoutingAssistant.tsx`.

### Gotchas

- Use `python3` (not `python`) on Linux if `python` is unavailable.
- Player search hits external sites (Transfermarkt, Wikipedia); internet access is required for live scraping.
- Start both backend and frontend for end-to-end UI testing. Health check: `curl http://127.0.0.1:8000/health`.

See [README.md](README.md) for full setup and API documentation (`http://127.0.0.1:8000/docs`).
