# 🚀 Guide de Déploiement sur Vercel

Ce guide explique comment déployer l'application X-scout sur Vercel.

## ⚠️ Architecture et Limitations

### Structure de l'application
- **Frontend** : React + Vite (peut être déployé sur Vercel)
- **Backend** : FastAPI (Python) - nécessite une solution alternative
- **Base de données** : SQLite (ne fonctionne pas sur Vercel - read-only)

### Options de déploiement

#### Option 1 : Frontend sur Vercel + Backend séparé (Recommandé)
- Frontend React → Vercel
- Backend FastAPI → Railway, Render, ou Fly.io
- Base de données → SQLite (local) ou PostgreSQL (cloud)

#### Option 2 : Tout sur Vercel (avec limitations)
- Frontend → Vercel
- Backend → Vercel Serverless Functions (Python)
- Base de données → Base externe (PostgreSQL, Supabase, etc.)

## 📋 Prérequis

1. Compte Vercel : [https://vercel.com](https://vercel.com)
2. Compte pour le backend (Railway, Render, ou Fly.io)
3. Clé API OpenAI configurée
4. Git repository sur GitHub (déjà fait ✅)

## 🎯 Option 1 : Déploiement Hybride (Recommandé)

### Étape 1 : Déployer le Backend sur Railway

1. **Créer un compte Railway** : [https://railway.app](https://railway.app)

2. **Créer un nouveau projet** :
   - Cliquez sur "New Project"
   - Sélectionnez "Deploy from GitHub repo"
   - Choisissez votre repository

3. **Configurer le service** :
   - Railway détectera automatiquement le backend Python
   - Créez un service pour le dossier `backend/`

4. **Variables d'environnement** :
   - Dans les settings du service, ajoutez :
     ```
     OPENAI_API_KEY=votre-clé-api-openai
     ```

5. **Port et commande de démarrage** :
   - Railway utilisera automatiquement le port fourni
   - Commande : `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT`

6. **Notez l'URL du backend** : `https://votre-app.railway.app`

### Étape 2 : Déployer le Frontend sur Vercel

1. **Installer Vercel CLI** (optionnel) :
```bash
npm install -g vercel
```

2. **Créer `vercel.json`** à la racine du projet :
```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "env": {
    "VITE_API_URL": "https://votre-app.railway.app"
  }
}
```

3. **Modifier `frontend/vite.config.ts`** :
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
  define: {
    // Utilise la variable d'environnement ou l'URL par défaut
    'import.meta.env.VITE_API_URL': JSON.stringify(
      process.env.VITE_API_URL || 'https://votre-app.railway.app'
    ),
  },
})
```

4. **Modifier `frontend/src/App.tsx`** :
```typescript
// Remplacer la ligne :
const API_URL = 'http://127.0.0.1:8000'

// Par :
const API_URL = import.meta.env.VITE_API_URL || 'https://votre-app.railway.app'
```

5. **Créer `frontend/vercel.json`** :
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

6. **Déployer via GitHub** :
   - Allez sur [vercel.com](https://vercel.com)
   - Cliquez sur "Add New Project"
   - Importez votre repository GitHub
   - **Root Directory** : `frontend`
   - **Framework Preset** : Vite
   - **Build Command** : `npm run build`
   - **Output Directory** : `dist`
   - **Environment Variables** :
     ```
     VITE_API_URL=https://votre-app.railway.app
     ```

7. **Déployer** : Vercel déploiera automatiquement

## 🎯 Option 2 : Tout sur Vercel (Serverless)

### Étape 1 : Convertir le Backend en Serverless Functions

1. **Créer `api/` à la racine** :
```
api/
  ├── __init__.py
  ├── main.py (copie de backend/main.py)
  └── requirements.txt
```

2. **Créer `vercel.json`** :
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/main.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "dist"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "api/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/$1"
    }
  ],
  "env": {
    "OPENAI_API_KEY": "@openai_api_key"
  }
}
```

3. **Adapter `api/main.py`** pour Vercel :
```python
# Ajouter à la fin de main.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

⚠️ **Note** : Cette approche a des limitations (timeout, SQLite read-only, etc.)

## 🔧 Configuration des Variables d'Environnement

### Sur Vercel

1. Allez dans **Settings** → **Environment Variables**
2. Ajoutez :
   - `VITE_API_URL` : URL de votre backend (Railway, Render, etc.)
   - `OPENAI_API_KEY` : (si backend sur Vercel)

### Sur Railway/Render

1. Allez dans **Variables** ou **Environment**
2. Ajoutez :
   - `OPENAI_API_KEY` : Votre clé API OpenAI

## 📝 Modifications nécessaires dans le code

### 1. Modifier `frontend/src/App.tsx`

```typescript
// Remplacer :
const API_URL = 'http://127.0.0.1:8000'

// Par :
const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
```

### 2. Modifier `backend/main.py` pour CORS

Assurez-vous que CORS autorise votre domaine Vercel :

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://votre-app.vercel.app",  # Ajoutez votre domaine Vercel
        "https://*.vercel.app"  # Ou tous les sous-domaines Vercel
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Créer `frontend/.vercelignore` (optionnel)

```
node_modules
dist
.env
.env.local
```

## 🚀 Déploiement Rapide (via CLI)

### Frontend uniquement

```bash
cd frontend
npm install -g vercel
vercel login
vercel --prod
```

### Avec configuration

```bash
# À la racine du projet
vercel --prod
```

## 🔍 Vérification après déploiement

1. **Frontend** : Visitez `https://votre-app.vercel.app`
2. **Backend** : Testez `https://votre-backend.railway.app/health`
3. **API** : Testez `https://votre-backend.railway.app/docs`

## 🐛 Dépannage

### Erreur CORS

- Vérifiez que le backend autorise le domaine Vercel
- Vérifiez que `VITE_API_URL` est correctement configuré

### Erreur 404 sur les routes

- Vérifiez la configuration des `rewrites` dans `vercel.json`
- Assurez-vous que le build génère `index.html` dans `dist/`

### Backend non accessible

- Vérifiez l'URL dans `VITE_API_URL`
- Vérifiez que le backend est bien déployé et accessible
- Testez l'endpoint `/health` du backend

### Variables d'environnement non chargées

- Vérifiez que les variables commencent par `VITE_` pour le frontend
- Redéployez après avoir ajouté des variables

## 📚 Ressources

- [Documentation Vercel](https://vercel.com/docs)
- [Vercel + Vite](https://vercel.com/docs/frameworks/vite)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)

## ✅ Checklist de déploiement

- [ ] Backend déployé sur Railway/Render
- [ ] Variables d'environnement configurées (OPENAI_API_KEY)
- [ ] CORS configuré pour autoriser Vercel
- [ ] `frontend/src/App.tsx` modifié pour utiliser `VITE_API_URL`
- [ ] `vercel.json` créé (si nécessaire)
- [ ] Frontend déployé sur Vercel
- [ ] Variables d'environnement Vercel configurées (VITE_API_URL)
- [ ] Application testée en production

---

**Note** : Pour une solution complète et recommandée, utilisez **Option 1** (Frontend sur Vercel + Backend sur Railway/Render).

