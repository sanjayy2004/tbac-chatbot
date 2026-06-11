from sqlalchemy import create_engine, Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/users.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ── User model ─────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    role = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ── Audit log model ────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    username = Column(String)
    role = Column(String)
    action = Column(String)
    resource = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=True)

# ── Create tables ──────────────────────────────────────────────
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")

# ── Get DB session ─────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()