# backend/db.py
import sqlite3
import os
from contextlib import closing
from datetime import datetime
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/sp3-4.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # ---- 用户表 ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            landlord_id INTEGER,
            tenant_house_id INTEGER,
            created_at TEXT
        );
    """)

    # ---- 工单表 ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            category TEXT,
            priority TEXT,
            creator TEXT,
            creator_role TEXT,
            attachment_path TEXT,
            status TEXT DEFAULT 'open',
            landlord_response TEXT,
            landlord_attachment TEXT,
            created_at TEXT,
            updated_at TEXT
        );
    """)

    # ---- 房屋表 ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS houses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            landlord_id INTEGER NOT NULL,
            house_name TEXT NOT NULL,
            address TEXT,
            created_at TEXT,
            FOREIGN KEY (landlord_id) REFERENCES users(id)
        );
    """)

    # ---- 房屋知识库文档 ----
    cur.execute("""
        CREATE TABLE IF NOT EXISTS house_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            house_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            rag_doc_id TEXT,
            uploaded_at TEXT,
            FOREIGN KEY (house_id) REFERENCES houses(id)
        );
    """)

    # ---- 用户表补丁：添加 tenant_house_id（如已存在则无视） ----
    try:
        cur.execute("ALTER TABLE users ADD COLUMN tenant_house_id INTEGER;")
    except:
        pass

    conn.commit()
    conn.close()


# convenience: create a user if not exists
from contextlib import closing
from datetime import datetime

def hash_pw(pw: str):
    """简易密码加密函数"""
    return hashlib.sha256(pw.encode()).hexdigest()

def ensure_user(username: str, role: str, password: str = None, landlord_username: str = None):
    """
    确保用户存在于 users 表中；
    如果不存在则创建。
    可选支持密码与绑定房东关系。
    返回用户 id。
    """
    with closing(get_conn()) as conn:
        cur = conn.cursor()
        now = datetime.utcnow().isoformat()

        # 检查是否已存在
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        existing = cur.fetchone()
        if existing:
            return existing["id"]

        # 房东绑定逻辑（仅租客）
        landlord_id = None
        if role == "tenant" and landlord_username:
            cur.execute("SELECT id FROM users WHERE username=? AND role='landlord'", (landlord_username,))
            row = cur.fetchone()
            if row:
                landlord_id = row["id"]

        # 若无密码则设默认密码
        if not password:
            password = "default123"
        hashed = hash_pw(password)

        # 插入用户记录
        cur.execute("""
            INSERT INTO users (username, password, role, landlord_id)
            VALUES (?, ?, ?, ?)
        """, (username, hashed, role, landlord_id))

        conn.commit()
        return cur.lastrowid


# call init on import
init_db()
