# backend/house_kb.py
import os
from backend.db import get_conn
from datetime import datetime
from backend.rag_pipeline import add_document_from_file

HOUSE_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "../data/house_kb")
os.makedirs(HOUSE_UPLOAD_DIR, exist_ok=True)

# ----------------------------
# Create a house for landlord
# ----------------------------
def create_house(landlord_id, house_name, address):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO houses (landlord_id, house_name, address, created_at)
        VALUES (?, ?, ?, ?)
    """, (landlord_id, house_name, address, datetime.utcnow().isoformat()))

    hid = cur.lastrowid
    conn.commit()
    conn.close()
    return hid


# ----------------------------
# List all houses belonging to a landlord
# ----------------------------
def list_houses(landlord_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM houses WHERE landlord_id=? ORDER BY created_at DESC", (landlord_id,))
    rows = [dict(r) for r in cur.fetchall()]

    conn.close()
    return rows


# ----------------------------
# Upload a document into a house KB
# ----------------------------
def upload_house_document(house_id, file_bytes, filename):
    """
    1. 把房东上传的 KB 文件存到磁盘
    2. 写入 house_documents 表
    3. 同时送进 RAG（调用 add_document_from_file 更新 VEC_STORE）
    """
    safe_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
    save_path = os.path.join(HOUSE_UPLOAD_DIR, safe_name)

    # 1️⃣ 保存文件到本地
    with open(save_path, "wb") as f:
        f.write(file_bytes)

    # 2️⃣ 同步到 RAG（关键的一步）
    lower = filename.lower()
    try:
        if lower.endswith(".pdf"):
            # 用二进制方式重新打开，让 rag_pipeline 自己抽取文本
            with open(save_path, "rb") as f:
                add_document_from_file(f, file_type="pdf")
        else:
            # 其他当作文本
            with open(save_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            add_document_from_file(text, file_type="txt")

        print(f"[house_kb] Indexed house document into RAG: {save_path}")
    except Exception as e:
        print(f"[house_kb] Error indexing house document into RAG: {e}")

    # 3️⃣ 写入 house_documents 表（用于 UI 展示“已有 KB”）
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO house_documents (house_id, file_path, uploaded_at)
        VALUES (?, ?, ?)
    """, (house_id, save_path, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    return save_path


# ----------------------------
# Retrieve ALL documents in a house KB
# ----------------------------
def get_house_docs(house_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM house_documents WHERE house_id=?", (house_id,))
    rows = [dict(r) for r in cur.fetchall()]

    conn.close()
    return rows

def has_house_kb(house_id):
    """Return True if the house has at least one KB document."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM house_documents WHERE house_id=?", (house_id,))
    row = cur.fetchone()
    conn.close()
    return row["c"] > 0


def load_house_kb_into_rag(house_id):
    """
    从数据库中读取 house 所有文件，然后自动构建向量库（VEC_STORE）
    在用户登录或进入 Chat 页面时调用
    """
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT file_path FROM house_documents WHERE house_id=?", (house_id,))
    files = [r["file_path"] for r in cur.fetchall()]
    conn.close()

    if not files:
        return False, "No KB files found."

    for fpath in files:
        try:
            lower = fpath.lower()
            if lower.endswith(".pdf"):
                with open(fpath, "rb") as f:
                    add_document_from_file(f, file_type="pdf")
            else:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    add_document_from_file(f.read(), file_type="txt")
        except Exception as e:
            print("[load_house_kb_into_rag] error:", e)

    return True, "Loaded KB into RAG."
