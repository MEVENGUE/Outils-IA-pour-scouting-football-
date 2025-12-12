# Filename: backend/main.py
# Description: API FastAPI unifiée pour servir les données de scouting et l'IA.

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
import requests
import sys
import os
import json
import re

# Ajoute le dossier de scraping au path pour pouvoir importer les fonctions
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scraping'))
from scraping.scraper import scrape_and_save_player_data

# Import du module de base de données centralisé
from database import (
    get_db_connection, 
    init_db, 
    save_player_to_db, 
    update_player_field,
    get_player_by_name as db_get_player_by_name,
    get_player_by_id as db_get_player_by_id,
    list_players as db_list_players
)

app = FastAPI(title="Unified Scouting API", version="3.0")

# --- Middleware CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Développement local
        "http://127.0.0.1:5173",  # Développement local
        "https://scoutfootballai-siteweb.vercel.app",# Ajoutez votre domaine Vercel spécifique ici si nécessaire
        # "https://votre-app.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration Base de Données & IA ---
# ⚠️ SÉCURITÉ : Ne pas commiter la clé API dans le code !
# Configurez votre clé API OpenAI via une variable d'environnement ou un fichier .env
# Pour obtenir une clé : https://platform.openai.com/api-keys
import os
from dotenv import load_dotenv

# Charge les variables d'environnement depuis un fichier .env (si présent)
load_dotenv()

# Récupère la clé API depuis la variable d'environnement
# Si la variable n'existe pas, utilise une valeur par défaut vide (à configurer)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Vérification que la clé API est configurée
if not OPENAI_API_KEY:
    print("⚠️  ATTENTION: OPENAI_API_KEY n'est pas configurée!")
    print("   Configurez-la via une variable d'environnement ou un fichier .env")
    print("   Voir README.md pour plus d'informations")

# --- Route racine ---
@app.get("/")
def root():
    """Page d'accueil de l'API avec les informations principales."""
    return {
        "message": "Bienvenue sur l'API Unified Scouting",
        "version": "3.0",
        "endpoints": {
            "documentation": "/docs",
            "players": "/players",
            "player_by_id": "/players/{player_id}",
            "countries": "/countries",
            "scrape_player": "/scrape-player (POST)",
            "ai_proxy": "/ai (POST)"
        },
        "status": "running"
    }

@app.get("/health")
def health_check():
    """Vérification de l'état de santé de l'API."""
    try:
        # Vérifie la connexion à la base de données
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

# --- Endpoints de l'IA ---
@app.post("/ai")
async def ai_proxy(request: Request):
    """Proxy pour les requêtes vers l'API OpenAI."""
    body = await request.json()
    try:
        # Adaptation du format pour OpenAI Chat Completions
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Si le body contient déjà un format OpenAI, on l'utilise tel quel
        # Sinon, on adapte depuis un format générique
        if "messages" not in body:
            # Conversion depuis un format générique vers OpenAI
            if "prompt" in body or "contents" in body:
                prompt = body.get("prompt") or (body.get("contents", [{}])[0].get("parts", [{}])[0].get("text", ""))
                openai_body = {
                    "model": body.get("model", "gpt-3.5-turbo"),
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": body.get("temperature", 0.7),
                    "max_tokens": body.get("max_tokens", 1000)
                }
            else:
                openai_body = body
        else:
            openai_body = body
        
        resp = requests.post(OPENAI_API_URL, json=openai_body, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as err:
        raise HTTPException(status_code=err.response.status_code, detail=err.response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Endpoint de Scraping à la demande ---
class PlayerRequest(BaseModel):
    player_name: str

def normalize_country_name_with_openai(country_name):
    """Normalise le nom d'un pays avec OpenAI pour correspondre au mapping du globe."""
    if not country_name:
        return None
    
    # Mapping simple pour les cas courants
    country_mapping = {
        "Espagne": "Spain",
        "Angleterre": "England",
        "Allemagne": "Germany",
        "Italie": "Italy",
        "Brésil": "Brazil",
        "Argentine": "Argentina",
        "Belgique": "Belgium",
        "Pays-Bas": "Netherlands",
        "Croatie": "Croatia",
        "Maroc": "Morocco",
        "Sénégal": "Senegal",
        "Côte d'Ivoire": "Ivory Coast",
        "Cameroun": "Cameroon",
        "Égypte": "Egypt",
        "Algérie": "Algeria",
        "Tunisie": "Tunisia",
        "Japon": "Japan",
        "Corée du Sud": "South Korea",
        "Chine": "China",
        "États-Unis": "United States",
        "USA": "United States",
        "Mexique": "Mexico",
        "Colombie": "Colombia",
        "Chili": "Chile",
        "Pérou": "Peru",
        "Équateur": "Ecuador",
        "Russie": "Russia",
        "Pologne": "Poland",
        "Suède": "Sweden",
        "Norvège": "Norway",
        "Danemark": "Denmark",
        "Suisse": "Switzerland",
        "Autriche": "Austria",
        "République tchèque": "Czech Republic",
        "Grèce": "Greece",
        "Turquie": "Turkey",
        "Israël": "Israel",
        "Arabie saoudite": "Saudi Arabia",
        "Émirats arabes unis": "United Arab Emirates",
        "Australie": "Australia",
        "Nouvelle-Zélande": "New Zealand",
        "Afrique du Sud": "South Africa",
    }
    
    # Vérifie d'abord le mapping simple
    if country_name in country_mapping:
        return country_mapping[country_name]
    
    # Si le nom est déjà en anglais, le retourne tel quel
    if country_name in ["Spain", "England", "Germany", "Italy", "Brazil", "Argentina", "France", 
                        "Belgium", "Netherlands", "Croatia", "Morocco", "Senegal", "Japan", 
                        "United States", "Mexico", "Colombia", "Chile", "Peru", "Ecuador", 
                        "Russia", "Poland", "Sweden", "Norway", "Denmark", "Switzerland", 
                        "Austria", "Czech Republic", "Greece", "Turkey", "Israel", "Saudi Arabia",
                        "United Arab Emirates", "Australia", "New Zealand", "South Africa",
                        "Cameroon", "Egypt", "Algeria", "Tunisia", "South Korea", "China",
                        "Ivory Coast", "Nigeria", "Ghana"]:
        return country_name
    
    # Utilise OpenAI pour normaliser si nécessaire
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Normalise le nom de ce pays en anglais (format standard): "{country_name}"
Réponds UNIQUEMENT avec le nom du pays en anglais, sans explication, sans guillemets, sans ponctuation.
Exemples: "Espagne" -> "Spain", "Angleterre" -> "England", "États-Unis" -> "United States"
Réponds uniquement le nom normalisé:"""
        
        openai_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 20
        }
        
        resp = requests.post(OPENAI_API_URL, json=openai_body, headers=headers, timeout=5)
        resp.raise_for_status()
        response_data = resp.json()
        normalized = response_data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        # Nettoie la réponse (enlève guillemets, points, etc.)
        normalized = normalized.strip('"\'.,;!?')
        return normalized if normalized else country_name
    except Exception as e:
        print(f"Erreur lors de la normalisation du pays {country_name}: {e}")
        return country_name

def generate_scouting_report_with_openai(player_data):
    """Génère un rapport de scouting détaillé avec OpenAI basé sur les données du joueur, incluant analyses avancées et prédictions."""
    if not player_data:
        return None
    
    try:
        # Calcul de statistiques avancées
        appearances = player_data.get('appearances', 0) or 0
        goals = player_data.get('goals', 0) or 0
        assists = player_data.get('assists', 0) or 0
        
        goals_per_match = round(goals / appearances, 2) if appearances > 0 else 0
        assists_per_match = round(assists / appearances, 2) if appearances > 0 else 0
        goal_contribution = goals + assists
        
        # Construction du prompt enrichi pour OpenAI
        prompt = f"""Tu es un expert en scouting footballistique et analyste de données sportives. Analyse les données suivantes d'un joueur et génère un rapport de scouting professionnel et détaillé en français avec des insights avancés.

DONNÉES DU JOUEUR:
- Nom: {player_data.get('name', 'N/A')}
- Âge: {player_data.get('age', 'N/A')} ans
- Nationalité: {player_data.get('nationality', 'N/A')}
- Club actuel: {player_data.get('current_club', 'N/A')}
- Poste (Transfermarkt): {player_data.get('position_tm', player_data.get('position', 'N/A'))}
- Poste (FBref): {player_data.get('position_fbref', 'N/A')}
- Poste affiché: {player_data.get('position', 'N/A')}
- Taille: {player_data.get('height', 'N/A')}
- Valeur marchande: {player_data.get('market_value', 'N/A')}

STATISTIQUES DE PERFORMANCE:
- Buts: {goals}
- Passes décisives: {assists}
- Matchs joués: {appearances}
- Buts par match: {goals_per_match}
- Passes décisives par match: {assists_per_match}
- Contribution totale (buts + passes): {goal_contribution}

Génère un rapport de scouting professionnel et complet qui inclut:
1. ANALYSE TECHNIQUE: Forces et faiblesses du joueur, style de jeu, caractéristiques techniques détaillées
2. ANALYSE STATISTIQUE: Interprétation des performances, comparaison avec les standards du poste, efficacité
3. POTENTIEL & VALEUR MARCHANDE: Évaluation de la valeur actuelle, potentiel d'évolution, projection de carrière
4. RECOMMANDATIONS STRATÉGIQUES: Pour quels types de clubs/ligues ce joueur serait adapté, scénarios de transfert possibles
5. PRÉDICTIONS: Tendances futures probables (évolution de valeur, opportunités de transfert, développement)

Le rapport doit être en français, très professionnel, détaillé (environ 400-500 mots) et inclure des insights basés sur les données fournies."""

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        openai_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Tu es un expert en scouting footballistique, analyste de données sportives et consultant en transferts avec une connaissance approfondie du football moderne, des marchés de transferts et de l'analyse statistique."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1200
        }
        
        resp = requests.post(OPENAI_API_URL, json=openai_body, headers=headers)
        resp.raise_for_status()
        response_data = resp.json()
        
        # Extrait le texte de la réponse OpenAI
        report = response_data.get('choices', [{}])[0].get('message', {}).get('content', '')
        return report.strip()
    except Exception as e:
        print(f"Erreur lors de la génération du rapport OpenAI: {e}")
        return None

def enrich_player_data_with_openai(player_data):
    """Enrichit les données du joueur avec OpenAI si certaines informations manquent."""
    if not player_data or not player_data.get('name'):
        return player_data
    
    # Vérifie si des données importantes manquent
    needs_enrichment = (
        (not player_data.get('goals') or player_data.get('goals') == 0) and
        (not player_data.get('assists') or player_data.get('assists') == 0) and
        (not player_data.get('appearances') or player_data.get('appearances') == 0)
    ) or not player_data.get('image_url') or not player_data.get('nationality')
    
    if not needs_enrichment:
        return player_data
    
    try:
        missing_fields = []
        if not player_data.get('goals') or player_data.get('goals') == 0:
            missing_fields.append("goals")
        if not player_data.get('assists') or player_data.get('assists') == 0:
            missing_fields.append("assists")
        if not player_data.get('appearances') or player_data.get('appearances') == 0:
            missing_fields.append("appearances")
        if not player_data.get('image_url'):
            missing_fields.append("image_url")
        if not player_data.get('nationality'):
            missing_fields.append("nationality")
        
        prompt = f"""Tu es un expert en données footballistiques. Fournis les informations manquantes pour ce joueur en format JSON strict.

Joueur: {player_data.get('name', 'N/A')}
Club: {player_data.get('current_club', 'N/A')}
Poste (Transfermarkt): {player_data.get('position_tm', player_data.get('position', 'N/A'))}
Poste (FBref): {player_data.get('position_fbref', 'N/A')}
Poste affiché: {player_data.get('position', 'N/A')}

IMPORTANT: Pour la nationalité, utilise le nom du pays en français ou en anglais (ex: "Espagne" ou "Spain", "France" ou "France", "Cameroun" ou "Cameroon"). 
Si le joueur est bien connu (comme Lamine Yamal qui est espagnol), fournis sa vraie nationalité.

Réponds UNIQUEMENT avec un JSON valide contenant les champs manquants parmi:
{{
  "goals": nombre_de_buts_ou_0,
  "assists": nombre_de_passes_ou_0,
  "appearances": nombre_de_matchs_ou_0,
  "image_url": "url_de_l_image_ou_null",
  "nationality": "nom_du_pays_en_anglais_ou_francais"
}}

Champs à remplir: {', '.join(missing_fields)}
Si tu ne connais pas une valeur, mets 0 pour les nombres, null pour l'URL, ou "Unknown" pour la nationalité SEULEMENT si tu es vraiment incertain. Réponds uniquement le JSON, sans texte supplémentaire."""

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        openai_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 200
        }
        
        resp = requests.post(OPENAI_API_URL, json=openai_body, headers=headers, timeout=10)
        resp.raise_for_status()
        response_data = resp.json()
        enriched_text = response_data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        
        # Nettoie la réponse (enlève les markdown code blocks si présents)
        enriched_text = re.sub(r'```json\s*', '', enriched_text)
        enriched_text = re.sub(r'```\s*', '', enriched_text)
        enriched_text = enriched_text.strip()
        
        try:
            enriched_data = json.loads(enriched_text)
            # Met à jour seulement les champs manquants
            if 'goals' in enriched_data and (not player_data.get('goals') or player_data.get('goals') == 0):
                player_data['goals'] = enriched_data.get('goals', 0)
            if 'assists' in enriched_data and (not player_data.get('assists') or player_data.get('assists') == 0):
                player_data['assists'] = enriched_data.get('assists', 0)
            if 'appearances' in enriched_data and (not player_data.get('appearances') or player_data.get('appearances') == 0):
                player_data['appearances'] = enriched_data.get('appearances', 0)
            if 'image_url' in enriched_data and not player_data.get('image_url'):
                player_data['image_url'] = enriched_data.get('image_url')
            if 'nationality' in enriched_data and not player_data.get('nationality'):
                nationality = enriched_data.get('nationality')
                if nationality and nationality.lower() != 'unknown' and nationality.lower() != 'null':
                    player_data['nationality'] = nationality
                    print(f"-> Nationalité enrichie avec OpenAI: {nationality}")
                    # Sauvegarde la nationalité dans la base de données
                    update_player_field(player_data.get('name'), 'nationality', nationality)
            print(f"-> Données enrichies avec OpenAI pour {player_data.get('name')}")
        except json.JSONDecodeError as e:
            print(f"-> Erreur parsing JSON OpenAI: {e}")
    except Exception as e:
        print(f"-> Erreur lors de l'enrichissement OpenAI: {e}")
    
    return player_data

@app.post("/scrape-player")
def trigger_player_scraping(player_req: PlayerRequest):
    """
    Lance le scraping pour un joueur, sauvegarde les données dans la DB,
    génère un rapport de scouting avec OpenAI, normalise les données, et retourne les données complètes.
    """
    if not player_req.player_name:
        raise HTTPException(status_code=400, detail="Player name is required")
    
    try:
        # Scraping des données du joueur
        player_data = scrape_and_save_player_data(player_req.player_name)
        if not player_data:
            raise HTTPException(status_code=404, detail=f"Could not find or scrape data for player: {player_req.player_name}")

        # Vérifie si la sauvegarde en DB a réussi (si pas d'ID, la DB a probablement échoué)
        # Note: scrape_and_save_player_data retourne les données même si la DB échoue
        # On vérifie donc si les données ont été sauvegardées en essayant de les récupérer
        try:
            from database import get_player_by_name
            saved_player = get_player_by_name(player_data.get('name'))
            if not saved_player:
                # Les données ont été scrapées mais pas sauvegardées en DB
                print(f"⚠️ ATTENTION: Données scrapées pour {player_data.get('name')} mais sauvegarde DB échouée")
                # On continue quand même, mais on log l'erreur
        except Exception as db_check_error:
            print(f"⚠️ Erreur lors de la vérification DB: {db_check_error}")
            # On continue quand même pour ne pas bloquer l'utilisateur
        
        # Enrichit les données manquantes avec OpenAI
        player_data = enrich_player_data_with_openai(player_data)
        
        # Normalise le nom du pays pour le globe
        if player_data.get('nationality') and player_data['nationality'].lower() != 'unknown':
            normalized_nationality = normalize_country_name_with_openai(player_data['nationality'])
            player_data['nationality'] = normalized_nationality or player_data['nationality']
        elif not player_data.get('nationality') or player_data.get('nationality', '').lower() == 'unknown':
            # Si la nationalité est "Unknown", essaie de la trouver avec OpenAI en utilisant le nom et le club
            print(f"-> Tentative de trouver la nationalité pour {player_data.get('name')} via OpenAI...")
            try:
                nationality_prompt = f"""Quelle est la nationalité de {player_data.get('name', 'N/A')} qui joue pour {player_data.get('current_club', 'N/A')}? 
Réponds UNIQUEMENT avec le nom du pays en français ou en anglais (ex: "Espagne" ou "Spain", "France", "Cameroun" ou "Cameroon").
Si tu ne connais pas, réponds "Unknown". Réponds uniquement le nom du pays, sans texte supplémentaire."""
                
                headers = {
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                openai_body = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "user", "content": nationality_prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 20
                }
                
                resp = requests.post(OPENAI_API_URL, json=openai_body, headers=headers, timeout=10)
                resp.raise_for_status()
                response_data = resp.json()
                found_nationality = response_data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                
                # Nettoie la réponse
                found_nationality = re.sub(r'["\']', '', found_nationality).strip()
                
                if found_nationality and found_nationality.lower() != 'unknown':
                    player_data['nationality'] = found_nationality
                    print(f"-> Nationalité trouvée via OpenAI: {found_nationality}")
                    # Normalise la nationalité trouvée
                    normalized_nationality = normalize_country_name_with_openai(found_nationality)
                    player_data['nationality'] = normalized_nationality or found_nationality
            except Exception as e:
                print(f"-> Erreur lors de la recherche de nationalité: {e}")
        
        # Génération du rapport de scouting avec OpenAI
        scouting_report = generate_scouting_report_with_openai(player_data)
        if scouting_report:
            player_data['scouting_report'] = scouting_report
            # Sauvegarde le rapport dans la base de données
            update_player_field(player_data.get('name'), 'scouting_report', scouting_report)
        
        # S'assure que toutes les valeurs numériques sont correctes
        if 'goals' not in player_data or player_data['goals'] is None:
            player_data['goals'] = 0
        if 'assists' not in player_data or player_data['assists'] is None:
            player_data['assists'] = 0
        if 'appearances' not in player_data or player_data['appearances'] is None:
            player_data['appearances'] = 0
        
        # S'assure que l'image_url est présent (même si vide)
        if 'image_url' not in player_data:
            player_data['image_url'] = None
        
        # S'assure que la nationalité est présente (même si "Unknown")
        if 'nationality' not in player_data or not player_data['nationality']:
            player_data['nationality'] = "Unknown"
            print(f"-> Attention: Nationalité non trouvée pour {player_data.get('name')}, mise à 'Unknown'")
        
        # Met à jour la base de données avec toutes les données enrichies
        if player_data.get('nationality'):
            update_player_field(player_data.get('name'), 'nationality', player_data['nationality'])
        
        return {"player": player_data}
    except HTTPException:
        raise
    except Exception as e:
        # Log l'erreur complète côté serveur pour le débogage
        import traceback
        error_trace = traceback.format_exc()
        print(f"Erreur de scraping pour {player_req.player_name}: {e}")
        print(f"Traceback complet:\n{error_trace}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erreur lors du scraping: {str(e)}. Vérifiez les logs serveur pour plus de détails."
        )

# --- Endpoints de Données Joueurs ---
@app.get("/players")
def list_players(name: str = None, country: str = None, position: str = None, max_age: int = None):
    """
    Récupère la liste des joueurs, éventuellement filtrée par nom, nationalité, poste ou âge maximum.
    """
    filters = {}
    if name:
        filters['name'] = name
    if country:
        filters['country'] = country
    if position:
        filters['position'] = position
    if max_age:
        filters['max_age'] = max_age
    
    players = db_list_players(filters if filters else None)
    return {"players": players}

@app.get("/players/{player_id}")
def get_player(player_id: int):
    """
    Récupère le détail d'un joueur par son ID.
    """
    player = db_get_player_by_id(player_id)
    if player:
        return {"player": player}
    else:
        raise HTTPException(status_code=404, detail="Player not found")

@app.get("/countries")
def list_countries():
    """
    Récupère toutes les nationalités de joueurs présentes et leur nombre de joueurs.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nationality, COUNT(*) as count FROM players GROUP BY nationality")
    rows = cur.fetchall()
    conn.close()
    countries = []
    for row in rows:
        country = row[0] or "Unknown"
        count = row[1]
        countries.append({"country": country, "players_count": count})
    return {"countries": countries}

@app.get("/player/{player_id}/transfers")
def get_player_transfers(player_id: int):
    """
    Récupère l'historique des transferts d'un joueur.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM transfers 
        WHERE player_id = ? 
        ORDER BY transfer_date DESC, created_at DESC
    """, (player_id,))
    rows = cur.fetchall()
    conn.close()
    transfers = [dict(row) for row in rows]
    return {"transfers": transfers}

@app.get("/player/{player_id}/market-value-history")
def get_market_value_history(player_id: int):
    """
    Récupère l'historique des valeurs de marché d'un joueur.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM market_value_history 
        WHERE player_id = ? 
        ORDER BY date_recorded DESC, created_at DESC
    """, (player_id,))
    rows = cur.fetchall()
    conn.close()
    history = [dict(row) for row in rows]
    return {"history": history}

@app.get("/analytics/player-stats")
def get_player_analytics(
    min_goals: int = None,
    min_assists: int = None,
    position: str = None,
    country: str = None
):
    """
    Endpoint d'analyse pour filtrer et analyser les joueurs selon différents critères.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM players WHERE 1=1"
    params = []
    
    if min_goals:
        query += " AND goals >= ?"
        params.append(min_goals)
    if min_assists:
        query += " AND assists >= ?"
        params.append(min_assists)
    if position:
        query += " AND position LIKE ?"
        params.append(f"%{position}%")
    if country:
        query += " AND nationality = ?"
        params.append(country)
    
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()
    
    players = [dict(row) for row in rows]
    
    # Calculs d'analytics
    total_players = len(players)
    avg_goals = sum(p.get('goals', 0) or 0 for p in players) / total_players if total_players > 0 else 0
    avg_assists = sum(p.get('assists', 0) or 0 for p in players) / total_players if total_players > 0 else 0
    
    return {
        "total_players": total_players,
        "average_goals": round(avg_goals, 2),
        "average_assists": round(avg_assists, 2),
        "players": players
    }

@app.get("/player-by-name/{player_name}")
def get_player_by_name(player_name: str):
    """
    Récupère un joueur par son nom (recherche exacte ou partielle).
    Normalise les données et génère un rapport si nécessaire.
    """
    player = db_get_player_by_name(player_name)
    if player:
        # Normalise le nom du pays pour le globe
        if player.get('nationality'):
            normalized_nationality = normalize_country_name_with_openai(player['nationality'])
            player['nationality'] = normalized_nationality or player['nationality']
        
        # Génère un rapport de scouting si pas déjà présent
        if 'scouting_report' not in player or not player.get('scouting_report'):
            scouting_report = generate_scouting_report_with_openai(player)
            if scouting_report:
                player['scouting_report'] = scouting_report
                # Sauvegarde le rapport dans la base de données
                update_player_field(player.get('name'), 'scouting_report', scouting_report)
        
        # S'assure que toutes les valeurs numériques sont correctes
        if 'goals' not in player or player['goals'] is None:
            player['goals'] = 0
        if 'assists' not in player or player['assists'] is None:
            player['assists'] = 0
        if 'appearances' not in player or player['appearances'] is None:
            player['appearances'] = 0
        
        # S'assure que l'image_url est présent (même si vide)
        if 'image_url' not in player:
            player['image_url'] = None
        
        return {"player": player}
    else:
        raise HTTPException(status_code=404, detail=f"Player '{player_name}' not found")
