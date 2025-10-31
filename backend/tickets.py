# backend/tickets.py
import os
from backend.db import get_conn
from datetime import datetime
import shutil

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../data/ticket_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def create_ticket(title, description, category, priority, creator, creator_role, attachment_file=None, attachment_name=None):
    """保存附件文件并写入 tickets 表，返回 ticket id"""
    att_path = None
    if attachment_file and attachment_name:
        safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{attachment_name}"
        att_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(att_path, "wb") as f:
            f.write(attachment_file)
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tickets (title, description, category, priority, creator, creator_role, attachment_path, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (title, description, category, priority, creator, creator_role, att_path, now, now))
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    return tid

def list_tickets(filter_by=None):
    """filter_by: dict e.g. {'creator': 'alice'} or {'status':'open'}"""
    conn = get_conn()
    cur = conn.cursor()
    q = "SELECT * FROM tickets"
    params = []
    if filter_by:
        clauses = []
        for k,v in filter_by.items():
            clauses.append(f"{k}=?")
            params.append(v)
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY created_at DESC"
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_ticket(ticket_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,))
    r = cur.fetchone()
    conn.close()
    return dict(r) if r else None

def update_ticket_response(ticket_id, landlord_response=None, landlord_attachment_bytes=None, landlord_attachment_name=None, new_status=None):
    att_path = None
    if landlord_attachment_bytes and landlord_attachment_name:
        safe_name = f"resp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{landlord_attachment_name}"
        att_path = os.path.join(UPLOAD_DIR, safe_name)
        with open(att_path, "wb") as f:
            f.write(landlord_attachment_bytes)
    now = datetime.utcnow().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    # build update
    updates = []
    params = []
    if landlord_response is not None:
        updates.append("landlord_response=?")
        params.append(landlord_response)
    if att_path:
        updates.append("landlord_attachment=?")
        params.append(att_path)
    if new_status:
        updates.append("status=?")
        params.append(new_status)
    if not updates:
        return False
    updates.append("updated_at=?")
    params.append(now)
    params.append(ticket_id)
    q = f"UPDATE tickets SET {', '.join(updates)} WHERE id=?"
    cur.execute(q, params)
    conn.commit()
    conn.close()
    return True
