# 🚀 Déploiement Rapide sur Vercel

## 📋 Vue d'ensemble

Votre application a deux parties :
- **Frontend** (React) → Vercel ✅
- **Backend** (FastAPI) → Railway ou Render ✅

## 🎯 Étapes Rapides

### 1️⃣ Déployer le Backend sur Railway (5 minutes)

1. **Créer un compte** : [https://railway.app](https://railway.app) (gratuit)

2. **Nouveau projet** :
   - Cliquez sur "New Project"
   - "Deploy from GitHub repo"
   - Sélectionnez votre repo : `Outils-IA-pour-scouting-football-`

3. **Configurer le service** :
   - Railway détecte automatiquement Python
   - **Root Directory** : `backend`
   - **Start Command** : `python -m uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Variables d'environnement** :
   - Settings → Variables
   - Ajoutez : `OPENAI_API_KEY` = votre clé API

5. **Notez l'URL** : `https://votre-app.railway.app` (visible dans les settings)

### 2️⃣ Déployer le Frontend sur Vercel (3 minutes)

1. **Créer un compte** : [https://vercel.com](https://vercel.com) (gratuit)

2. **Nouveau projet** :
   - "Add New Project"
   - Importez votre repo GitHub
   - **Root Directory** : `frontend`
   - **Framework Preset** : Vite
   - **Build Command** : `npm run build`
   - **Output Directory** : `dist`

3. **Variables d'environnement** :
   - Settings → Environment Variables
   - Ajoutez : `VITE_API_URL` = `https://votre-app.railway.app`

4. **Déployer** : Cliquez sur "Deploy"

### 3️⃣ Tester

- Frontend : `https://votre-app.vercel.app`
- Backend : `https://votre-app.railway.app/health`

## ✅ C'est tout !

Votre application est maintenant en ligne ! 🎉

## 🔧 Si ça ne fonctionne pas

1. **Vérifiez les variables d'environnement** dans Railway et Vercel
2. **Vérifiez l'URL du backend** dans `VITE_API_URL`
3. **Vérifiez les logs** dans Railway et Vercel pour les erreurs

## 📚 Documentation complète

Voir `DEPLOIEMENT_VERCEL.md` pour plus de détails.

