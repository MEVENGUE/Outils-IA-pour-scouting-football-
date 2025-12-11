# X-scout - Dashboard Online Scouting

<div align="center">

![X-scout Logo](Logo/X-scout%20logo.jpg)

**Plateforme intelligente de scouting footballistique avec IA et visualisation 3D**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19.1.0-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://openai.com/)

</div>

## 📋 Table des matières

- [Description](#-description)
- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Technologies utilisées](#-technologies-utilisées)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Structure du projet](#-structure-du-projet)
- [API Endpoints](#-api-endpoints)
- [Fonctionnalités avancées](#-fonctionnalités-avancées)
- [Dépannage](#-dépannage)
- [Contribution](#-contribution)
- [Licence](#-licence)

## 🎯 Description

**X-scout** est une application web moderne de scouting footballistique qui combine le web scraping, l'intelligence artificielle et la visualisation 3D pour offrir une expérience complète d'analyse de joueurs.

L'application permet de :
- Rechercher et analyser des joueurs de football
- Visualiser leur nationalité sur un globe 3D interactif
- Générer des rapports de scouting professionnels avec l'IA
- Consulter des statistiques détaillées et des données enrichies

## ✨ Fonctionnalités

### 🔍 Recherche intelligente
- **Normalisation automatique des noms** : Corrige automatiquement les noms mal écrits, ajoute les accents manquants et trouve le bon joueur même avec des erreurs de saisie
- **Scraping multi-sources** : Récupère les données depuis Transfermarkt et Wikipedia
- **Enrichissement IA** : Complète automatiquement les données manquantes avec OpenAI

### 📊 Visualisation 3D
- **Globe interactif** : Visualise la nationalité des joueurs sur un globe 3D fluorescent (thème rouge)
- **Points de localisation** : Affiche un point rouge sur le pays du joueur
- **Effets visuels** : Animations et effets de lueur inspirés de Kaspersky Cybermap

### 🤖 Intelligence Artificielle
- **Rapports de scouting** : Génère des rapports professionnels détaillés avec analyse technique, statistique et prédictions
- **Assistant IA** : Chat interactif pour poser des questions sur les joueurs
- **Enrichissement de données** : Complète automatiquement les statistiques, nationalités et images manquantes

### 📈 Statistiques détaillées
- Buts, passes décisives, matchs joués
- Valeur marchande, club actuel, position
- Graphiques de performance (buts/match, passes/match)
- Contribution totale (buts + passes)

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │  React + TypeScript + Vite
│   (React)       │  react-globe.gl (3D)
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────┐
│   Backend       │  FastAPI (Python)
│   (FastAPI)     │  ├── API REST
└────────┬────────┘  ├── OpenAI Integration
         │           └── Database Management
┌────────▼────────┐
│   Scraping      │  BeautifulSoup + Requests
│   (Python)      │  ├── Transfermarkt
└────────┬────────┘  └── Wikipedia
         │
┌────────▼────────┐
│   Database      │  SQLite
│   (SQLite)      │  └── players.db
└─────────────────┘
```

## 🛠️ Technologies utilisées

### Backend
- **FastAPI** : Framework web moderne et rapide
- **SQLite** : Base de données relationnelle
- **BeautifulSoup4** : Parsing HTML pour le scraping
- **Requests** : Client HTTP pour les requêtes
- **OpenAI API** : Intelligence artificielle pour les rapports et l'enrichissement

### Frontend
- **React 19** : Bibliothèque UI
- **TypeScript** : Typage statique
- **Vite** : Build tool et dev server
- **react-globe.gl** : Visualisation 3D du globe
- **Three.js** : Moteur 3D sous-jacent

## 📦 Installation

### Prérequis

- **Python 3.8+** : [Télécharger Python](https://www.python.org/downloads/)
- **Node.js 18+** : [Télécharger Node.js](https://nodejs.org/)
- **npm** ou **yarn** : Gestionnaire de paquets Node.js
- **Clé API OpenAI** : [Obtenir une clé](https://platform.openai.com/api-keys)

### Étapes d'installation

1. **Cloner le repository** (ou télécharger le projet)
```bash
git clone <repository-url>
cd "Dashboard Online Scouting"
```

2. **Installer les dépendances Backend**
```bash
cd backend
pip install -r requirements.txt
```

3. **Installer les dépendances Frontend**
```bash
cd ../frontend
npm install
```

## ⚙️ Configuration

### Configuration OpenAI

⚠️ **IMPORTANT** : Pour des raisons de sécurité, la clé API OpenAI n'est **PAS** incluse dans le code source.

#### Méthode 1 : Fichier .env (Recommandé)

1. **Créer un fichier `.env`** à la racine du projet :
```bash
# À la racine du projet
touch .env
```

2. **Copier le contenu** de `.env.example` dans `.env` :
```bash
cp .env.example .env
```

3. **Éditer le fichier `.env`** et ajouter votre clé API :
```env
OPENAI_API_KEY=votre-clé-api-openai-ici
```

4. **Obtenir une clé API** : [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

#### Méthode 2 : Variable d'environnement système

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="votre-clé-api-openai"
```

**Windows (CMD):**
```cmd
set OPENAI_API_KEY=votre-clé-api-openai
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY="votre-clé-api-openai"
```

#### Vérification

Après configuration, vérifiez que la clé est bien chargée en démarrant le backend. Vous devriez voir :
- ✅ Si la clé est configurée : L'application démarre normalement
- ⚠️ Si la clé n'est pas configurée : Un message d'avertissement s'affiche

**Note** : Le fichier `.env` est automatiquement ignoré par Git (dans `.gitignore`) pour des raisons de sécurité.

### Configuration de l'API URL (Frontend)

Si le backend tourne sur un autre port, modifier `frontend/src/App.tsx` :
```typescript
const API_URL = 'http://127.0.0.1:8000'  // Modifier si nécessaire
```

## 🚀 Utilisation

### Démarrage de l'application

1. **Démarrer le Backend** (dans un terminal)
```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Le backend sera accessible sur : `http://127.0.0.1:8000`
- Documentation API : `http://127.0.0.1:8000/docs`
- Health check : `http://127.0.0.1:8000/health`

2. **Démarrer le Frontend** (dans un autre terminal)
```bash
cd frontend
npm run dev
```

Le frontend sera accessible sur : `http://localhost:5173`

### Utilisation de l'application

1. **Ouvrir** `http://localhost:5173` dans votre navigateur
2. **Rechercher un joueur** en tapant son nom dans la barre de recherche
3. **Visualiser** :
   - Les données du joueur dans le dossier
   - La nationalité sur le globe 3D
   - Le rapport de scouting généré par l'IA
4. **Interagir** avec l'assistant IA pour poser des questions sur le joueur

### Exemples de recherche

- `Kylian Mbappé` ou `Kylian Mbappe` (sans accent) → Trouve automatiquement le bon joueur
- `Jude Bellingham` ou `Jude Bellingam` (faute) → Corrige automatiquement
- `Pedri` → Trouve le joueur même avec un surnom
- `Lamine Yamal` → Affiche les données complètes

## 📁 Structure du projet

```
Dashboard Online Scouting/
│
├── backend/                 # Backend FastAPI
│   ├── main.py             # Application principale et endpoints API
│   ├── database.py         # Gestion centralisée de la base de données
│   ├── requirements.txt     # Dépendances Python
│   └── ...
│
├── frontend/                # Frontend React
│   ├── src/
│   │   ├── App.tsx         # Composant principal
│   │   ├── components/
│   │   │   ├── Globe.tsx   # Globe 3D interactif
│   │   │   ├── PlayerDossier.tsx  # Affichage des données joueur
│   │   │   └── AIScoutingAssistant.tsx  # Chat IA
│   │   └── ...
│   ├── package.json        # Dépendances Node.js
│   └── ...
│
├── scraping/                # Module de scraping
│   ├── scraper.py          # Scraping Transfermarkt et Wikipedia
│   └── players.db         # Base de données SQLite (générée automatiquement)
│
├── Logo/                    # Assets du projet
│   └── X-scout logo.jpg
│
└── README.md               # Ce fichier
```

## 🔌 API Endpoints

### Endpoints principaux

#### `GET /`
Page d'accueil de l'API avec les informations principales

#### `GET /health`
Vérification de l'état de santé de l'API et de la base de données

#### `POST /scrape-player`
Lance le scraping pour un joueur et retourne les données complètes

**Body:**
```json
{
  "player_name": "Kylian Mbappé"
}
```

**Response:**
```json
{
  "player": {
    "name": "Kylian Mbappé",
    "age": 25,
    "nationality": "France",
    "current_club": "Real Madrid",
    "position": "Attaquant",
    "market_value": "€180.00m",
    "goals": 45,
    "assists": 12,
    "appearances": 38,
    "image_url": "https://...",
    "scouting_report": "## Rapport de Scouting..."
  }
}
```

#### `GET /players`
Liste tous les joueurs avec filtres optionnels

**Query parameters:**
- `name` : Filtrer par nom
- `country` : Filtrer par pays
- `position` : Filtrer par position
- `max_age` : Filtrer par âge maximum

#### `GET /players/{player_id}`
Récupère un joueur par son ID

#### `GET /player-by-name/{player_name}`
Récupère un joueur par son nom (recherche partielle)

#### `GET /countries`
Liste tous les pays des joueurs enregistrés

#### `POST /ai`
Proxy pour les requêtes vers l'API OpenAI (utilisé par le frontend)

### Documentation interactive

Accédez à la documentation Swagger complète sur : `http://127.0.0.1:8000/docs`

## 🎨 Fonctionnalités avancées

### Normalisation automatique des noms

Le système utilise OpenAI pour corriger automatiquement :
- **Accents manquants** : `Kylian Mbappe` → `Kylian Mbappé`
- **Fautes d'orthographe** : `Jude Bellingam` → `Jude Bellingham`
- **Noms incomplets** : Conserve les surnoms connus (`Pedri` reste `Pedri`)

### Enrichissement intelligent

Si des données manquent après le scraping, OpenAI complète automatiquement :
- Statistiques (buts, passes, matchs)
- Nationalité
- Image du joueur

### Rapports de scouting IA

Chaque joueur reçoit un rapport professionnel incluant :
1. **Analyse technique** : Forces, faiblesses, style de jeu
2. **Analyse statistique** : Interprétation des performances
3. **Potentiel & valeur marchande** : Évaluation et projection
4. **Recommandations stratégiques** : Clubs/ligues adaptés
5. **Prédictions** : Tendances futures probables

### Globe 3D interactif

- **Thème fluorescent rouge** : Inspiré de Kaspersky Cybermap
- **Points de localisation** : Affiche le pays du joueur avec un point rouge
- **Animations** : Effets de lueur et animations fluides
- **Interactivité** : Rotation et zoom avec la souris

## 🐛 Dépannage

### Le backend ne démarre pas

1. Vérifier que Python 3.8+ est installé
2. Vérifier que les dépendances sont installées : `pip install -r requirements.txt`
3. Vérifier que le port 8000 n'est pas déjà utilisé

### Le frontend ne se connecte pas au backend

1. Vérifier que le backend tourne sur `http://127.0.0.1:8000`
2. Vérifier l'URL dans `frontend/src/App.tsx`
3. Vérifier les logs du backend pour les erreurs CORS

### Erreurs de scraping

1. Vérifier votre connexion internet
2. Transfermarkt peut bloquer les requêtes trop fréquentes (attendre quelques secondes)
3. Vérifier que le nom du joueur est correct (la normalisation IA devrait aider)

### Erreurs OpenAI

1. **Vérifier que la clé API est configurée** :
   - Vérifiez que le fichier `.env` existe et contient `OPENAI_API_KEY=votre-clé`
   - Ou vérifiez que la variable d'environnement `OPENAI_API_KEY` est définie
   - Voir la section [Configuration OpenAI](#-configuration-openai) dans le README

2. **Vérifier que votre clé API OpenAI est valide** :
   - Testez votre clé sur [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Assurez-vous qu'elle n'a pas expiré

3. **Vérifier votre quota OpenAI** :
   - Vérifiez votre quota sur [https://platform.openai.com/usage](https://platform.openai.com/usage)

4. **Vérifier votre connexion internet**

### Base de données corrompue

Supprimer `scraping/players.db` et relancer l'application (la base sera recréée automatiquement)

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👨‍💻 Auteur

**MEVENGUE Franck**

## 🙏 Remerciements

- **Transfermarkt** : Source de données des joueurs
- **Wikipedia** : Source des images
- **OpenAI** : Intelligence artificielle pour les rapports
- **react-globe.gl** : Bibliothèque de visualisation 3D

---

<div align="center">

**Fait avec ❤️ pour le football**

⭐ Si ce projet vous a aidé, n'hésitez pas à lui donner une étoile !

</div>

