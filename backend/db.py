# backend/db.py
import sqlite3
import os
from contextlib import closing
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/rentbot.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        # users table (simple demo)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            role TEXT CHECK(role IN ('tenant','landlord')),
            created_at TEXT
        )
        """)
        # tickets / work orders
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            category TEXT,
            priority TEXT,
            status TEXT DEFAULT 'open',
            creator TEXT,
            creator_role TEXT,
            attachment_path TEXT,
            landlord_response TEXT,
            landlord_attachment TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)
        conn.commit()

# convenience: create a user if not exists
def ensure_user(username: str, role: str):
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()
        cur.execute("SELECT id FROM users WHERE username=?",(username,))
        r = cur.fetchone()
        if r:
            return r["id"]
        cur.execute("INSERT INTO users (username, role, created_at) VALUES (?,?,?)", (username, role, now))
        conn.commit()
        return cur.lastrowid

# call init on import
init_db()
