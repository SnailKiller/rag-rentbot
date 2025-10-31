# app.py
import streamlit as st
import sys, os, uuid, tempfile, time
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# RAG 接口（与你现有的保持一致）
from backend.rag_pipeline import add_document_from_file, query_rag, is_fitted

try:
    from backend import tickets as ticket_mod
    from backend.db import ensure_user
    HAVE_TICKETS = True
except Exception:
    HAVE_TICKETS = False

st.set_page_config(page_title="Contract Q&A + Tickets", layout="wide")
st.title("📄 Contract Q&A Assistant — with Tickets")

# -------------------------
# Session init
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_uploaded" not in st.session_state:
    st.session_state.doc_uploaded = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

# -------------------------
# Sidebar: login + upload
# -------------------------
st.sidebar.header("Account / Upload")
if st.session_state.current_user:
    u = st.session_state.current_user
    st.sidebar.markdown(f"**User:** {u['username']}  \n**Role:** {u['role']}")
    if st.sidebar.button("Logout"):
        st.session_state.current_user = None
        st.rerun()
else:
    name = st.sidebar.text_input("Username", key="login_name")
    role = st.sidebar.selectbox("Role", ["tenant", "landlord"], key="login_role")
    if st.sidebar.button("Login"):
        if not name.strip():
            st.sidebar.error("Enter username")
        else:
            if HAVE_TICKETS:
                ensure_user(name.strip(), role)
            st.session_state.current_user = {"username": name.strip(), "role": role}
            st.sidebar.success("Logged in")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Upload & Index Document")
uploaded_file = st.sidebar.file_uploader("Upload contract (pdf/txt)", type=["pdf","txt","docx","doc","png","jpg","jpeg"])
if uploaded_file:
    st.sidebar.write(f"File: {uploaded_file.name}")
    if st.sidebar.button("Index Document"):
        try:
            with st.spinner("Extracting & indexing..."):
                # Determine file type
                lower = uploaded_file.name.lower()
                if lower.endswith(".pdf"):
                    add_document_from_file(uploaded_file, file_type="pdf")
                else:
                    # read as text
                    content = uploaded_file.read()
                    try:
                        text = content.decode("utf-8")
                    except:
                        text = content.decode("latin-1", errors="ignore")
                    add_document_from_file(text, file_type="txt")
                st.session_state.doc_uploaded = True
                st.sidebar.success("Indexed")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# 🌈 自定义侧边栏导航样式
st.sidebar.markdown(
    """
    <style>
    /* 整个侧边栏 */
    section[data-testid="stSidebar"] > div {
        background-color: #f8f9fa;
        padding-top: 20px;
    }
    /* 导航项整体 */
    div[data-testid="stRadio"] label {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 6px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        font-weight: 500;
        font-size: 15px;
    }
    /* 悬浮时效果 */
    div[data-testid="stRadio"] label:hover {
        background-color: #e9ecef;
    }
    /* 选中项高亮 */
    div[data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
        background-color: #007BFF !important;
        color: white !important;
        font-weight: 600 !important;
        box-shadow: 0px 0px 6px rgba(0,0,0,0.15);
    }
    /* 隐藏默认圆点 */
    div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"] {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 🧭 侧边栏导航栏
st.sidebar.subheader("Navigation")
page = st.sidebar.radio(
    label="Navigation menu",
    label_visibility="collapsed",   # ✅ 隐藏显示但保留语义
    options=["💬 Chat", "🛠 Submit Ticket", "📋 My Tickets", "🏠 Landlord Panel"],
    index=0,
)


# -------------------------
# Main: Chat
# -------------------------
if page == "💬 Chat":
    st.header("💬 Chat (RAG)")
    if not is_fitted():
        st.info("Please upload and index a document from the sidebar first.")
    else:
        # show chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        # input
        if prompt := st.chat_input("Ask about the contract..."):
            with st.chat_message("user"):
                st.write(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.spinner("Retrieving and generating answer..."):
                try:
                    answer = query_rag(prompt, top_k=3)
                except Exception as e:
                    answer = f"Error during query: {e}"
            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

# -------------------------
# Submit Ticket (Tenant)
# -------------------------
elif page == "🛠 Submit Ticket":
    st.header("🛠 Submit Maintenance Ticket")
    if not st.session_state.current_user or st.session_state.current_user["role"] != "tenant":
        st.warning("You must login as a tenant to submit tickets.")
    elif not HAVE_TICKETS:
        st.error("Ticketing backend is not available (backend/tickets.py missing).")
    else:
        with st.form("ticket_form", clear_on_submit=True):
            title = st.text_input("Title")
            category = st.selectbox("Category", ["Plumbing", "Electrical", "Appliance", "Lock/Key", "Other"])
            priority = st.selectbox("Priority", ["Low", "Normal", "High", "Urgent"])
            description = st.text_area("Describe the issue", height=200)
            att = st.file_uploader("Attach photo/doc (optional)", type=["png","jpg","jpeg","pdf","docx","doc"])
            submitted = st.form_submit_button("Submit Ticket")
            if submitted:
                if not title.strip() or not description.strip():
                    st.error("Please fill title and description.")
                else:
                    att_bytes = att.read() if att else None
                    att_name = att.name if att else None
                    tid = ticket_mod.create_ticket(title, description, category, priority,
                                                   st.session_state.current_user["username"],
                                                   st.session_state.current_user["role"],
                                                   attachment_file=att_bytes, attachment_name=att_name)
                    st.success(f"Ticket {tid} created.")
                    st.rerun()

# -------------------------
# My Tickets (Tenant)
# -------------------------
elif page == "📋 My Tickets":
    st.header("📋 My Tickets")

    if not st.session_state.current_user:
        st.warning("Please log in.")
    elif not HAVE_TICKETS:
        st.error("Ticketing backend not available.")
    else:
        user = st.session_state.current_user["username"]
        rows = ticket_mod.list_tickets(filter_by={"creator": user})

        if not rows:
            st.info("You have no tickets.")
        else:
            # 🎨 CSS 样式部分
            st.markdown("""
            <style>
            .ticket-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                grid-gap: 1rem;
                margin-top: 1rem;
            }
            .ticket-card {
                position: relative;
                padding: 16px 14px;
                border-radius: 12px;
                color: white;
                box-shadow: 0 3px 8px rgba(0,0,0,0.1);
                transition: all 0.25s ease-in-out;
                overflow: hidden;
                word-break: break-word;
            }
            .ticket-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 5px 12px rgba(0,0,0,0.15);
            }
            .ticket-title {
                font-weight: 700;
                font-size: 18px;
                margin-bottom: 6px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .ticket-meta {
                font-size: 14px;
                opacity: 0.9;
                margin-bottom: 8px;
            }
            .ticket-desc {
                font-size: 14px;
                opacity: 0.95;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            /* 状态标签 */
            .status-badge {
                position: absolute;
                top: 10px;
                right: 12px;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 8px;
                border-radius: 6px;
                color: white;
                text-transform: uppercase;
            }
            .status-open { background-color: #0d6efd; }        /* 蓝色 */
            .status-inprogress { background-color: #ffc107; color: black; }  /* 黄色 */
            .status-closed { background-color: #198754; }      /* 绿色 */
            /* 优先级背景色 */
            .priority-Low { background-color: #cfe3d7; }        /* 绿色 */
            .priority-Normal { background-color: #abd6df; }     /* 蓝色 */
            .priority-High { background-color: #efe59a; }       /* 红色 */
            .priority-Urgent { background-color: #d57c6f; }     /* 紫色 */
            </style>
            """, unsafe_allow_html=True)

            # 🎛️ 网格布局开始
            st.markdown('<div class="ticket-grid">', unsafe_allow_html=True)

            for r in rows:
                priority = r.get("priority", "Normal").capitalize()
                status = r.get("status", "open").lower().replace(" ", "")
                title = r.get("title", "Untitled")
                desc = r.get("description", "")
                category = r.get("category", "General")

                st.markdown(f"""
                <div class="ticket-card priority-{priority}">
                    <div class="status-badge status-{status}">{r['status']}</div>
                    <div class="ticket-title">#{r['id']} {title}</div>
                    <div class="ticket-meta">
                        Category: {category} <br>
                        Priority: <b>{priority}</b>
                    </div>
                    <div class="ticket-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

# -------------------------
# Landlord Panel
# -------------------------
elif page == "🏠 Landlord Panel":
    st.header("🏠 Landlord Panel")
    if not st.session_state.current_user or st.session_state.current_user["role"] != "landlord":
        st.warning("You must be a landlord to view this.")
    elif not HAVE_TICKETS:
        st.error("Ticketing backend not available.")
    else:
        st.subheader("Open tickets")
        opens = ticket_mod.list_tickets(filter_by={"status": "open"})
        if not opens:
            st.info("No open tickets.")
        else:
            for t in opens:
                st.markdown(f"**#{t['id']} {t['title']}** — by {t['creator']} at {t['created_at']}")
                st.markdown(f"{t['description']}")
                if t.get("attachment_path"):
                    st.markdown(f"Attachment: `{t['attachment_path']}`")
                with st.form(f"resp_{t['id']}", clear_on_submit=True):
                    resp = st.text_area("Response / Action taken", key=f"resp_{t['id']}")
                    new_status = st.selectbox("Set status", ["in_progress", "resolved"], key=f"status_{t['id']}")
                    att = st.file_uploader("Attach result (optional)", key=f"landlord_att_{t['id']}")
                    if st.form_submit_button("Submit Response"):
                        att_bytes = att.read() if att else None
                        att_name = att.name if att else None
                        ok = ticket_mod.update_ticket_response(t['id'],
                                                               landlord_response=resp,
                                                               landlord_attachment_bytes=att_bytes,
                                                               landlord_attachment_name=att_name,
                                                               new_status=new_status)
                        if ok:
                            st.success("Response saved.")
                            st.rerun()
                        else:
                            st.error("No changes submitted.")

        st.markdown("---")
        st.subheader("All tickets")
        all_t = ticket_mod.list_tickets()
        for t in all_t:
            st.text(f"#{t['id']} {t['title']} — {t['status']}")
