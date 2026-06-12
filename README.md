# 🤖 Company Internal Chatbot with RBAC

A secure internal chatbot system with Role-Based Access Control (RBAC) using RAG (Retrieval-Augmented Generation).

## 🏗️ Architecture

- **Frontend:** Streamlit
- **Backend:** FastAPI + JWT Authentication
- **Vector DB:** ChromaDB
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)
- **LLM:** Groq (llama-3.1-8b-instant)
- **Database:** SQLite
- **Auth:** JWT Tokens

## 👥 User Roles & Access

| Role | Access |
|------|--------|
| Finance | Financial reports + General handbook |
| HR | HR data + General handbook |
| Marketing | Marketing reports + General handbook |
| Engineering | Technical docs + General handbook |
| Employee | General handbook only |
| C-Level | All documents |

## 🚀 Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/sanjayy2004/tbac-chatbot.git
cd tbac-chatbot
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create .env file
```bash
cp .env.example .env
```
Fill in your API keys in `.env`

### 5. Clone data repository
```bash
git clone https://github.com/springboardmentor441p-coderr/Fintech-data data/raw
```

### 6. Preprocess documents
```bash
python backend/preprocessor.py
```

### 7. Build vector store
```bash
python backend/vector_store.py
```

### 8. Start backend
```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8080
```

### 9. Start frontend
```bash
streamlit run frontend/app.py
```

## 🧪 Demo Accounts

| Username | Password | Role |
|----------|----------|------|
| alice | finance123 | Finance |
| bob | hr123 | HR |
| carol | mkt123 | Marketing |
| dave | eng123 | Engineering |
| eve | emp123 | Employee |
| frank | ceo123 | C-Level |

## 🧪 Run Tests
```bash
python -m tests.test_system
```

## 📁 Project Structure
```
rbac-chatbot/
├── backend/
│   ├── main.py          # FastAPI app
│   ├── auth.py          # JWT authentication
│   ├── rbac.py          # Role-based access control
│   ├── rag.py           # RAG pipeline
│   ├── vector_store.py  # ChromaDB vector store
│   ├── preprocessor.py  # Document preprocessing
│   └── database.py      # SQLite database
├── frontend/
│   └── app.py           # Streamlit UI
├── data/
│   ├── raw/             # Raw documents
│   └── processed_chunks.json
├── tests/
│   └── test_system.py   #