import sqlite3
from pathlib import Path

DB_PATH = Path("domaine.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT UNIQUE,
        customer_name TEXT,
        customer_phone TEXT,
        created_at_iso TEXT,
        items_json TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        msg_type TEXT,
        sent_at_iso TEXT
    )""")
    conn.commit()
    conn.close()
