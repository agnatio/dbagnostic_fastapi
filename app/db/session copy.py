# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import os
from app.db.config import settings

# Create engine with some useful settings for SQLite
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    poolclass=StaticPool,  # Good for development with SQLite
    echo=settings.DEBUG,  # SQL logging based on debug mode
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints that need database access.
    Creates a new database session for each request and closes it afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_database():
    """Verify database connection and create tables if they don't exist."""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False
