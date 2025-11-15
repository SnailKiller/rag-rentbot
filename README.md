# RentBot — Intelligent Rental Assistant

### Contract Q&A • Automatic Ticketing • Multi-Tenant House Knowledge Base • RAG Pipeline

---

## 📌 Overview

**RentBot** is an intelligent rental assistant combining:

* **RAG-based contract question answering**
* **Automatic maintenance ticket creation from chat**
* **Multi-house knowledge bases for landlords**
* **Tenant–Landlord binding**
* **Full login & registration system (with password hashing)**
* **Streamlit frontend + SQLite backend**

This system supports real-world rental workflows while remaining lightweight, explainable, and easy to deploy.

---

## ✨ Features

### 🔍 **1. RAG-based Contract Q&A**

* Supports both **tenant-uploaded contracts** and **landlord-provided house knowledge bases**.
* Includes **query rewriting** to improve retrieval quality.
* Automatically loads the **tenant's house KB** on login → No need to reupload each time.

### 🛠 **2. Automatic Ticket Creation from Chat**

RentBot detects maintenance-related intent such as:

> “The aircon is not cooling, please help.”

→ It auto-creates a **ticket draft**, which the tenant edits and submits.

### 📋 **3. Tenant Maintenance Tickets**

* Tenants submit tickets with:
  ✔ title
  ✔ category
  ✔ priority
  ✔ description
  ✔ image/PDF attachments
* Tickets saved to SQLite database.

### 🏠 **4. Landlord Panel**

Landlords can:

* Manage **multiple houses**
* Upload house-level KB documents (PDF/TXT)
* View **tickets only from their own tenants**
* Respond to tickets and change status (open / in_progress / closed)

### 🔐 **5. Login System**

* Users can register as **tenant** or **landlord**.
* Tenants must select:

  * Landlord username
  * The specific house they rent

Passwords are stored using **SHA-256 hashing**.

---

## 🗂️ Project Structure

```
rag-rentbot/
├── app.py                 # Streamlit UI
├── backend/
│   ├── rag_pipeline.py    # Core RAG (TF-IDF or OpenAI embedding)
│   ├── house_kb.py        # Multi-house knowledge base
│   ├── tickets.py         # Ticket CRUD operations
│   ├── users.py           # Login + registration + hashing
│   ├── db.py              # Database init
│   └── ticket_module.py
├── assets/
│   ├── rentbot_logo.png
├── data/
│   ├── rentbot.db         # SQLite database
│   └── house_docs/
└── requirements.txt
```

---

## 🧠 RAG Architecture

RentBot uses a hybrid RAG pipeline:

1. **Query Rewrite (semantic enrichment + disambiguation)**
2. **Document Chunking**
3. **TF-IDF Vectorization / Embedding**
4. **Top-K Context Retrieval**
5. **LLM Answer Generation with Context Window**

Advantages:

* Handles ambiguous user queries
* Adapts to document style and terminology
* Supports multi-source knowledge (contract + house KB)

---

## 🚀 Demo Workflow

### 🟦 Landlord

1. Login as landlord
2. Create a house (e.g., *“Maple Residence 3F”*)
3. Upload house KB PDF
4. The tenant linked to this house can now query the KB

### 🟩 Tenant

1. Register as tenant
2. Select landlord & house from dropdown
3. Chat → “Who should I contact for emergency repair?”
   ✔ Receives answer from house KB
4. Ask: “My air conditioner is leaking”
   ✔ Auto ticket draft is generated
   ✔ Submit ticket

### 🟧 Landlord Ticket Management

* Visit *Landlord Panel*
* See only tickets submitted by their own tenants
* Respond & update status

---

## 🛠 Installation

```bash
git clone https://github.com/<yourname>/rag-rentbot.git
cd rag-rentbot
pip install -r requirements.txt
streamlit run app.py
```

---

## 🔑 Secrets Setup

Create `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY="your-key"
```
