from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import jwt
import os
from dotenv import load_dotenv
from backend.rag import rag_pipeline
from backend.database import create_tables, get_db, User
from backend.auth import (
    authenticate_user, create_access_token,
    decode_token, hash_password, log_action
)
from backend.rbac import (
    get_role_info, get_accessible_departments,
    preprocess_query, filter_results_by_role
)


load_dotenv()

# ── App setup ──────────────────────────────────────────────────
app = FastAPI(
    title="RBAC Chatbot API",
    description="Company Internal Chatbot with Role-Based Access Control",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# ── Create tables and seed users on startup ────────────────────
@app.on_event("startup")
def startup():
    create_tables()
    seed_users()

def seed_users():
    from backend.database import SessionLocal
    db = SessionLocal()
    sample_users = [
        {"username": "alice", "name": "Alice Finance", "password": "finance123", "role": "finance"},
        {"username": "bob", "name": "Bob HR", "password": "hr123", "role": "hr"},
        {"username": "carol", "name": "Carol Marketing", "password": "mkt123", "role": "marketing"},
        {"username": "dave", "name": "Dave Engineering", "password": "eng123", "role": "engineering"},
        {"username": "eve", "name": "Eve Employee", "password": "emp123", "role": "employee"},
        {"username": "frank", "name": "Frank CEO", "password": "ceo123", "role": "c_level"},
    ]
    for u in sample_users:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if not existing:
            user = User(
                username=u["username"],
                name=u["name"],
                hashed_password=hash_password(u["password"]),
                role=u["role"]
            )
            db.add(user)
    db.commit()
    db.close()
    print("✅ Sample users seeded!")

# ── Get current user from token ────────────────────────────────
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ── Pydantic models ────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    sources: list
    role: str
    query: str

# ── Routes ─────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "RBAC Chatbot API is running!"}

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        log_action(db, form_data.username, "unknown", "LOGIN", "auth", success=False)
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    token = create_access_token({"sub": user.username, "role": user.role})
    log_action(db, user.username, user.role, "LOGIN", "auth", success=True)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "name": user.name,
        "username": user.username
    }

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    role_info = get_role_info(current_user.role)
    return {
        "username": current_user.username,
        "name": current_user.name,
        "role": current_user.role,
        "role_display": role_info["display"],
        "accessible_departments": get_accessible_departments(current_user.role)
    }

@app.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Run RAG pipeline
    result = rag_pipeline(request.query, current_user.role)

    # Log action
    log_action(db, current_user.username, current_user.role, "CHAT", result["query"])

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        role=current_user.role,
        query=result["query"]
    )

@app.get("/health")
def health():
    return {"status": "healthy"}