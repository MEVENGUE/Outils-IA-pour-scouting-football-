# Filename: scraping/scraper.py
# Description: Script de scraping amélioré pour collecter les données des joueurs à la demande avec enrichissement OpenAI.

import requests
from bs4 import BeautifulSoup
import sqlite3
import re
import time
import os
import sys
import json
import difflib
import unicodedata
from datetime import date, datetime
from urllib.parse import quote
from dotenv import load_dotenv

# Configuration de la base de données SQLite
# Utilise maintenant le module centralisé depuis backend
# Le DB_PATH local n'est utilisé que si le module centralisé n'est pas disponible
# En production, le module centralisé gère le chemin correct (/app/data)
DB_PATH = os.path.join(os.path.dirname(__file__), "players.db")

# Import du module de base de données centralisé
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
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
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

RESERVE_TEAM_PATTERN = re.compile(
    r"\b(II|III|IV|B|U\d{2}|Youth|Reserve|Academy|Amateurs|Juniors)\b",
    re.IGNORECASE,
)

def _load_env_files() -> None:
    backend_dir = os.path.join(os.path.dirname(__file__), '..')
    repo_root = os.path.join(backend_dir, '..')
    for env_path in (
        os.path.join(backend_dir, '.env'),
        os.path.join(repo_root, '.env'),
    ):
        if os.path.isfile(env_path):
            load_dotenv(env_path, override=False)

_load_env_files()

# Récupère la clé API depuis la variable d'environnement
# Si la variable n'existe pas, utilise une valeur par défaut vide (à configurer)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Vérification que la clé API est configurée
if not OPENAI_API_KEY:
    print("⚠️  ATTENTION: OPENAI_API_KEY n'est pas configurée dans scraper.py!")
    print("   Configurez-la via une variable d'environnement ou un fichier .env")

def openai_available() -> bool:
    return bool(OPENAI_API_KEY and OPENAI_API_KEY.strip())

def _normalize_name_for_match(name: str) -> str:
    if not name:
        return ""
    normalized = unicodedata.normalize("NFD", name.lower())
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()

def _name_similarity(left: str, right: str) -> float:
    left_norm = _normalize_name_for_match(left)
    right_norm = _normalize_name_for_match(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm == right_norm:
        return 1.0
    return difflib.SequenceMatcher(None, left_norm, right_norm).ratio()

def _is_reserve_team(label: str) -> bool:
    if not label:
        return False
    return bool(RESERVE_TEAM_PATTERN.search(label))

def _absolute_href(href: str, base: str = "https://www.transfermarkt.com") -> str:
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return base + href

def _score_tm_candidate(link_text: str, href: str, query_name: str) -> float:
    if _is_reserve_team(link_text) or _is_reserve_team(href):
        return -1.0
    score = _name_similarity(link_text, query_name)
    if score >= 0.95:
        score += 0.05
    return score

def _pick_best_tm_link(links, query_name: str) -> str | None:
    candidates: list[tuple[float, str]] = []
    for link in links:
        href = link.get("href", "")
        link_text = link.get_text(strip=True)
        if not href:
            continue
        score = _score_tm_candidate(link_text, href, query_name)
        if score >= 0.55:
            candidates.append((score, _absolute_href(href)))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]

def normalize_player_name_with_openai(player_name):
    """
    Utilise OpenAI pour corriger et normaliser un nom de joueur mal écrit ou avec des accents.
    Retourne le nom correct du joueur pour faciliter la recherche.
    """
    if not player_name or len(player_name.strip()) < 2:
        return player_name

    if not openai_available():
        return player_name.strip()
    
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
            normalized_name = (
                normalize_player_name_with_openai(player_name)
                if openai_available()
                else player_name.strip()
            )
            clean_name = normalized_name.strip()
            search_url = (
                "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche"
                f"?query={clean_name.replace(' ', '+')}"
            )
            resp = requests.get(search_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            player_header = soup.find(
                'div',
                class_='table-header',
                string=re.compile(r'\s*Players\s*', re.IGNORECASE),
            )
            if not player_header:
                player_header = soup.find(
                    'div',
                    class_='table-header',
                    string=re.compile(r'Spieler|Joueurs', re.IGNORECASE),
                )

            if player_header:
                parent_box = player_header.find_parent('div', class_='box')
                if parent_box:
                    section_links = parent_box.select('td.hauptlink a.spielprofil_tooltip')
                    best_href = _pick_best_tm_link(section_links, clean_name)
                    if best_href:
                        return best_href

            all_player_links = soup.select('a.spielprofil_tooltip')
            best_href = _pick_best_tm_link(all_player_links[:10], clean_name)
            if best_href:
                return best_href

            fallback_links = soup.select('a[href*="/spieler/"]')
            best_href = _pick_best_tm_link(fallback_links[:10], clean_name)
            if best_href:
                return best_href

        except requests.exceptions.Timeout:
            print(f"Timeout lors de la recherche pour {player_name}")
        except requests.exceptions.RequestException as e:
            print(f"Erreur de recherche URL pour {player_name} sur {site}: {e}")
    return None

def _age_from_birthdate_str(birthdate_str: str):
    """
    birthdate_str: '1998-12-20' ou '20/12/1998' etc.
    ✅ Renommé pour éviter collision avec _age_from_birthdate(dob) pour Wikidata
    """
    if not birthdate_str:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            d = datetime.strptime(birthdate_str, fmt).date()
            today = date.today()
            return today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        except ValueError:
            continue
    return None

def _extract_jsonld_player(soup):
    """
    Transfermarkt met souvent un bloc <script type="application/ld+json"> contenant birthDate, height, name…
    """
    scripts = soup.select('script[type="application/ld+json"]')
    for sc in scripts:
        raw = sc.string or sc.get_text(strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        # Parfois c'est une liste
        items = data if isinstance(data, list) else [data]
        for it in items:
            if not isinstance(it, dict):
                continue
            t = (it.get("@type") or "").lower()
            if t in ("person", "sportsplayer"):
                return it
    return None

def _clean_text(s: str) -> str:
    if not s:
        return s
    s = re.sub(r"[\u200b\u200e\u200f]", "", s)  # zero-width
    s = " ".join(s.split())
    return s.strip()

def _parse_number(s: str):
    if not s:
        return None
    m = re.search(r"\b(\d+)\b", s.replace(".", "").replace(",", ""))
    return int(m.group(1)) if m else None

def scrape_transfermarkt(url: str):
    """Scrape les données depuis une page de profil Transfermarkt - Version robuste avec JSON-LD et fallbacks."""
    data = {}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # --- 1) JSON-LD (le plus stable) ---
        jsonld = _extract_jsonld_player(soup)
        if jsonld:
            name = _clean_text(jsonld.get("name", "")) or None
            if name:
                data["name"] = name

            birth = jsonld.get("birthDate")
            age = _age_from_birthdate_str(birth) if birth else None  # ✅ Fix: utilise _age_from_birthdate_str pour string
            if age is not None:
                data["age"] = age

            # height peut être "1.78 m" ou "1.78"
            height = jsonld.get("height")
            if isinstance(height, str) and height.strip():
                data["height"] = _clean_text(height)
            elif isinstance(height, (int, float)):
                data["height"] = f"{height} m"

        # --- 2) Header classique ---
        name_elem = soup.select_one("h1.data-header__headline")
        if name_elem and not data.get("name"):
            data["name"] = _clean_text(name_elem.get_text(strip=True).split("#")[0])

        mv_elem = soup.select_one(".data-header__market-value-wrapper")
        if mv_elem:
            mv_text = _clean_text(mv_elem.get_text(" ", strip=True))
            m = re.search(r"(€\s?[\d.,]+\s?[mk]?)", mv_text, re.IGNORECASE)
            data["market_value"] = _clean_text(m.group(1)) if m else mv_text

        club_link = soup.select_one(".data-header__club-info a")
        if club_link:
            data["current_club"] = _clean_text(club_link.get_text(strip=True))

        # --- 3) Info table (labels plus tolérants) ---
        for row in soup.select(".info-table__row"):
            lab = row.select_one(".info-table__label")
            val = row.select_one(".info-table__content")
            if not lab or not val:
                continue
            label = _clean_text(lab.get_text(" ", strip=True)).lower()
            content = _clean_text(val.get_text(" ", strip=True))

            # AGE (si JSON-LD absent)
            if ("date of birth" in label) or ("geburtsdatum" in label) or ("date de naissance" in label):
                # souvent: "Dec 20, 1998 (26)"
                if "age" in label or "(" in content:
                    m = re.search(r"\((\d+)\)", content)
                    if m:
                        data["age"] = int(m.group(1))

            # NATIONALITY
            if any(x in label for x in ["nationality", "nationalität", "nationalité", "citizenship", "staatsangehörigkeit"]):
                nat = content
                nat = re.sub(r"[\U0001F1E6-\U0001F1FF]", "", nat)  # flags
                nat = re.sub(r"[\U0001F300-\U0001F9FF]", "", nat)  # emojis
                nat = nat.split("\n")[0].split(",")[0].split("|")[0]
                nat = _clean_text(nat.strip(".,;:!?()[]{}"))
                if nat:
                    data["nationality"] = nat

            # POSITION
            if any(x in label for x in ["position", "poste"]):
                # Ex: "Centre-Forward" ou "Right-Back"
                if content:
                    pos = content.strip()
                    pos = re.sub(r"\s+", " ", pos)
                    data["position_tm"] = pos
                    data["position"] = pos

            # HEIGHT
            if any(x in label for x in ["height", "größe", "taille"]):
                if content:
                    data["height"] = content.replace(",", ".")
        
        # --- 4) Stats "header" (souvent présent) ---
        # Sur beaucoup de profils, TM affiche dans le header des stats du type Matches/Goals/Assists
        # Ça évite tes regex/tableaux instables.
        stats_container = soup.select_one(".data-header__stats-container")
        if stats_container:
            text = stats_container.get_text(" ", strip=True).lower()

            # matches / goals / assists
            # on cherche des nombres proches des mots clés
            m_app = re.search(r"(matches|spiele|matchs|appearances)\s*(\d+)", text)
            m_go  = re.search(r"(goals|tore|buts)\s*(\d+)", text)
            m_as  = re.search(r"(assists|vorlagen|passes)\s*(\d+)", text)

            if m_app and not data.get("appearances"):
                data["appearances"] = int(m_app.group(2))
            if m_go and not data.get("goals"):
                data["goals"] = int(m_go.group(2))
            if m_as and not data.get("assists"):
                data["assists"] = int(m_as.group(2))

        _parse_tm_performance_stats(soup, data)

        if data.get("appearances") or data.get("goals") or data.get("assists"):
            data["stats_source"] = "transfermarkt"

        print(
            f"-> Profil TM: {data.get('name')} | age={data.get('age')} | "
            f"club={data.get('current_club')} | pos={data.get('position')} | "
            f"apps={data.get('appearances')} g={data.get('goals')} a={data.get('assists')}"
        )

    except Exception as e:
        print(f"Erreur scraping Transfermarkt ({url}): {e}")

    return data

def _parse_tm_performance_stats(soup: BeautifulSoup, data: dict) -> None:
    """Extrait les stats depuis les tableaux de performance Transfermarkt."""
    stats_tables = soup.select(
        'table.items, table.data-table, .responsive-table, table[class*="items"]'
    )

    for table in stats_tables:
        headers: list[str] = []
        thead = table.select_one('thead')
        header_rows = thead.select('tr') if thead else table.select('tr.header, tr:first-child')

        for header_row in header_rows[:2]:
            header_cells = header_row.select('th, td')
            if not header_cells:
                continue
            headers = [cell.get_text(strip=True).lower() for cell in header_cells]
            if any(
                term in ' '.join(headers)
                for term in ['spiele', 'matches', 'appearances', 'matchs', 'goals', 'tore', 'assists', 'vorlagen']
            ):
                break

        tbody = table.select_one('tbody')
        data_rows = tbody.select('tr') if tbody else table.select('tr:not(.header)')

        for row in data_rows[:5]:
            cells = row.select('td')
            if len(cells) < 3:
                continue

            for index, cell in enumerate(cells):
                cell_text = cell.get_text(strip=True)
                clean_text = re.sub(r'[^\d.]', '', cell_text) if cell_text else ''
                if not clean_text or not clean_text.replace('.', '').isdigit():
                    continue

                try:
                    num = int(float(clean_text))
                except ValueError:
                    continue

                header = headers[index] if index < len(headers) else ''
                if any(term in header for term in ['spiele', 'matches', 'appearances', 'matchs', 'games']):
                    if not data.get('appearances'):
                        data['appearances'] = num
                elif any(term in header for term in ['tore', 'goals', 'buts']):
                    if not data.get('goals'):
                        data['goals'] = num
                elif any(term in header for term in ['vorlagen', 'assists', 'passes']):
                    if not data.get('assists'):
                        data['assists'] = num

def _extract_tm_player_id(tm_url: str | None) -> str | None:
    if not tm_url:
        return None
    match = re.search(r'/spieler/(\d+)', tm_url)
    return match.group(1) if match else None

def _http_get(url: str, *, referer: str | None = None, accept_json: bool = False):
    """HTTP GET with optional anti-bot fallbacks for protected sports sites."""
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
    if accept_json:
        headers["Accept"] = "application/json, text/plain, */*"

    if "fbref.com" in url:
        try:
            from curl_cffi import requests as curl_requests

            for impersonate in ("chrome120", "chrome110", "safari17_0", "edge101"):
                response = curl_requests.get(
                    url,
                    headers=headers,
                    impersonate=impersonate,
                    timeout=15,
                )
                if response.status_code == 200:
                    return response
        except ImportError:
            pass
        except Exception as exc:
            print(f"-> curl_cffi FBref fetch failed: {exc}")

        try:
            import cloudscraper

            scraper = cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "windows", "mobile": False},
            )
            response = scraper.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                return response
        except ImportError:
            pass
        except Exception as exc:
            print(f"-> cloudscraper FBref fetch failed: {exc}")

    response = requests.get(url, headers=headers, timeout=15)
    return response if response.status_code == 200 else None

def fetch_tm_ceapi_stats(player_id: str) -> dict | None:
    """Récupère les stats saison via l'API JSON Transfermarkt (ceapi)."""
    try:
        api_url = f"https://www.transfermarkt.com/ceapi/player/{player_id}/performance"
        response = _http_get(api_url, accept_json=True)
        if response is None:
            return None

        competitions = response.json()
        if not isinstance(competitions, list) or not competitions:
            return None

        totals = {
            "appearances": 0,
            "goals": 0,
            "assists": 0,
            "minutes_played": 0,
            "yellow_cards": 0,
            "red_cards": 0,
        }
        season_label = competitions[0].get("nameSeason")

        for competition in competitions:
            totals["appearances"] += int(competition.get("gamesPlayed") or 0)
            totals["goals"] += int(competition.get("goalsScored") or 0)
            totals["assists"] += int(competition.get("assists") or 0)
            totals["minutes_played"] += int(competition.get("minutesPlayed") or 0)
            totals["yellow_cards"] += int(competition.get("yellowCards") or 0)
            totals["red_cards"] += (
                int(competition.get("redCards") or 0)
                + int(competition.get("secondYellowCards") or 0)
            )

        if totals["appearances"] <= 0 and totals["goals"] <= 0 and totals["assists"] <= 0:
            return None

        if totals["appearances"] > 0:
            totals["goals_per_match"] = round(totals["goals"] / totals["appearances"], 3)
            totals["assists_per_match"] = round(totals["assists"] / totals["appearances"], 3)

        totals["stats_source"] = "transfermarkt_ceapi"
        totals["stats_season"] = season_label
        totals["stats_available"] = True
        return totals
    except Exception as exc:
        print(f"-> Erreur TM ceapi stats pour {player_id}: {exc}")
        return None

def fetch_player_statistics(
    player_name: str,
    tm_url: str | None = None,
    club_hint: str | None = None,
) -> dict | None:
    """Agrège les stats depuis la meilleure source disponible (TM ceapi puis FBref)."""
    player_id = _extract_tm_player_id(tm_url)
    if player_id:
        tm_stats = fetch_tm_ceapi_stats(player_id)
        if tm_stats:
            print(
                f"-> Stats TM ceapi: {tm_stats.get('goals')}G {tm_stats.get('assists')}A "
                f"{tm_stats.get('appearances')}MJ (saison {tm_stats.get('stats_season')})"
            )
            return tm_stats

    season = current_fb_season()
    fb_stats = fbref_stats_for_player(player_name, season=season, club_hint=club_hint)
    if fb_stats:
        fb_stats["stats_source"] = "fbref"
        fb_stats["stats_season"] = fb_stats.get("fbref_season") or season
        fb_stats["stats_available"] = True
        print(
            f"-> Stats FBref: {fb_stats.get('goals')}G {fb_stats.get('assists')}A "
            f"{fb_stats.get('appearances')}MJ (saison {fb_stats.get('stats_season')})"
        )
        return fb_stats

    return None

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

# ========== FBREF SCRAPING (Stats saison courante) ==========
FBREF_BASE = "https://fbref.com"
FBREF_SEARCH = "https://fbref.com/en/search/search.fcgi?search={q}"

def _fbref_uncomment(html: str) -> str:
    # FBref met énormément de tables dans <!-- ... -->
    return re.sub(r"<!--|-->", "", html)

def fbref_search_candidates(player_name: str, limit: int = 8) -> list[dict]:
    q = quote(player_name.strip())
    url = FBREF_SEARCH.format(q=q)
    response = _http_get(url, referer=FBREF_BASE)
    if response is None:
        print(f"-> FBref search blocked or unavailable for {player_name}")
        return []

    soup = BeautifulSoup(_fbref_uncomment(response.text), "html.parser")

    out = []
    for anchor in soup.select('div.search-item-name a[href^="/en/players/"]'):
        href = anchor.get("href")
        name = anchor.get_text(strip=True)
        if href and name:
            out.append({"name": name, "url": FBREF_BASE + href})
            if len(out) >= limit:
                break

    if not out:
        for anchor in soup.select('a[href^="/en/players/"]'):
            href = anchor.get("href")
            name = anchor.get_text(strip=True)
            if href and name:
                out.append({"name": name, "url": FBREF_BASE + href})
                if len(out) >= limit:
                    break

    return out

def fbref_scrape_standard(player_url: str, season: str | None = None, club_hint: str | None = None) -> dict | None:
    response = _http_get(player_url, referer=FBREF_BASE)
    if response is None:
        return None
    soup = BeautifulSoup(_fbref_uncomment(response.text), "html.parser")

    table = soup.select_one("table#stats_standard_dom_lg") or soup.select_one("table#stats_standard")
    if not table:
        return None

    rows = table.select("tbody tr")
    best = None
    best_score = -1

    for row in rows:
        # skip separators
        if "class" in row.attrs and "thead" in row.get("class", []):
            continue

        season_txt = row.select_one('th[data-stat="season"]')
        season_txt = season_txt.get_text(strip=True) if season_txt else ""

        mp = row.select_one('td[data-stat="games"]') or row.select_one('td[data-stat="mp"]')
        gls = row.select_one('td[data-stat="goals"]') or row.select_one('td[data-stat="gls"]')
        ast = row.select_one('td[data-stat="assists"]') or row.select_one('td[data-stat="ast"]')
        mins = row.select_one('td[data-stat="minutes"]') or row.select_one('td[data-stat="min"]')
        squad = row.select_one('td[data-stat="squad"]')

        def to_int(cell):
            if not cell:
                return 0
            t = cell.get_text(strip=True).replace(",", "")
            return int(t) if t.isdigit() else 0

        mp_i = to_int(mp)
        gls_i = to_int(gls)
        ast_i = to_int(ast)
        mins_i = to_int(mins)
        squad_txt = squad.get_text(" ", strip=True) if squad else ""

        # score: priorité saison demandée, sinon minutes
        score = mins_i
        if season and season_txt == season:
            score += 1_000_000  # force la saison courante
        if club_hint and club_hint.lower() in squad_txt.lower():
            score += 50_000     # bonus si club match

        if score > best_score:
            best_score = score
            best = {
                "fbref_url": player_url,
                "fbref_season": season_txt,
                "appearances": mp_i,
                "goals": gls_i,
                "assists": ast_i,
                "minutes_played": mins_i,
            }

    return best

def fbref_stats_for_player(player_name: str, season: str | None = None, club_hint: str | None = None) -> dict | None:
    candidates = fbref_search_candidates(player_name, limit=8)
    if not candidates:
        return None

    target = _normalize_name_basic(player_name)
    candidates = sorted(
        candidates,
        key=lambda candidate: _name_similarity(candidate["name"], target),
        reverse=True,
    )

    for candidate in candidates[:4]:
        time.sleep(0.5)
        stats = fbref_scrape_standard(candidate["url"], season=season, club_hint=club_hint)
        if stats and (stats.get("appearances", 0) > 0 or stats.get("minutes_played", 0) > 0):
            stats["position_fbref"] = stats.get("position_fbref")
            return stats

    time.sleep(0.5)
    return fbref_scrape_standard(candidates[0]["url"], season=season, club_hint=club_hint)

# ========== WIKIDATA SCRAPING (Source stable pour données de base) ==========

WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"

def _parse_wikidata_time(time_str: str) -> date | None:
    # "+2006-07-13T00:00:00Z"
    try:
        s = time_str.strip()
        if s.startswith("+"):
            s = s[1:]
        return date.fromisoformat(s.split("T")[0])
    except Exception:
        return None

def _age_from_dob(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def _clean_text(s: str | None) -> str | None:
    if not s:
        return None
    s = re.sub(r"[\u200b\u200e\u200f]", "", s)
    s = " ".join(s.split()).strip()
    return s or None

def _pos_normalize(label: str) -> str:
    l = (label or "").lower()
    # normalisation simple pour ton UI
    if "goalkeeper" in l or "gardien" in l:
        return "Goalkeeper"
    if "defender" in l or "back" in l or "défenseur" in l:
        return "Defender"
    if "midfielder" in l or "milieu" in l:
        return "Midfielder"
    if "forward" in l or "winger" in l or "atta" in l:
        return "Forward"
    # fallback
    return label

def wikidata_search_qid(player_name: str, lang: str = "en") -> str | None:
    params = {
        "action": "wbsearchentities",
        "format": "json",
        "search": player_name,
        "language": lang,
        "limit": 8,
        "type": "item"
    }
    r = requests.get(WIKIDATA_API, params=params, headers=HEADERS, timeout=10)
    if r.status_code != 200:
        return None
    data = r.json()
    results = data.get("search", [])
    if not results:
        return None

    best_qid = None
    best_score = 0.0
    for result in results:
        label = result.get("label", "")
        description = (result.get("description") or "").lower()
        score = _name_similarity(label, player_name)
        if any(term in description for term in ("football", "soccer", "association football")):
            score += 0.25
        if score > best_score:
            best_score = score
            best_qid = result.get("id")

    return best_qid if best_score >= 0.55 else None

def wikidata_get_entity(qid: str) -> dict | None:
    url = WIKIDATA_ENTITY.format(qid=qid)
    r = requests.get(url, headers=HEADERS, timeout=12)
    if r.status_code != 200:
        return None
    return r.json()

def _wd_get_label(entity: dict, qid: str, lang="en") -> str | None:
    try:
        labels = entity["entities"][qid]["labels"]
        return labels.get(lang, {}).get("value") or labels.get("fr", {}).get("value")
    except Exception:
        return None

def _wd_resolve_label(qid: str, lang="en") -> str | None:
    ent = wikidata_get_entity(qid)
    if not ent:
        return None
    return _wd_get_label(ent, qid, lang=lang)

def _wd_claims(entity: dict, qid: str, pid: str) -> list:
    try:
        return entity["entities"][qid]["claims"].get(pid, [])
    except Exception:
        return []

def _wd_first_qid(entity: dict, qid: str, pid: str) -> str | None:
    claims = _wd_claims(entity, qid, pid)
    for c in claims:
        dv = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(dv, dict) and "id" in dv:
            return dv["id"]
    return None

def _wd_time(entity: dict, qid: str, pid: str) -> date | None:
    claims = _wd_claims(entity, qid, pid)
    if not claims:
        return None
    dv = claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
    t = dv.get("time")
    return _parse_wikidata_time(t) if t else None

def _wd_quantity(entity: dict, qid: str, pid: str) -> tuple[float | None, str | None]:
    # returns (amount, unit_url)
    claims = _wd_claims(entity, qid, pid)
    if not claims:
        return None, None
    dv = claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", {})
    amount = dv.get("amount")
    unit = dv.get("unit")
    try:
        if amount is None:
            return None, unit
        return float(str(amount).replace("+", "")), unit
    except Exception:
        return None, unit

def _wd_best_current_club_qid(entity: dict, qid: str) -> str | None:
    """
    P54 = club actuel/ancien club.
    On choisit en priorité :
      1) un statement sans date de fin (qualifier P582 absent)
      2) parmi ceux-ci, celui avec la date de début (P580) la plus récente
      3) fallback: premier
    """
    claims = _wd_claims(entity, qid, "P54")
    if not claims:
        return None

    def get_qid(c):
        dv = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        return dv.get("id") if isinstance(dv, dict) else None

    def get_qual_date(c, pid):
        q = c.get("qualifiers", {}).get(pid, [])
        if not q:
            return None
        dv = q[0].get("datavalue", {}).get("value", {})
        t = dv.get("time")
        return _parse_wikidata_time(t) if t else None

    best = None
    best_start = date(1900, 1, 1)

    for c in claims:
        club_qid = get_qid(c)
        if not club_qid:
            continue

        club_label = _wd_resolve_label(club_qid, "en") or ""
        if _is_reserve_team(club_label):
            continue

        end = get_qual_date(c, "P582")   # end time
        start = get_qual_date(c, "P580") # start time

        if end is None:
            # club en cours
            if start and start > best_start:
                best_start = start
                best = club_qid
            elif best is None:
                best = club_qid

    if best:
        return best

    for c in claims:
        club_qid = get_qid(c)
        if not club_qid:
            continue
        club_label = _wd_resolve_label(club_qid, "en") or ""
        if not _is_reserve_team(club_label):
            return club_qid

    # fallback
    return get_qid(claims[0])

def wikidata_profile(player_name: str) -> dict | None:
    qid = wikidata_search_qid(player_name, lang="en")
    if not qid:
        return None

    entity = wikidata_get_entity(qid)
    if not entity:
        return None

    out = {"wikidata_qid": qid, "name": _wd_get_label(entity, qid, "en") or player_name}

    # age (P569)
    dob = _wd_time(entity, qid, "P569")
    if dob:
        out["age"] = _age_from_dob(dob)

    # nationality (P27)
    nat_qid = _wd_first_qid(entity, qid, "P27")
    if nat_qid:
        out["nationality"] = _wd_resolve_label(nat_qid, "en")

    # position (P413)
    pos_qid = _wd_first_qid(entity, qid, "P413")
    if pos_qid:
        pos_label = _wd_resolve_label(pos_qid, "en")
        if pos_label:
            out["position"] = _pos_normalize(pos_label)

    # height (P2048) - ✅ Fix: gestion cm -> m
    amount, unit = _wd_quantity(entity, qid, "P2048")
    if amount is not None:
        # unit url finira souvent par Q11573 (metre) ou Q174728 (centimetre)
        if unit and unit.endswith("Q174728"):  # centimetre
            out["height"] = f"{amount/100:.2f} m"
        else:
            # la plupart du temps c'est déjà en mètres
            out["height"] = f"{amount:.2f} m"

    # current club (P54) - ✅ Fix: prend le bon club (sans date de fin ou le plus récent)
    club_qid = _wd_best_current_club_qid(entity, qid)
    if club_qid:
        out["current_club"] = _wd_resolve_label(club_qid, "en")

    # image (P18)
    p18 = _wd_claims(entity, qid, "P18")
    if p18:
        dv = p18[0].get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(dv, str) and dv.strip():
            out["image_url"] = f"https://commons.wikimedia.org/wiki/Special:FilePath/{quote(dv)}"

    # nettoyage
    out = {k: _clean_text(v) if isinstance(v, str) else v for k, v in out.items()}
    return out

def merge_keep_existing(dst: dict, src: dict) -> dict:
    """
    Merge src dans dst en ne remplaçant que si la valeur src n'est pas None/vide.
    """
    for k, v in src.items():
        if v is not None and v != "":
            dst[k] = v
    return dst

def merge_supplement(dst: dict, src: dict, protected_keys: set[str]) -> dict:
    """Complète dst avec src sans écraser les champs déjà renseignés."""
    for key, value in src.items():
        if key in protected_keys and dst.get(key):
            continue
        if value is not None and value != "":
            dst[key] = value
    return dst

def _has_stats(data: dict) -> bool:
    if data.get("stats_available") is True:
        return True
    return any(data.get(field) not in (None, 0, "") for field in ("goals", "assists", "appearances"))

def current_fb_season(today: date | None = None) -> str:
    """Saison FBref probable (format YYYY-YYYY). On bascule en juillet."""
    if today is None:
        today = date.today()
    y = today.year
    return f"{y}-{y+1}" if today.month >= 7 else f"{y-1}-{y}"

def current_season_str() -> str:
    """Alias pour compatibilité."""
    return current_fb_season()

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

        # ✅ Fix: calculer les colonnes AVANT de fermer la connexion
        columns = [d[0] for d in cur.description] if cur.description else []
        conn.close()

        if row:
            return dict(zip(columns, row))

        return None

    except Exception as e:
        print(f"Erreur DB lors de la sauvegarde: {e}")
        import traceback
        print(traceback.format_exc())
        if 'conn' in locals():
            conn.close()
        return None


def scrape_and_save_player_data(player_name: str):
    """
    Pipeline robuste: Transfermarkt -> Wikidata -> FBref
    """
    print(f"--- Lancement du scraping pour : {player_name} ---")

    try:
        normalized_name = (
            normalize_player_name_with_openai(player_name)
            if openai_available()
            else player_name.strip()
        )
        print(f"-> Nom normalisé: '{player_name}' -> '{normalized_name}'")

        all_data = {"name": normalized_name}

        # 1) Transfermarkt en premier (club, stats, valeur marchande)
        try:
            tm_url = get_player_page_url(normalized_name, "transfermarkt")
            if tm_url:
                tm_data = scrape_transfermarkt(tm_url) or {}
                all_data = merge_keep_existing(all_data, tm_data)
                all_data["source_transfermarkt"] = tm_url
                print(
                    f"-> Transfermarkt OK: club={all_data.get('current_club')} "
                    f"apps={all_data.get('appearances')} g={all_data.get('goals')} a={all_data.get('assists')}"
                )
            else:
                print("-> Transfermarkt: aucun profil trouvé")
        except Exception as e:
            print(f"-> Erreur scraping Transfermarkt: {e}")

        # 2) Wikidata pour compléter les champs manquants
        try:
            wd = wikidata_profile(all_data.get("name", normalized_name))
            if wd:
                protected = {"current_club", "market_value", "position", "position_tm"}
                if _has_stats(all_data):
                    protected.update({"goals", "assists", "appearances", "minutes_played", "stats_source"})
                all_data = merge_supplement(all_data, wd, protected)
                print(
                    f"-> Wikidata OK: age={all_data.get('age')} "
                    f"pos={all_data.get('position')} nat={all_data.get('nationality')}"
                )
            else:
                print("-> Wikidata: aucun résultat")
        except Exception as e:
            print(f"-> Erreur scraping Wikidata: {e}")

        # 3) Stats saison (TM ceapi prioritaire, FBref en fallback)
        try:
            if all_data.get("source_transfermarkt") or not _has_stats(all_data):
                stats = fetch_player_statistics(
                    all_data.get("name", normalized_name),
                    tm_url=all_data.get("source_transfermarkt"),
                    club_hint=all_data.get("current_club"),
                )
                if stats:
                    all_data = merge_keep_existing(all_data, stats)
        except Exception as e:
            print(f"-> Erreur récupération stats: {e}")

        all_data["stats_available"] = _has_stats(all_data)

        # 4) Valeurs par défaut propres (évite null/None en front)
        for k in ("goals", "assists", "appearances", "minutes_played"):
            if all_data.get(k) is None:
                all_data[k] = 0

        # 5) Image fallback Wikipedia si absent
        if not all_data.get("image_url"):
            try:
                img = scrape_wikipedia_image(all_data.get("name", normalized_name))
                if img:
                    all_data["image_url"] = img
            except Exception as e:
                print(f"-> Erreur image: {e}")

        # 6) Sauvegarde DB
        try:
            saved = save_player_to_db(all_data)
            if saved:
                saved["stats_available"] = all_data.get("stats_available", False)
                saved["stats_season"] = all_data.get("stats_season")
                saved["stats_source"] = all_data.get("stats_source")
                print(f"-> Données sauvegardées pour {saved.get('name')}")
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
