# db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
# Create the database directory if it doesn't exist
db_dir = os.path.join(current_dir, "..", "database")
os.makedirs(db_dir, exist_ok=True)
# Database URL
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(db_dir, 'app.db')}"

# Create engine with some useful settings for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite
    poolclass=StaticPool,  # Good for development with SQLite
    echo=True,  # SQL logging, set to False in production
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
