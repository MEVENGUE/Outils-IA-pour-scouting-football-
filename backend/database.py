# Filename: backend/database.py
# Description: Module centralisé pour toutes les opérations de base de données

import sqlite3
import os
from typing import Optional, Dict, Any, List

# Configuration centralisée de la base de données
DB_NAME = "players.db"
# Chemin unique vers la DB dans le dossier scraping
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'scraping', DB_NAME)

def get_db_connection():
    """Retourne une connexion à la base de données avec row_factory configuré."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise la base de données avec toutes les tables nécessaires."""
    conn = get_db_connection()
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
        position_tm TEXT,
        position_fbref TEXT,
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
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
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
        created_at TEXT
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
        created_at TEXT
    )
    """)
    
    # Ajoute les colonnes si elles n'existent pas (migration)
    columns_to_add = [
        'scouting_report', 'image_url', 'weight', 'yellow_cards', 
        'red_cards', 'minutes_played', 'goals_per_match', 'assists_per_match',
        'contract_expires', 'position_tm', 'position_fbref', 'created_at', 'updated_at'
    ]
    for col in columns_to_add:
        try:
            if col in ['goals_per_match', 'assists_per_match']:
                cur.execute(f"ALTER TABLE players ADD COLUMN {col} REAL")
            elif col in ['yellow_cards', 'red_cards', 'minutes_played']:
                cur.execute(f"ALTER TABLE players ADD COLUMN {col} INTEGER")
            elif col in ['created_at', 'updated_at']:
                cur.execute(f"ALTER TABLE players ADD COLUMN {col} TEXT DEFAULT CURRENT_TIMESTAMP")
            else:
                cur.execute(f"ALTER TABLE players ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass  # La colonne existe déjà
    
    conn.commit()
    conn.close()

def save_player_to_db(player_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Insère ou met à jour les données d'un joueur avec gestion d'erreurs améliorée."""
    if not player_data or not player_data.get('name'):
        print("-> Données invalides pour la sauvegarde")
        return None
    
    try:
        init_db()  # S'assure que la DB est initialisée
        conn = get_db_connection()
        cur = conn.cursor()

        # On s'assure que toutes les colonnes existent
        cur.execute("PRAGMA table_info(players)")
        table_columns = {row[1] for row in cur.fetchall()}
        
        # Filtre les données pour ne garder que les colonnes existantes
        valid_data = {k: v for k, v in player_data.items() if k in table_columns and v is not None}
        
        if not valid_data or 'name' not in valid_data:
            print("-> Aucune donnée valide à sauvegarder")
            conn.close()
            return None

        # Construit la requête SQL de manière plus sûre
        columns = list(valid_data.keys())
        if not columns:
            print("-> Aucune colonne valide pour la sauvegarde")
            conn.close()
            return None
            
        placeholders = ', '.join('?' * len(columns))
        columns_str = ', '.join(columns)
        
        # Utilise INSERT OR REPLACE de manière plus sûre
        sql = f"INSERT OR REPLACE INTO players ({columns_str}) VALUES ({placeholders})"
        
        # Prépare les valeurs dans le bon ordre et convertit None en NULL SQL
        values = []
        for col in columns:
            val = valid_data[col]
            # Convertit None en chaîne vide pour les champs TEXT
            if val is None:
                val = ''
            values.append(val)

        cur.execute(sql, values)
        conn.commit()
        
        # Récupère le joueur sauvegardé
        player_name = valid_data.get('name')
        cur.execute("SELECT * FROM players WHERE name = ?", (player_name,))
        row = cur.fetchone()
        
        if row:
            saved_player = dict(row)
            conn.close()
            return saved_player
        else:
            conn.close()
            return None
            
    except sqlite3.Error as e:
        print(f"Erreur DB lors de la sauvegarde de {player_data.get('name')}: {e}")
        import traceback
        print(f"Traceback DB: {traceback.format_exc()}")
        if 'conn' in locals():
            conn.close()
        return None
    except Exception as e:
        print(f"Erreur inattendue lors de la sauvegarde: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        if 'conn' in locals():
            conn.close()
        return None

def update_player_field(player_name: str, field: str, value: Any) -> bool:
    """Met à jour un champ spécifique d'un joueur."""
    if not player_name or not field:
        return False
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Vérifie que la colonne existe
        cur.execute("PRAGMA table_info(players)")
        table_columns = {row[1] for row in cur.fetchall()}
        
        if field not in table_columns:
            print(f"-> Colonne '{field}' n'existe pas dans la table players")
            conn.close()
            return False
        
        # Vérifie si la colonne updated_at existe avant de l'utiliser
        if 'updated_at' in table_columns:
            cur.execute(f"UPDATE players SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE name = ?", 
                       (value, player_name))
        else:
            cur.execute(f"UPDATE players SET {field} = ? WHERE name = ?", 
                       (value, player_name))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"-> Erreur lors de la mise à jour de {field} pour {player_name}: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def get_player_by_name(player_name: str) -> Optional[Dict[str, Any]]:
    """Récupère un joueur par son nom (recherche exacte ou partielle)."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM players WHERE name LIKE ? LIMIT 1", (f"%{player_name}%",))
        row = cur.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération du joueur {player_name}: {e}")
        if 'conn' in locals():
            conn.close()
        return None

def get_player_by_id(player_id: int) -> Optional[Dict[str, Any]]:
    """Récupère un joueur par son ID."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM players WHERE id = ?", (player_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None
    except Exception as e:
        print(f"Erreur lors de la récupération du joueur ID {player_id}: {e}")
        if 'conn' in locals():
            conn.close()
        return None

def list_players(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Récupère la liste des joueurs avec filtres optionnels."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = "SELECT * FROM players WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('name'):
                query += " AND name LIKE ?"
                params.append(f"%{filters['name']}%")
            if filters.get('country'):
                query += " AND nationality = ?"
                params.append(filters['country'])
            if filters.get('position'):
                query += " AND position = ?"
                params.append(filters['position'])
            if filters.get('max_age'):
                query += " AND age <= ?"
                params.append(filters['max_age'])
        
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Erreur lors de la récupération de la liste des joueurs: {e}")
        if 'conn' in locals():
            conn.close()
        return []

