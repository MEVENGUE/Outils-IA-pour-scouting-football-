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
# Le DB_PATH local n'est utilisé que si le module centralisé n'est pas disponible
# En production, le module centralisé gère le chemin correct (/app/data)
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
    # S'assure que le répertoire existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
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

        # Infos détaillées - Version robuste avec fallback
        def norm(s: str) -> str:
            return re.sub(r"\s+", " ", s.strip().lower())

        # ---- 1) Lecture via info-table (méthode principale) ----
        for row in soup.select(".info-table__row"):
            label_el = row.select_one(".info-table__label")
            val_el = row.select_one(".info-table__content")
            if not label_el or not val_el:
                continue

            label = norm(label_el.get_text(" ", strip=True))
            val = val_el.get_text(" ", strip=True).strip()

            # AGE
            if any(k in label for k in ["date of birth", "age", "geburtsdatum", "alter", "date de naissance"]):
                m = re.search(r"\((\d{1,2})\)", val)
                if m:
                    data["age"] = int(m.group(1))

            # NATIONALITY
            if any(k in label for k in ["nationality", "citizenship", "nationalität", "nationalité", "staatsangehörigkeit"]):
                nationality = val
                nationality = re.sub(r"[\U0001F1E6-\U0001F1FF]", "", nationality)
                nationality = re.sub(r"[\U0001F300-\U0001F9FF]", "", nationality)
                nationality = nationality.split("\n")[0].split(",")[0].split("|")[0].strip()
                nationality = " ".join(nationality.split()).strip('.,;:!?()[]{}')
                if nationality:
                    data["nationality"] = nationality

            # POSITION
            if any(k in label for k in ["position", "poste"]):
                # Transfermarkt peut renvoyer "Left Winger" etc.
                pos = val.strip()
                pos = re.sub(r"\s+", " ", pos)
                data["position_tm"] = pos
                # Compatibilité avec le frontend actuel
                data["position"] = pos

            # HEIGHT
            if any(k in label for k in ["height", "größe", "taille"]):
                data["height"] = val.replace(",", ".").strip()

        # ---- 2) Fallback: lecture via header items (si info-table absent) ----
        if "age" not in data or "position" not in data or "height" not in data:
            header_items = soup.select(".data-header__items li")
            for li in header_items:
                txt = li.get_text(" ", strip=True)
                t = norm(txt)

                # exemples possibles : "Age: 24", "Position: Right Winger", "Height: 1,71 m"
                if "age" in t and "age" not in data:
                    m = re.search(r"\b(\d{1,2})\b", txt)
                    if m:
                        data["age"] = int(m.group(1))

                if "position" in t and "position" not in data:
                    # prend ce qui suit ':'
                    parts = txt.split(":")
                    if len(parts) >= 2:
                        pos = parts[1].strip()
                        pos = re.sub(r"\s+", " ", pos)
                        data["position_tm"] = pos
                        data["position"] = pos

                if "height" in t and "height" not in data:
                    parts = txt.split(":")
                    if len(parts) >= 2:
                        data["height"] = parts[1].strip().replace(",", ".")
        
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

def _fbref_uncomment_tables(html: str) -> str:
    """FBref met parfois des tables dans des commentaires HTML <!-- ... -->"""
    return re.sub(r"<!--|-->", "", html)

def _normalize_name_basic(s: str) -> str:
    """Normalise un nom pour la comparaison (enlève accents, caractères spéciaux)"""
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def fbref_search_player_urls(player_name: str, limit: int = 8) -> list:
    """
    Retourne une liste de candidats FBref (nom + url) via la recherche globale FBref.
    """
    try:
        q = requests.utils.quote(player_name)
        url = f"https://fbref.com/en/search/search.fcgi?search={q}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code != 200:
            return []

        html = _fbref_uncomment_tables(resp.text)
        soup = BeautifulSoup(html, "html.parser")

        results = []
        # Sur FBref, les résultats pertinents sont souvent dans item "Players"
        for a in soup.select('div.search-item-name a[href^="/en/players/"]'):
            name = a.get_text(strip=True)
            href = a.get("href")
            if not href:
                continue
            results.append({
                "name": name,
                "url": "https://fbref.com" + href
            })
            if len(results) >= limit:
                break

        # fallback si structure HTML différente
        if not results:
            for a in soup.select('a[href^="/en/players/"]'):
                name = a.get_text(strip=True)
                href = a.get("href")
                if name and href:
                    results.append({"name": name, "url": "https://fbref.com" + href})
                if len(results) >= limit:
                    break

        return results
    except Exception as e:
        print(f"-> Erreur recherche FBref pour {player_name}: {e}")
        return []

def scrape_fbref_stats(player_name: str, season: str = "2024-2025", tm_club: str = None) -> dict:
    """
    Version robuste qui recherche le joueur via la recherche globale FBref.
    1) Recherche le joueur sur FBref
    2) Ouvre la page joueur
    3) Prend les stats "Standard" de la saison demandée, sinon la ligne la plus récente (max minutes)
    
    Args:
        player_name: Nom du joueur à rechercher
        season: Saison à rechercher (format "2024-2025")
        tm_club: Club du joueur depuis Transfermarkt (pour mieux matcher en cas d'ambiguïté)
    
    Returns:
        dict: Dictionnaire avec les stats (goals, assists, appearances, minutes_played, position_fbref)
    """
    target = _normalize_name_basic(player_name)
    candidates = fbref_search_player_urls(player_name)

    if not candidates:
        print(f"-> FBref: aucun résultat de recherche pour {player_name}")
        return {}

    # Scoring simple (nom proche + bonus si club TM trouvé dans la page)
    def score_candidate(c):
        cand_norm = _normalize_name_basic(c["name"])
        base = 1.0 if cand_norm == target else 0.0
        # similarité grossière
        import difflib
        base = max(base, difflib.SequenceMatcher(None, target, cand_norm).ratio())
        return base

    candidates = sorted(candidates, key=score_candidate, reverse=True)[:5]

    best = {}
    best_minutes = -1

    for c in candidates:
        try:
            r = requests.get(c["url"], headers=HEADERS, timeout=12)
            if r.status_code != 200:
                continue
            html = _fbref_uncomment_tables(r.text)
            soup = BeautifulSoup(html, "html.parser")

            # Bonus: si tm_club fourni, on essaie de vérifier que le club apparaît quelque part
            club_bonus = 0.0
            if tm_club:
                page_text = soup.get_text(" ", strip=True).lower()
                if tm_club.lower() in page_text:
                    club_bonus = 0.15

            # Table standard par saison/compétition (id fréquent sur pages joueurs)
            table = soup.select_one("table#stats_standard_dom_lg") or soup.select_one("table#stats_standard")
            if not table:
                continue

            rows = table.select("tbody tr")
            # On cherche la meilleure ligne:
            # - si saison == season, on la privilégie
            # - sinon on prend max minutes
            for row in rows:
                # ignore separators
                if "class" in row.attrs and "thead" in str(row.get("class", [])):
                    continue

                season_cell = row.select_one('th[data-stat="season"]')
                season_txt = season_cell.get_text(strip=True) if season_cell else ""

                mins_cell = row.select_one('td[data-stat="minutes"]')
                goals_cell = row.select_one('td[data-stat="goals"]')
                ast_cell = row.select_one('td[data-stat="assists"]')
                games_cell = row.select_one('td[data-stat="games"]')

                # position (souvent "position" ou "pos")
                pos_cell = row.select_one('td[data-stat="position"], td[data-stat="pos"]')

                def to_int(x):
                    if not x:
                        return 0
                    t = x.get_text(strip=True).replace(",", "")
                    return int(t) if t.isdigit() else 0

                minutes = to_int(mins_cell)
                goals = to_int(goals_cell)
                assists = to_int(ast_cell)
                games = to_int(games_cell)

                # Sélection
                is_target_season = (season_txt == season)
                candidate_minutes_key = minutes + int(1000 * club_bonus)  # bonus si club match

                if is_target_season and candidate_minutes_key > best_minutes:
                    best_minutes = candidate_minutes_key
                    best = {
                        "goals": goals,
                        "assists": assists,
                        "appearances": games,
                        "minutes_played": minutes,
                    }
                    if pos_cell:
                        pos = pos_cell.get_text(strip=True)
                        if pos and pos.lower() != 'nan':
                            best["position_fbref"] = pos.strip()

                # fallback: si on ne trouve pas la saison, max minutes
                if not is_target_season and candidate_minutes_key > best_minutes and not best:
                    best_minutes = candidate_minutes_key
                    best = {
                        "goals": goals,
                        "assists": assists,
                        "appearances": games,
                        "minutes_played": minutes,
                    }
                    if pos_cell:
                        pos = pos_cell.get_text(strip=True)
                        if pos and pos.lower() != 'nan':
                            best["position_fbref"] = pos.strip()

            if best:
                print(f"-> FBref OK ({c['name']}): {best.get('goals',0)}G {best.get('assists',0)}A {best.get('appearances',0)}MJ")
                return best

        except Exception as e:
            print(f"-> Erreur lors du scraping FBref pour {c.get('name', 'unknown')}: {e}")
            continue

    print(f"-> Aucune stat FBref trouvée pour {player_name}")
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
        # Passe le club TM pour mieux matcher en cas d'ambiguïté (ex: "Danilo")
        try:
            fbref_stats = scrape_fbref_stats(
                precise_name,
                season="2024-2025",
                tm_club=all_data.get("current_club")
            )
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
