# Filename: scraping/scraper.py
# Description: Script de scraping amélioré pour collecter les données des joueurs à la demande avec enrichissement OpenAI.

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
import os
import sys

# Configuration de la base de données SQLite
# Utilise maintenant le module centralisé depuis backend
DB_PATH = os.path.join(os.path.dirname(__file__), "players.db")

# Import du module de base de données centralisé
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
try:
    from database import init_db, save_player_to_db as db_save_player_to_db, get_db_connection
    USE_CENTRALIZED_DB = True
except ImportError:
    USE_CENTRALIZED_DB = False
    print("-> Attention: Module database.py non trouvé, utilisation de la DB locale")

def init_db_local():
    """Fonction locale de fallback si le module centralisé n'est pas disponible."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Table principale des joueurs avec colonnes étendues
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        age INTEGER,
        nationality TEXT,
        current_club TEXT,
        position TEXT,
        market_value TEXT,
        height TEXT,
        weight TEXT,
        goals INTEGER,
        assists INTEGER,
        appearances INTEGER,
        yellow_cards INTEGER,
        red_cards INTEGER,
        minutes_played INTEGER,
        goals_per_match REAL,
        assists_per_match REAL,
        contract_expires TEXT,
        source_wikipedia TEXT,
        source_transfermarkt TEXT,
        scouting_report TEXT,
        image_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Table pour l'historique des transferts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        player_name TEXT,
        from_club TEXT,
        to_club TEXT,
        transfer_date TEXT,
        transfer_fee TEXT,
        transfer_type TEXT,
        season TEXT,
        FOREIGN KEY (player_id) REFERENCES players(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Table pour l'historique des valeurs de marché
    cur.execute("""
    CREATE TABLE IF NOT EXISTS market_value_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        player_name TEXT,
        market_value TEXT,
        date_recorded TEXT,
        FOREIGN KEY (player_id) REFERENCES players(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Ajoute les colonnes si elles n'existent pas (migration)
    columns_to_add = [
        'scouting_report', 'image_url', 'weight', 'yellow_cards', 
        'red_cards', 'minutes_played', 'goals_per_match', 'assists_per_match',
        'contract_expires', 'created_at', 'updated_at'
    ]
    for col in columns_to_add:
        try:
            if col in ['goals_per_match', 'assists_per_match']:
                cur.execute(f"ALTER TABLE players ADD COLUMN {col} REAL")
            elif col in ['yellow_cards', 'red_cards', 'minutes_played']:
                cur.execute(f"ALTER TABLE players ADD COLUMN {col} INTEGER")
            elif col in ['created_at', 'updated_at']:
                cur.execute(f"ALTER TABLE players ADD COLUMN {col} TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            else:
                cur.execute(f"ALTER TABLE players ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass  # La colonne existe déjà
    
    conn.commit()
    conn.close()

# En-tête User-Agent pour imiter un navigateur
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

# Configuration OpenAI pour la normalisation des noms
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
    print("⚠️  ATTENTION: OPENAI_API_KEY n'est pas configurée dans scraper.py!")
    print("   Configurez-la via une variable d'environnement ou un fichier .env")

def normalize_player_name_with_openai(player_name):
    """
    Utilise OpenAI pour corriger et normaliser un nom de joueur mal écrit ou avec des accents.
    Retourne le nom correct du joueur pour faciliter la recherche.
    """
    if not player_name or len(player_name.strip()) < 2:
        return player_name
    
    # Si le nom semble déjà correct (contient des lettres normales), on peut le garder tel quel
    # Mais on va quand même demander à OpenAI de le normaliser pour être sûr
    
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Tu es un expert en football. Corrige et normalise ce nom de joueur de football (peut être mal écrit, avec des accents manquants ou incorrects, ou des fautes d'orthographe).

Nom fourni: "{player_name}"

IMPORTANT: 
- Si c'est un surnom ou nom court connu (comme "Pedri", "Neymar", "Cristiano"), GARDE le surnom/nom court tel quel
- Si c'est un nom complet mal écrit, corrige-le avec les accents et l'orthographe correcte
- Utilise l'orthographe exacte et officielle du joueur tel qu'il apparaît sur Transfermarkt
- Garde les accents et caractères spéciaux si nécessaire
- Si le nom est ambigu (plusieurs joueurs possibles), retourne le nom le plus probable pour un joueur actuel et connu
- Réponds UNIQUEMENT avec le nom (surnom si c'est un surnom, nom complet si c'est un nom complet), sans explication, sans guillemets, sans ponctuation supplémentaire

Exemples:
- "Kylian Mbappe" -> "Kylian Mbappé" (corrige l'accent)
- "Lamine Yamal" -> "Lamine Yamal" (déjà correct)
- "Pedri" -> "Pedri" (garde le surnom)
- "Jude Bellingam" -> "Jude Bellingham" (corrige l'orthographe)
- "Erling Haaland" -> "Erling Haaland" (déjà correct)
- "Vinicius Junior" -> "Vinícius Júnior" (ajoute les accents)

Nom normalisé:"""
        
        openai_body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "Tu es un expert en football avec une connaissance approfondie des noms de joueurs actuels et historiques."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 50
        }
        
        resp = requests.post(OPENAI_API_URL, json=openai_body, headers=headers, timeout=8)
        resp.raise_for_status()
        response_data = resp.json()
        normalized_name = response_data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
        
        # Nettoie la réponse (enlève guillemets, points, etc.)
        normalized_name = normalized_name.strip('"\'.,;!?()[]{}')
        normalized_name = normalized_name.strip()
        
        # Si OpenAI a retourné quelque chose de valide et différent, on l'utilise
        if normalized_name and len(normalized_name) > 1 and normalized_name.lower() != player_name.lower():
            print(f"-> Nom normalisé par OpenAI: '{player_name}' -> '{normalized_name}'")
            return normalized_name
        elif normalized_name and len(normalized_name) > 1:
            # Même si similaire, on garde la version normalisée d'OpenAI
            return normalized_name
        else:
            # Si OpenAI n'a pas retourné de résultat valide, on garde le nom original
            return player_name
            
    except requests.exceptions.Timeout:
        print(f"-> Timeout OpenAI pour la normalisation de '{player_name}', utilisation du nom original")
        return player_name
    except Exception as e:
        print(f"-> Erreur lors de la normalisation OpenAI de '{player_name}': {e}")
        return player_name

def get_player_page_url(player_name, site):
    """Trouve l'URL de la page du joueur sur Transfermarkt avec recherche améliorée."""
    if site == "transfermarkt":
        try:
            # Normalise le nom avec OpenAI pour corriger les erreurs d'orthographe et accents
            normalized_name = normalize_player_name_with_openai(player_name)
            # Nettoie le nom pour la recherche
            clean_name = normalized_name.strip()
            search_url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={clean_name.replace(' ', '+')}"
            resp = requests.get(search_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Méthode 1: Cherche dans la section Players
            player_header = soup.find('div', class_='table-header', string=re.compile(r'\s*Players\s*', re.IGNORECASE))
            if not player_header:
                # Essaie avec différentes variantes
                player_header = soup.find('div', class_='table-header', string=re.compile(r'Spieler|Joueurs', re.IGNORECASE))
            
            if player_header:
                parent_box = player_header.find_parent('div', class_='box')
                if parent_box:
                    result_link = parent_box.select_one('td.hauptlink a.spielprofil_tooltip')
                    if result_link and result_link.get('href'):
                        href = result_link['href']
                        if not href.startswith('http'):
                            href = "https://www.transfermarkt.com" + href
                        return href
            
            # Méthode 2: Cherche tous les liens de profil de joueur
            all_player_links = soup.select('a.spielprofil_tooltip')
            if all_player_links:
                # Prend le premier résultat qui semble correspondre
                for link in all_player_links[:5]:  # Limite aux 5 premiers résultats
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)
                    # Vérifie si le nom correspond approximativement
                    if href and ('spieler' in href.lower() or 'player' in href.lower()):
                        if not href.startswith('http'):
                            href = "https://www.transfermarkt.com" + href
                        return href
            
            # Méthode 3: Fallback - cherche n'importe quel lien de profil
            first_result = soup.select_one('a[href*="/spieler/"]')
            if first_result and first_result.get('href'):
                href = first_result['href']
                if not href.startswith('http'):
                    href = "https://www.transfermarkt.com" + href
                return href

        except requests.exceptions.Timeout:
            print(f"Timeout lors de la recherche pour {player_name}")
        except requests.exceptions.RequestException as e:
            print(f"Erreur de recherche URL pour {player_name} sur {site}: {e}")
    return None

def scrape_transfermarkt(url):
    """Scrape les données depuis une page de profil Transfermarkt avec amélioration des statistiques."""
    data = {}
    try:
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Nom, Club, Valeur
        name_elem = soup.select_one('h1.data-header__headline')
        if name_elem:
            data['name'] = name_elem.get_text(strip=True).split('#')[0].strip()
        
        market_value_elem = soup.select_one('.data-header__market-value-wrapper')
        if market_value_elem:
            market_value_text = market_value_elem.get_text(strip=True)
            # Extrait la valeur (ex: "€80.00m" ou "80.00m")
            value_match = re.search(r'([€$]?[\d.,]+[mk]?)', market_value_text)
            if value_match:
                data['market_value'] = value_match.group(1)
            else:
                data['market_value'] = market_value_text.split(' ')[0] if market_value_text else 'N/A'
        
        club_link = soup.select_one('.data-header__club-info a')
        data['current_club'] = club_link.get_text(strip=True) if club_link else 'N/A'

        # Infos détaillées
        for info_box in soup.select('.info-table__row'):
            label_elem = info_box.select_one('.info-table__label')
            content_elem = info_box.select_one('.info-table__content')
            if not label_elem or not content_elem:
                continue
                
            label = label_elem.get_text(strip=True)
            content = content_elem.get_text(strip=True)
            
            if "Date of birth/Age" in label or "Geburtsdatum/Alter" in label or "Date de naissance" in label:
                if '(' in content:
                    age_match = re.search(r'\((\d+)\)', content)
                    if age_match:
                        try:
                            data['age'] = int(age_match.group(1))
                        except ValueError:
                            pass
            # Recherche de la nationalité avec plusieurs variantes
            if ("Nationality" in label or "Nationalität" in label or "Nationalité" in label or 
                "Citizenship" in label or "Staatsangehörigkeit" in label):
                # Nettoie la nationalité (peut contenir des emojis de drapeaux, plusieurs lignes, etc.)
                nationality = content.strip()
                
                # Enlève les emojis de drapeaux (Unicode flags)
                nationality = re.sub(r'[\U0001F1E6-\U0001F1FF]', '', nationality)  # Enlève les emojis de drapeaux
                # Enlève les emojis de drapeaux individuels
                nationality = re.sub(r'[\U0001F300-\U0001F9FF]', '', nationality)  # Enlève tous les emojis
                
                # Prend la première nationalité si plusieurs (séparées par \n, , ou |)
                if '\n' in nationality:
                    nationality = nationality.split('\n')[0].strip()
                if ',' in nationality:
                    nationality = nationality.split(',')[0].strip()
                if '|' in nationality:
                    nationality = nationality.split('|')[0].strip()
                
                # Nettoie les espaces multiples mais garde les caractères spéciaux comme les accents
                nationality = ' '.join(nationality.split())
                
                # Enlève les caractères non-alphanumériques en début/fin mais garde les accents
                nationality = nationality.strip('.,;:!?()[]{}')
                
                if nationality and len(nationality) > 1:
                    data['nationality'] = nationality
                    print(f"-> Nationalité trouvée: {nationality}")
            
            # Poste (Transfermarkt) - robuste
            if any(k in label.lower() for k in ["position", "poste"]):
                pos = content.strip()
                # Nettoyage : enlève les espaces multiples
                pos = re.sub(r"\s+", " ", pos)
                data["position_tm"] = pos
                # Compatibilité avec le frontend actuel
                data["position"] = pos
            if "Height" in label or "Größe" in label or "Taille" in label:
                data['height'] = content.replace(',', '.').strip()
        
        # Méthode alternative: cherche la nationalité dans d'autres sections si pas trouvée
        if 'nationality' not in data:
            # Cherche dans les spans avec des classes de drapeaux ou de nationalité
            nationality_spans = soup.select('span[title*="nationality"], span[title*="Nationalität"], .flaggenrahmen')
            for span in nationality_spans:
                title = span.get('title', '')
                if title and ('nationality' in title.lower() or 'nationalität' in title.lower()):
                    # Essaie d'extraire le nom du pays du title
                    country_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', title)
                    if country_match:
                        data['nationality'] = country_match.group(1)
                        print(f"-> Nationalité trouvée via title: {data['nationality']}")
                        break
        
        # ⚠️ STATISTIQUES : Ne plus scraper depuis Transfermarkt (non fiable)
        # Les stats sont maintenant récupérées depuis FBref via scrape_fbref_stats()
        # Transfermarkt est utilisé uniquement pour le profil (nom, âge, club, valeur, etc.)
        
        # Valeurs par défaut pour les stats (seront remplacées par FBref si disponible)
        data['appearances'] = 0
        data['goals'] = 0
        data['assists'] = 0
        data['minutes_played'] = 0
        
        print(f"-> Profil Transfermarkt extrait (stats à récupérer via FBref)")

    except (requests.exceptions.RequestException, AttributeError, IndexError, TypeError) as e:
        print(f"Erreur scraping Transfermarkt ({url}): {e}")
    return data

def scrape_fbref_stats(player_name, season="2024-2025"):
    """
    Récupère les stats standard FBref pour un joueur donné.
    Utilise l'API publique FBref via scraping direct.
    
    Args:
        player_name: Nom du joueur à rechercher
        season: Saison à rechercher (format "2024-2025")
    
    Returns:
        dict: Dictionnaire avec les stats (goals, assists, appearances, minutes_played)
    """
    import unicodedata
    import difflib
    
    # Normalisation des noms (enlève accents, caractères spéciaux)
    def normalize_name(name):
        """Normalise un nom pour la comparaison"""
        # Enlève les accents
        name = unicodedata.normalize('NFD', name.lower())
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        # Enlève caractères spéciaux
        name = re.sub(r'[^\w\s]', '', name)
        return name.strip()
    
    try:
        # Liste des ligues majeures à chercher
        leagues = {
            'Premier League': '9',
            'La Liga': '12',
            'Bundesliga': '20',
            'Serie A': '11',
            'Ligue 1': '13',
        }
        
        target_normalized = normalize_name(player_name)
        best_match = None
        best_stats = {}
        
        # Cherche dans chaque ligue
        for league_name, league_id in leagues.items():
            try:
                # URL de recherche FBref pour la ligue
                search_url = f"https://fbref.com/en/comps/{league_id}/{season}/stats/{season}-{league_name}-Stats"
                
                resp = requests.get(search_url, headers=HEADERS, timeout=10)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # Cherche le tableau de stats des joueurs
                stats_table = soup.select_one('table#stats_standard')
                if not stats_table:
                    continue
                
                # Parcourt les lignes du tableau
                rows = stats_table.select('tbody tr')
                for row in rows:
                    # Ignore les lignes d'en-tête
                    if 'thead' in str(row.get('class', [])):
                        continue
                    
                    # Récupère le nom du joueur
                    player_cell = row.select_one('th[data-stat="player"] a, td[data-stat="player"] a')
                    if not player_cell:
                        continue
                    
                    player_name_found = player_cell.get_text(strip=True)
                    player_name_normalized = normalize_name(player_name_found)
                    
                    # Compare avec le nom recherché
                    similarity = difflib.SequenceMatcher(None, target_normalized, player_name_normalized).ratio()
                    
                    if similarity >= 0.85:  # Seuil de similarité
                        # Récupère les stats
                        try:
                            goals_cell = row.select_one('td[data-stat="goals"]')
                            assists_cell = row.select_one('td[data-stat="assists"]')
                            minutes_cell = row.select_one('td[data-stat="minutes"]')
                            games_cell = row.select_one('td[data-stat="games"]')
                            
                            # Récupère la position FBref
                            pos_cell = row.select_one('td[data-stat="position"], td[data-stat="pos"]')
                            position_fbref = None
                            if pos_cell:
                                position_fbref = pos_cell.get_text(strip=True)
                            
                            goals = int(goals_cell.get_text(strip=True) or 0) if goals_cell else 0
                            assists = int(assists_cell.get_text(strip=True) or 0) if assists_cell else 0
                            minutes = int(minutes_cell.get_text(strip=True).replace(',', '') or 0) if minutes_cell else 0
                            games = int(games_cell.get_text(strip=True) or 0) if games_cell else 0
                            
                            # Calcule appearances (matchs joués, pas seulement matchs dans le 11)
                            appearances = games  # FBref "games" = matchs joués
                            
                            stats = {
                                'goals': goals,
                                'assists': assists,
                                'appearances': appearances,
                                'minutes_played': minutes
                            }
                            
                            # Ajoute la position FBref si disponible
                            if position_fbref and position_fbref.lower() != 'nan' and position_fbref.strip():
                                stats['position_fbref'] = position_fbref.strip()
                            
                            # Garde le meilleur match (plus de minutes = plus actif)
                            if minutes > best_stats.get('minutes_played', 0):
                                best_match = player_name_found
                                best_stats = stats
                                
                        except (ValueError, AttributeError) as e:
                            continue
                
            except requests.exceptions.RequestException:
                continue
            except Exception as e:
                print(f"-> Erreur lors de la recherche FBref dans {league_name}: {e}")
                continue
        
        if best_stats:
            print(f"-> Stats FBref trouvées pour {best_match}: {best_stats.get('goals')} buts, {best_stats.get('assists')} passes, {best_stats.get('appearances')} matchs")
            return best_stats
        else:
            print(f"-> Aucune stat FBref trouvée pour {player_name}")
            return {}
            
    except Exception as e:
        print(f"-> Erreur générale lors du scraping FBref: {e}")
        return {}

def scrape_wikipedia_image(player_name):
    """Scrape l'image du joueur depuis Wikipedia avec plusieurs tentatives."""
    if not player_name:
        return None
    
    # Nettoyage du nom pour Wikipedia
    clean_name = player_name.strip()
    
    # Tentatives avec différentes variantes du nom
    name_variants = [
        clean_name,
        clean_name.replace(' ', '_'),
        clean_name.replace('é', 'e').replace('è', 'e').replace('ê', 'e'),
        clean_name.split()[0] if ' ' in clean_name else clean_name,  # Prénom seulement
    ]
    
    for variant in name_variants:
        try:
            api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{variant.replace(' ', '_')}"
            resp = requests.get(api_url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                json_data = resp.json()
                if json_data.get('thumbnail'):
                    image_url = json_data['thumbnail']['source']
                    # Agrandit l'image si possible (change 200px en 400px ou plus)
                    if '200px' in image_url:
                        image_url = image_url.replace('200px', '400px')
                    print(f"-> Image trouvée pour {player_name}: {image_url}")
                    return image_url
        except requests.exceptions.RequestException:
            continue
        except Exception as e:
            print(f"-> Erreur lors de la recherche d'image pour {variant}: {e}")
            continue
    
    # Si Wikipedia échoue, essaie avec l'image de Transfermarkt
    try:
        # Note: Transfermarkt protège ses images, mais on peut essayer
        print(f"-> Aucune image trouvée sur Wikipedia pour {player_name}")
    except:
        pass
    
    return None

def save_player_to_db(player_data):
    """Insère ou met à jour les données d'un joueur avec gestion d'erreurs améliorée."""
    
    # Utilise le module centralisé si disponible
    if USE_CENTRALIZED_DB:
        return db_save_player_to_db(player_data)

    # Fallback local
    if not player_data or not player_data.get('name'):
        print("-> Données invalides pour la sauvegarde")
        return None

    try:
        # Initialise la DB locale
        init_db_local()

        # S'assure que le répertoire existe
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cur = conn.cursor()

        # Vérifie les colonnes existantes
        cur.execute("PRAGMA table_info(players)")
        table_columns = {row[1] for row in cur.fetchall()}

        # Filtrage des données valides
        valid_data = {k: v for k, v in player_data.items() if k in table_columns and v is not None}

        if not valid_data:
            print("-> Aucune donnée valide à sauvegarder")
            conn.close()
            return None

        columns = list(valid_data.keys())
        placeholders = ', '.join('?' * len(columns))
        columns_str = ', '.join(columns)

        sql = f"INSERT OR REPLACE INTO players ({columns_str}) VALUES ({placeholders})"
        
        values = [valid_data[col] if valid_data[col] is not None else '' for col in columns]

        cur.execute(sql, values)
        conn.commit()

        # Récupération
        player_name = valid_data.get('name')
        cur.execute("SELECT * FROM players WHERE name = ?", (player_name,))
        row = cur.fetchone()

        conn.close()

        if row:
            return dict(zip([d[0] for d in cur.description], row))

        return None

    except Exception as e:
        print(f"Erreur DB lors de la sauvegarde: {e}")
        import traceback
        print(traceback.format_exc())
        if 'conn' in locals():
            conn.close()
        return None


def scrape_and_save_player_data(player_name):
    print(f"--- Lancement du scraping pour : {player_name} ---")

    try:
        # Normalise d'abord le nom avec OpenAI pour améliorer les chances de trouver le joueur
        normalized_name = normalize_player_name_with_openai(player_name)
        print(f"-> Nom normalisé: '{player_name}' -> '{normalized_name}'")
        
        tm_url = get_player_page_url(normalized_name, "transfermarkt")
        if not tm_url:
            print("-> Impossible de trouver le joueur sur Transfermarkt.")
            return None

        all_data = {'name': normalized_name, 'source_transfermarkt': tm_url}

        # Scrap Transfermarkt (profil uniquement - pas de stats)
        try:
            tm_data = scrape_transfermarkt(tm_url)
            if tm_data:
                all_data.update(tm_data)
        except Exception as e:
            print(f"-> Erreur scraping Transfermarkt: {e}")

        precise_name = all_data.get('name', player_name)
        
        # Scrap FBref pour les stats (source fiable)
        try:
            fbref_stats = scrape_fbref_stats(precise_name)
            if fbref_stats:
                all_data.update(fbref_stats)
                print(f"-> Stats FBref intégrées pour {precise_name}")
        except Exception as e:
            print(f"-> Erreur scraping FBref: {e}")
        
        # Fusion des positions : priorité à Transfermarkt (plus précis)
        if all_data.get("position_tm"):
            all_data["position"] = all_data["position_tm"]
        elif all_data.get("position_fbref"):
            all_data["position"] = all_data["position_fbref"]
        
        # Log des positions trouvées
        if all_data.get("position_tm") or all_data.get("position_fbref"):
            positions_info = []
            if all_data.get("position_tm"):
                positions_info.append(f"TM: {all_data['position_tm']}")
            if all_data.get("position_fbref"):
                positions_info.append(f"FBref: {all_data['position_fbref']}")
            print(f"-> Positions trouvées: {', '.join(positions_info)}")

        # Image Wikipedia
        try:
            img = scrape_wikipedia_image(precise_name)
            if img:
                all_data["image_url"] = img
        except Exception as e:
            print(f"-> Erreur image: {e}")

        # Sauvegarde
        try:
            saved = save_player_to_db(all_data)
            if saved:
                print(f"-> Données sauvegardées pour {precise_name}")
                return saved
        except Exception as e:
            print(f"-> Erreur sauvegarde DB: {e}")

        return all_data

    except Exception as e:
        import traceback
        print("-> ERREUR CRITIQUE:", e)
        print(traceback.format_exc())
        return None


if __name__ == "__main__":
    # Test du script
    players_to_scrape = ["Jude Bellingham", "Lamine Yamal", "Fredy Guarín"]
    for name in players_to_scrape:
        scrape_and_save_player_data(name)
        time.sleep(2)
    print("\n--- Scraping de test terminé. ---")
