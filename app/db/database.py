# app/db/database.py
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declared_attr, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool
from typing import Generator, Dict, Any, Optional
import os
from enum import Enum


class DatabaseType(Enum):
    SQLITE = "sqlite"
    POSTGRES = "postgresql"


class DatabaseSettings(ABC):
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DB_DIR = os.path.join(self.BASE_DIR, "database")
        os.makedirs(self.DB_DIR, exist_ok=True)
        self.ECHO_SQL = os.getenv("ECHO_SQL", "True").lower() == "true"

    @property
    @abstractmethod
    def DATABASE_URL(self) -> str:
        """Database connection URL"""
        pass

    @property
    @abstractmethod
    def engine_settings(self) -> Dict[str, Any]:
        """Database-specific engine settings"""
        pass


class SQLiteSettings(DatabaseSettings):
    def __init__(self):
        super().__init__()
        self._db_file = os.path.join(self.DB_DIR, "app.db")

    @property
    def DATABASE_URL(self) -> str:
        return f"sqlite:///{self._db_file}"

    @property
    def engine_settings(self) -> Dict[str, Any]:
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
            "echo": self.ECHO_SQL,
        }


class PostgresSettings(DatabaseSettings):
    def __init__(self):
        super().__init__()
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "postgres")
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.database = os.getenv("POSTGRES_DB", "fastapi_db")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def engine_settings(self) -> Dict[str, Any]:
        return {
            "poolclass": QueuePool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "echo": self.ECHO_SQL,
        }


class DatabaseFactory:
    _instance: Optional["DatabaseFactory"] = None
    _settings: Optional[DatabaseSettings] = None
    _engine = None
    _session_maker = None

    def __init__(self):
        # Initialize settings based on environment
        db_type = os.getenv("DB_TYPE", "sqlite").lower()
        self._settings = SQLiteSettings() if db_type == "sqlite" else PostgresSettings()

    @classmethod
    def get_instance(cls) -> "DatabaseFactory":
        """Get or create database factory instance"""
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(
                self._settings.DATABASE_URL, **self._settings.engine_settings
            )
        return self._engine

    @property
    def session_maker(self):
        if self._session_maker is None:
            self._session_maker = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
        return self._session_maker

    def get_db(self) -> Generator:
        session = self.session_maker()
        try:
            yield session
        finally:
            session.close()


# Base class for models
class CustomBase:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


Base = declarative_base(cls=CustomBase)


# Database dependency
def get_db() -> Generator:
    return DatabaseFactory.get_instance().get_db()


def verify_database() -> bool:
    """Verify database connection"""
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False


# Initialize tables
def init_database():
    """Initialize database and create tables"""
    factory = DatabaseFactory.get_instance()
    Base.metadata.create_all(bind=factory.engine)
