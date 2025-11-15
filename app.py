# app.py
import streamlit as st
import sys, os, uuid, tempfile, time
from backend.rag_pipeline import add_document_from_file, query_rag, is_fitted
from openai import OpenAI
from backend import house_kb
from backend import users as user_mod
import base64

def get_image_base64(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except FileNotFoundError:
        st.error(f"图片文件未找到: {path}")
        return None

sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
# RAG 接口（与你现有的保持一致）
from backend.rag_pipeline import add_document_from_file, query_rag, is_fitted

try:
    from backend import tickets as ticket_mod
    from backend.db import ensure_user
    HAVE_TICKETS = True
except Exception:
    HAVE_TICKETS = False

# 【修改点 1】: 所有的 Session State 初始化都移到最前面
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "doc_uploaded" not in st.session_state:
    st.session_state.doc_uploaded = False

# 【修改点 2】: st.set_page_config 必须是第一个 Streamlit 命令
# 我们根据登录状态决定页面布局
if not st.session_state.current_user:
    st.set_page_config(page_title="Login", layout="centered")
else:
    st.set_page_config(page_title="Contract Q&A + Tickets", layout="wide")


# 如果未登录 → 进入登录界面
if not st.session_state.current_user:
    
    # 【修改点 3】: 注入渐变背景 CSS，并美化登录卡片
    st.markdown(
        """
        <style>
        /* 【修改点 1】: 强制隐藏顶部的白边 (Header) 和底部的页脚 */
        [data-testid="stHeader"] {
            display: none;
        }
        footer {
            display: none;
        }
        /* 1. 应用渐变背景到整个应用容器 */
        .stApp {
            background: linear-gradient(135deg, #fdd2ae 0%, #def9dc 100%);
            /* 你可以换成你喜欢的任何渐变色 */
        }
        
        /* 2. 将登录表单容器 .main 变成一个浮动卡片 */
        .main { 
            max-width: 500px; 
            margin: auto; 
            padding: 40px; 
            background: white; /* 卡片是纯白色 */
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            padding-top: 40px;
        }

        /* 3. 保留你其他的自定义样式 */
        .stImage { margin-bottom: 20px; } 
        .login-title { text-align: center; font-size: 28px; font-weight: bold; margin-bottom: 10px; }
        .login-subtitle { text-align: center; color: #666; font-size: 16px; margin-bottom: 30px; }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 1. 创建三列，比例为 1:1:1
    col1, col2, col3 = st.columns([1, 1, 1])

    # 2. 把图片放在中间的列 (col2)
    with col2:
        st.image("assets/rentbot_logo.png", width=200)
    
    st.markdown('<div class="login-title">Welcome to RentBot</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-subtitle">GenAI Customer Service for Tenants & Landlords</div>', unsafe_allow_html=True)

    # 【注意】: 删除了你第二个重复的 <style> 块
    
    st.markdown("### Login or Register")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:  # LOGIN TAB
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pw")

        if st.button("Login", key="login_btn"):
            ok, user = user_mod.login_user(username, password)
            if ok:
                st.session_state.current_user = user
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error(user)


    with tab2:  # REGISTER TAB
        new_user = st.text_input("New Username", key="reg_user")
        new_pw = st.text_input("New Password", type="password", key="reg_pass")
        role = st.selectbox("Account Type", ["tenant", "landlord"], key="reg_role")

        landlord_name = None
        house_id = None

        # ----------------------------
        # Tenant: need to bind landlord + house
        # ----------------------------
        if role == "tenant":
            landlord_name = st.text_input("Landlord Username", key="reg_landlord")

            if landlord_name:
                landlord_id = user_mod.get_user_id_by_name(landlord_name)

                if landlord_id:
                    houses = house_kb.list_houses(landlord_id)

                    if houses:
                        house_options = [f"{h['id']} - {h['house_name']}" for h in houses]
                        selected = st.selectbox("Select House", house_options, key="reg_house_sel")
                        house_id = int(selected.split(" - ")[0])
                    else:
                        st.info("This landlord has no houses yet.")
                else:
                    st.warning("Landlord not found.")

        # ----------------------------
        # Register button (with unique key)
        # ----------------------------
        if st.button("Create Account", key="register_btn"):
            ok, msg = user_mod.register_user(
                new_user,
                new_pw,
                role,
                landlord_username=landlord_name,
                house_id=house_id
            )
            st.success(msg)

    st.stop()



# =========================================================
# (以下是主应用界面，只有登录后才会运行)
# (这里的背景将是 Streamlit 默认的纯色)
# =========================================================

# =========================================================
# 💎 注入全新的 "科技 + 小清新" UI 主题 (V3 修复版)
# =========================================================
st.markdown(
    """
    <style>
    /* === 🎨 Tech + Fresh Theme (Safe Version) === */

    /* 【【【 注意：这里已删除所有隐藏顶栏的代码 】】】 */
    /* 你的侧边栏按钮会 100% 恢复正常 */


    /* 1. Main App Background (保留) */
    .stApp > div:first-child {
        background-color: #F0F4F8; /* 科技蓝灰背景 */
    }

    /* 2. Main Title (保留) */
    h1 {
        font-size: 28px; 
        color: #1E293B;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    h2 {
        font-size: 22px; 
        color: #334155;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    h3 {
        color: #334155; 
        font-size: 18px;
        font-weight: 600;
    }
    /* (你截图中的标题图标是 st.title/st.header 默认的，
       如果你想换回机器人图标，我们可以稍后再做，
       我们先保证功能恢复！) */

    /* 3. Sidebar 样式 (保留) */
    section[data-testid="stSidebar"] > div {
        background-color: #F8FAFC; 
        border-right: 1px solid #EAF0F4; 
        padding-top: 20px;
    }

    /* 4. Sidebar 导航 (保留) */
    div[data-testid="stRadio"] label {
        display: flex;
        align-items: center;
        padding: 10px 14px; 
        border-radius: 8px;
        margin-bottom: 6px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        font-weight: 500;
        font-size: 15px;
        color: #475569; 
    }
    div[data-testid="stRadio"] label:hover {
        background-color: #FFFFFF; 
        color: #0068C9; 
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
        background-color: #E6F0FF !important; 
        color: #00529E !important; 
        font-weight: 600 !important;
        box-shadow: none;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"] {
        display: none;
    }

    /* 5. 表单/卡片 样式 (保留) */
    [data-testid="stForm"], [data-testid="stExpander"] {
        background-color: #FFFFFF;
        border-radius: 12px; 
        padding: 20px 24px;
        border: 1px solid #EAF0F4;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    /* 6. 聊天气泡 (保留) */
    [data-testid="stChatMessage"] {
        background-color: #FFFFFF;
        border-radius: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        border: 1px solid #EAF0F4;
    }
    [data-testid="stChatMessage"][data-testid="chat-bubble-from-user"] {
        background-color: #E6F0FF; 
    }

    /* 7. 按钮 (保留) */
    [data-testid="stButton"] button {
        background-color: #0068C9; 
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }
    [data-testid="stButton"] button:hover {
        background-color: #00529E; 
        color: white;
    }
    [data-testid="stButton"] button:focus {
        box-shadow: 0 0 0 2px #C9E0FF; 
    }
    
    /* 8. Ticket 卡片 (保留) */
    .ticket-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        grid-gap: 1.25rem; 
        margin-top: 1rem;
    }
    .ticket-card {
        position: relative;
        padding: 20px 18px;
        border-radius: 12px;
        color: #333; 
        background-color: var(--ticket-bg-color, #FFFFFF);
        box-shadow: 0 3px 8px rgba(0,0,0,0.05);
        transition: all 0.25s ease-in-out;
        overflow: hidden;
        word-break: break-word;
        border: 1px solid #EAF0F4;
    }
    .ticket-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 5px 12px rgba(0,0,0,0.08);
    }
    .ticket-title {
        font-weight: 700;
        font-size: 18px;
        margin-bottom: 6px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: #1E293B;
    }
    .ticket-meta, .ticket-desc {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* 9. Ticket 状态标签 (保留) */
    .status-badge {
        position: absolute;
        top: 16px;
        right: 16px;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
        color: white;
        text-transform: uppercase;
    }
    .status-open { background-color: #0068C9; } 
    .status-inprogress { background-color: #FFA000; color: white; } 
    .status-closed { background-color: #28A745; } 
    </style>
    """,
    unsafe_allow_html=True
)
# =========================================================
# 💎 主题注入结束
# =========================================================

robot_logo_base64 = get_image_base64("assets/12.png") 

# -------------------------
# Session init (已移到顶部)
# -------------------------

# -------------------------
# Sidebar: login + upload
# -------------------------
st.sidebar.header("Account / Upload")
if st.session_state.current_user:
    u = st.session_state.current_user
    st.sidebar.markdown(f"**User:** {u['username']}  \n**Role:** {u['role']}")
    if st.sidebar.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()
    # 添加红色按钮样式
    st.sidebar.markdown("""
    <style>
        [data-testid="stButton"] button[type="primary"] {
            background-color: #FF4B4B; /* 红色 */
            color: white;
        }
        [data-testid="stButton"] button[type="primary"]:hover {
            background-color: #D94141; /* 深红色 */
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

else:
    # (这段代码理论上不会运行了，因为顶部有检查，但保留也无妨)
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

# 🧭 动态侧边栏导航栏（根据用户角色显示不同菜单）
st.sidebar.subheader("Navigation")

user = st.session_state.current_user

if user is None:
    # 未登录：只显示聊天
    nav_options = ["💬 Chat"]
elif user["role"] == "tenant":
    nav_options = [
        "💬 Chat",
        "🛠 Submit Ticket",
        "📋 My Tickets",
    ]
elif user["role"] == "landlord":
    nav_options = [
        "💬 Chat",
        "🏠 Landlord Panel",
    ]
else:
    nav_options = ["💬 Chat"]

page = st.sidebar.radio(
    label="Navigation menu",
    label_visibility="collapsed",
    options=nav_options,
    index=0,
)


# -------------------------
# Main: Chat (RAG + Ticket Intent)
# -------------------------
if page == "💬 Chat":
    u = st.session_state.current_user

    if u["role"] == "tenant" and u.get("tenant_house_id"):
        loaded, msg = house_kb.load_house_kb_into_rag(u["tenant_house_id"])
        if loaded:
            st.session_state.doc_uploaded = True  # 告诉系统“已经有知识库”
        else:
            st.warning(msg)
        docs = house_kb.get_house_docs(u["tenant_house_id"])
        if docs:
            st.info(f"🏠 Using knowledge base for house ID {u['tenant_house_id']}")
        else:
            st.warning("⚠️ This house has no knowledge base.")

    if robot_logo_base64:
        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <img src="data:image/png;base64,{robot_logo_base64}" style="height: 28px; margin-right: 10px; border-radius: 4px;"/>
                <h2 style="margin: 0;">Chat (RAG + Ticket Creation)</h2>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.header("Chat (RAG + Ticket Creation)") # 备用方案
    # =========================
    # 1️⃣ 判断是否有“至少一个可用知识库”
    # =========================

    # 用户自己是否上传过文档？
    has_user_doc = is_fitted()

    # 租客是否绑定了房屋？
    tenant_house_kb = False
    if u["role"] == "tenant" and u.get("tenant_house_id"):
        tenant_house_kb = house_kb.has_house_kb(u["tenant_house_id"])

    # 房东是否有自己的房屋知识库？
    landlord_kb = False
    if u["role"] == "landlord":
        houses = house_kb.list_houses(u["id"])
        landlord_kb = any(house_kb.has_house_kb(h["id"]) for h in houses)

    # 最终判断：是否至少存在一个可以用于回答的知识库？
    kb_available = has_user_doc or tenant_house_kb or landlord_kb

    if not kb_available:
        st.warning("⚠️ No knowledge base available yet. Please upload a document or ask your landlord to upload a house KB.")
        st.stop()
    else:
        # ✅ 展示聊天记录
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # ✅ 用户输入
        if prompt := st.chat_input("Ask about the contract or report a maintenance issue..."):
            with st.chat_message("user"):
                st.write(prompt)
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Step 1️⃣ — 意图识别（仅英文关键字）
            keywords = ["create ticket", "maintenance issue", "report problem", "repair request", "fix", "broken"]
            if any(k in prompt.lower() for k in keywords):
                st.session_state["ticket_draft"] = {
                    "title": "New Maintenance Request",
                    "description": prompt,
                    "priority": "Normal"
                }
                st.success("🧾 I detected that you want to create a maintenance ticket. Please fill in the details below 👇")
            else:
                # Step 2️⃣ — 正常问答
                with st.spinner("Retrieving and generating answer..."):
                    try:
                        answer = query_rag(prompt, top_k=3)
                    except Exception as e:
                        answer = f"Error during query: {e}"
                with st.chat_message("assistant"):
                    st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

        # Step 3️⃣ — 工单草稿表单（仅在检测到创建意图时出现）
        if "ticket_draft" in st.session_state:
            draft = st.session_state["ticket_draft"]

            if not st.session_state.current_user:
                st.warning("Please log in as a tenant to submit tickets.")
            elif not HAVE_TICKETS:
                st.error("Ticketing backend not available.")
            else:
                st.markdown("### ✍️ Ticket Draft")

                with st.form("ticket_draft_form"):
                    title = st.text_input("Title", draft["title"])
                    category = st.selectbox("Category", ["Plumbing", "Electrical", "Appliance", "Lock/Key", "Other"])
                    priority = st.selectbox("Priority", ["Low", "Normal", "High", "Urgent"], index=1)
                    description = st.text_area("Describe the issue", draft["description"], height=180)
                    att = st.file_uploader("Attach photo/doc (optional)", type=["png","jpg","jpeg","pdf","docx","doc"])
                    submitted = st.form_submit_button("✅ Submit Ticket")

                    if submitted:
                        if st.session_state.current_user["role"] != "tenant":
                            st.warning("Only tenants can create maintenance tickets.")
                        else:
                            att_bytes = att.read() if att else None
                            att_name = att.name if att else None

                            tid = ticket_mod.create_ticket(
                                title=title,
                                description=description,
                                category=category,
                                priority=priority,
                                creator=st.session_state.current_user["username"],
                                creator_role=st.session_state.current_user["role"],
                                attachment_file=att_bytes,
                                attachment_name=att_name
                            )
                            st.success(f"🎉 Ticket #{tid} created successfully!")
                            del st.session_state["ticket_draft"]
                            st.rerun()

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
                /* 【修改】: 颜色改为从 CSS 变量继承，以便动态设置 */
                color: #333; 
                background-color: var(--ticket-bg-color, #f0f0f0);
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
            
            /* 【修改】: 移除了 .priority-X 的背景色设置, 改为内联 style
            </style>
            """, unsafe_allow_html=True)

            # 🎛️ 网格布局开始
            st.markdown('<div class="ticket-grid">', unsafe_allow_html=True)

            # 定义优先级颜色
            PRIORITY_COLORS = {
                "Low": "#d1e7dd",     # 浅绿
                "Normal": "#cff4fc",  # 浅蓝
                "High": "#fff3cd",    # 浅黄
                "Urgent": "#f8d7da"   # 浅红
            }

            for r in rows:
                priority = r.get("priority", "Normal").capitalize()
                status = r.get("status", "open").lower().replace(" ", "")
                title = r.get("title", "Untitled")
                desc = r.get("description", "")
                category = r.get("category", "General")
                
                # 获取背景色
                bg_color = PRIORITY_COLORS.get(priority, "#f0f0f0") # 默认灰色

                # 【修改】: 使用内联 style 设置背景色
                st.markdown(f"""
                <div class="ticket-card" style="--ticket-bg-color: {bg_color};">
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
    user = st.session_state.current_user

    if not user or user["role"] != "landlord":
        st.warning("You must be a landlord to view this.")
        st.stop()

    landlord_id = user_mod.get_user_id_by_name(user["username"])

    # ============================================
    # 1️⃣ 显示房源 + House KB 管理
    # ============================================
    st.subheader("🏘 Your Houses")

    houses = house_kb.list_houses(landlord_id)

    with st.expander("➕ Add New House"):
        hname = st.text_input("House Name")
        haddr = st.text_input("Address")
        if st.button("Create House"):
            hid = house_kb.create_house(landlord_id, hname, haddr)
            st.success(f"House #{hid} created!")
            st.rerun()

    for h in houses:
        st.markdown(f"### 🏠 {h['house_name']} — {h['address']}")

        # ---- 显示现有 KB 文档 ----
        docs = house_kb.get_house_docs(h["id"])
        if docs:
            st.markdown("📚 Existing Knowledge Base:")
            for d in docs:
                st.markdown(f"- `{d['file_path']}`")
        else:
            st.info("No documents yet.")

        # ---- 文件上传器 ----
        up = st.file_uploader(
            f"Upload Knowledge File for {h['house_name']}",
            type=["pdf", "txt"],
            key=f"upload_{h['id']}"
        )

        # ---- 上传 ----
        if up and st.button(f"Add to KB ({h['house_name']})", key=f"btn_{h['id']}"):
            file_bytes = up.read()
            house_kb.upload_house_document(h["id"], file_bytes, up.name)
            st.success("📘 File uploaded and added to Knowledge Base!")
            st.session_state["refresh_kb"] = True
            st.rerun()

    # 刷新逻辑
    if st.session_state.get("refresh_kb"):
        del st.session_state["refresh_kb"]
        st.rerun()

    st.markdown("---")

    # ============================================
    # 2️⃣ Tenant Tickets 管理（工单管理）
    # ============================================
    st.subheader("🛠 Tenant Maintenance Tickets")

    # ---- 获取所有属于 landlord 的租客 ----
    conn = ticket_mod.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE landlord_id=?", (landlord_id,))
    tenant_names = [r["username"] for r in cur.fetchall()]
    conn.close()

    if not tenant_names:
        st.info("You have no tenants yet.")
        st.stop()

    placeholders = ",".join(["?"] * len(tenant_names))
    query = f"SELECT * FROM tickets WHERE creator IN ({placeholders}) ORDER BY created_at DESC"

    conn = ticket_mod.get_conn()
    cur = conn.cursor()
    cur.execute(query, tenant_names)
    tickets = [dict(r) for r in cur.fetchall()]
    conn.close()

    if not tickets:
        st.info("Your tenants have not submitted any tickets.")
        st.stop()

    # ---- 展示工单 ----
    for t in tickets:
        st.markdown(f"**#{t['id']} {t['title']}** — by {t['creator']} ({t['priority']})")
        st.markdown(t["description"])

        if t.get("attachment_path"):
            st.markdown(f"📎 Attachment: `{t['attachment_path']}`")

        if t.get("landlord_response"):
            st.info(f"Last response:\n{t['landlord_response']}")

        # ---- 回复工单表单 ----
        with st.form(f"resp_{t['id']}", clear_on_submit=True):
            resp = st.text_area("Response / Action Taken", key=f"resp_txt_{t['id']}")
            status_opts = ["open", "in_progress", "closed"]
            current_idx = status_opts.index(t["status"]) if t["status"] in status_opts else 0
            new_status = st.selectbox(
                "Set status",
                status_opts,
                index=current_idx,
                key=f"status_sel_{t['id']}"
            )
            if st.form_submit_button("Submit Response"):
                ticket_mod.update_ticket_response(
                    t["id"],
                    landlord_response=resp,
                    new_status=new_status
                )
                st.success("Response saved!")
                st.rerun()
