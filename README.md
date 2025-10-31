# 🏠 RentBot — Intelligent Rental Document & Ticketing Assistant

### 🤖 A Streamlit-based RAG system for document understanding and rental workflow management.

---

## 🌟 Overview
**RentBot** is an intelligent assistant designed to simplify rental document management and communication between tenants and landlords.

It supports:
- Contract understanding via **RAG-based question answering**  
- File parsing and indexing (PDF/TXT)  
- Tenant–landlord interaction through a **ticket management system**  
- Multi-role login (Tenant / Landlord)  
- Real-time Q&A powered by OpenAI API  

---

## 🚀 Features
| Module | Description |
|---------|--------------|
| 🧠 **RAG Q&A System** | Upload a tenancy agreement and ask natural language questions about it. |
| 🗂️ **File Parsing** | Extract and chunk text using PyMuPDF and LangChain splitters. |
| 💬 **Chat Interface** | Interactive Streamlit chat with conversation memory. |
| 🧾 **Ticket System** | Tenants can submit maintenance requests, landlords can respond. |
| 👥 **User Management** | Separate login flows for tenants and landlords. |
| 📊 **Validation Framework** | Evaluate retrieval accuracy using ROUGE-L, EM, and Semantic Similarity metrics. |

---

## 🧩 System Architecture
```

Frontend (Streamlit)
├── File Upload
├── Chat Interface
├── Ticket Management
Backend (Python)
├── RAG Pipeline (TF-IDF / OpenAI Embedding)
├── Storage & Retrieval
├── User & Ticket Logic
Validation (Colab / Local)
├── ROUGE-L, EM, SemanticSim evaluation

```

---

## ⚙️ Installation

### 1️⃣ Clone the repository
```bash
git clone https://github.com/<your-username>/rentbot.git
cd rentbot
```

### 2️⃣ Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set your OpenAI API key

Create a file `.streamlit/secrets.toml`:

```toml
OPENAI_API_KEY = "your_api_key_here"
```

Alternatively, export it in your shell:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

---

## 🧠 Run the App

```bash
streamlit run app.py
```

Then visit [http://localhost:8501](http://localhost:8501)

---

## 🧪 Validation

We designed a 20-question evaluation to assess:

* **ROUGE-L** — textual overlap accuracy
* **Exact Match (EM)** — factual correctness
* **Semantic Similarity** — meaning-level alignment

Example output:

| Metric      | Mean Score |
| ----------- | ---------- |
| ROUGE-L     | 0.255      |
| EM          | 0.15       |
| SemanticSim | 0.565      |
| Final Score | 0.317      |

📊 See: [`rag_validation_report.xlsx`](./validation/rag_validation_report.xlsx)

---

## 🧱 Folder Structure

```
backend/
 ├── rag_pipeline.py
 ├── embeddings.py
 ├── tickets.py
 ├── user_module.py
 ├── document_parser.py
 ├── main.py
 ├── vectorstore.py
 └── db.py
app.py
requirements.txt
README.md
validate_rag.py
```

---

## 🪪 License

MIT License © 2025 RentBot Team


