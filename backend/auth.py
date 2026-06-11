from datetime import datetime, timedelta
from typing import Optional
import jwt
import hashlib
import hmac
from sqlalchemy.orm import Session
from backend.database import User, AuditLog
import os
from dotenv import load_dotenv
import uuid

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# ── Password hashing (using sha256 for compatibility) ──────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

# ── JWT token ──────────────────────────────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ── User authentication ────────────────────────────────────────
def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username.lower()).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

# ── Audit logging ──────────────────────────────────────────────
def log_action(db: Session, username: str, role: str, action: str, resource: str, success: bool = True):
    log = AuditLog(
        id=str(uuid.uuid4()),
        username=username,
        role=role,
        action=action,
        resource=resource,
        timestamp=datetime.utcnow(),
        success=success
    )
    db.add(log)
    db.commit()