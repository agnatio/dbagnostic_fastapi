# app/db/session.py
from typing import Generator
from sqlalchemy.orm import Session
from app.db.database import DatabaseFactory, verify_database


# Re-export the get_db function from database.py
def get_db() -> Generator[Session, None, None]:
    yield from DatabaseFactory.get_instance().get_db()


# Re-export verify_database function
__all__ = ["get_db", "verify_database"]
