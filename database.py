import sqlite3
import os
from datetime import datetime, timedelta

# Ensures the database is always saved in the script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'pingator_v2.db')

# --- DATA RETENTION CONFIGURATION ---
# Quantos dias os registros de ping ficarão salvos no banco de dados.
# Você pode mudar isso para 14, 30, etc.
RETENTION_DAYS = 7

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=15)
    
    # --- HDD SAVING OPTIMIZATIONS ---
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")
    
    return conn

def cleanup_old_pings():
    """Deletes ping records older than RETENTION_DAYS."""
    conn = get_conn()
    c = conn.cursor()
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
    c.execute("DELETE FROM pings WHERE timestamp < ?", (cutoff_date,))
    conn.commit()

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    # Table for network metrics
    c.execute('''CREATE TABLE IF NOT EXISTS pings
                 (timestamp TIMESTAMP, main_target TEXT, pinged_ip TEXT, latency REAL, packet_loss INTEGER)''')
                 
    # --- PERFORMANCE INDEXES ---
    # Faz com que os gráficos carreguem muito mais rápido e a deleção seja instantânea
    c.execute('CREATE INDEX IF NOT EXISTS idx_pings_timestamp ON pings(timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_pings_main_target ON pings(main_target)')
                 
    # Table to persist UI tabs
    c.execute('''CREATE TABLE IF NOT EXISTS targets (target TEXT UNIQUE)''')
    
    # Table for general app settings (like remembering the last open tab)
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT UNIQUE, value TEXT)''')

    # Auto-migrate: Add timeframe column if upgrading from an older version
    try:
        c.execute("ALTER TABLE targets ADD COLUMN timeframe INTEGER DEFAULT 10")
    except sqlite3.OperationalError:
        pass 

    conn.commit()
    
    # Runs the cleanup routine every time the database initializes (app startup)
    cleanup_old_pings()
    
    # If the targets table is empty (first run), insert a default target
    c.execute("SELECT count(*) FROM targets")
    if c.fetchone()[0] == 0:
        c.execute("INSERT OR IGNORE INTO targets (target, timeframe) VALUES ('google.com', 10)")
        conn.commit()
        
    return conn

def get_saved_targets():
    """Fetches all saved tabs from the database."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT target FROM targets")
    return [row[0] for row in c.fetchall()]

def add_saved_target(target):
    """Saves a new tab to the database with a default timeframe of 10."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO targets (target, timeframe) VALUES (?, 10)", (target,))
    conn.commit()

def remove_saved_target(target):
    """Deletes a tab from the database."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM targets WHERE target = ?", (target,))
    c.execute("DELETE FROM settings WHERE key = 'last_tab' AND value = ?", (target,))
    conn.commit()

def update_timeframe(target, timeframe):
    """Updates the user's preferred timeframe for a specific target."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE targets SET timeframe = ? WHERE target = ?", (timeframe, target))
    conn.commit()

def get_timeframe(target):
    """Retrieves the saved timeframe for a specific target."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT timeframe FROM targets WHERE target = ?", (target,))
    result = c.fetchone()
    return result[0] if result else 10

# --- SETTINGS FUNCTIONS ---
def set_last_tab(target):
    """Saves the last selected target to remember on startup."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_tab', ?)", (target,))
    conn.commit()

def get_last_tab():
    """Retrieves the last selected target."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'last_tab'")
    result = c.fetchone()
    return result[0] if result else None

def get_setting(key, default_value):
    """Retrieves a generic setting, returns default if not found."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    return int(result[0]) if result else default_value

def set_setting(key, value):
    """Saves a generic setting."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()