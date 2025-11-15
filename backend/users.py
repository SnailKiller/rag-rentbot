# backend/users.py
from backend.db import get_conn
import hashlib

def hash_pw(pw: str):
    """生成 SHA256 哈希"""
    return hashlib.sha256(pw.encode()).hexdigest()

def register_user(username, password, role, landlord_username=None, house_id=None):
    """注册用户，如果是租客则绑定房东 & house_id"""
    conn = get_conn()
    cur = conn.cursor()

    landlord_id = None
    if role == "tenant" and landlord_username:
        cur.execute("SELECT id FROM users WHERE username=? AND role='landlord'", (landlord_username,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False, "Landlord not found."
        landlord_id = row["id"]

    try:
        cur.execute("""
            INSERT INTO users (username, password, role, landlord_id, tenant_house_id)
            VALUES (?, ?, ?, ?, ?)
        """, (username, hash_pw(password), role, landlord_id, house_id))
        conn.commit()
        return True, "Registered successfully!"
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()


def login_user(username, password):
    """验证用户名和密码"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return False, "❌ User not found."
    if hash_pw(password) != row["password"]:
        return False, "❌ Invalid password."
    return True, dict(row)

def get_user_id_by_name(username):
    """Return user ID from username"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row["id"]
    return None
