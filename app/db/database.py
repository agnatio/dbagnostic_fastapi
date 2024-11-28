# app/db/database.py
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declared_attr, declarative_base
from sqlalchemy.pool import StaticPool, QueuePool
from typing import Generator, Dict, Any, Optional
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# from app.db.models.models_user import User


class DatabaseSettings(ABC):
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DB_DIR = os.path.join(self.BASE_DIR, "database")
        self.ECHO_SQL = os.getenv("ECHO_SQL", "True").lower() == "true"

    @property
    @abstractmethod
    def DATABASE_URL(self) -> str:
        pass

    @property
    @abstractmethod
    def engine_settings(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_database_if_not_exists(self):
        pass


class SQLiteSettings(DatabaseSettings):
    def __init__(self):
        super().__init__()
        os.makedirs(self.DB_DIR, exist_ok=True)
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

    def create_database_if_not_exists(self):
        # SQLite creates database automatically
        pass


class PostgresSettings(DatabaseSettings):
    def __init__(self):
        super().__init__()
        self.host = os.getenv("POSTGRES_HOST", "49.12.220.213")
        self.port = os.getenv("POSTGRES_PORT", "5432")
        self.user = os.getenv("POSTGRES_USER", "postgres")
        self.password = os.getenv("POSTGRES_PASSWORD", "fido&espero&amo")
        self.database = os.getenv("POSTGRES_DB", "nt_p1")
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

    def create_database_if_not_exists(self):
        """Create PostgreSQL database if it doesn't exist"""
        # Connection string to connect to PostgreSQL server (not specific database)
        conn_string = (
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/postgres"
        )

        try:
            # Connect to default database
            conn = psycopg2.connect(conn_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()

            # Check if database exists
            cursor.execute(
                f"SELECT 1 FROM pg_database WHERE datname = '{self.database}'"
            )
            exists = cursor.fetchone()

            if not exists:
                print(f"Creating database {self.database}")
                cursor.execute(f"CREATE DATABASE {self.database}")
                print(f"Database {self.database} created successfully")
            else:
                print(f"Database {self.database} already exists")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"Error creating database: {str(e)}")
            raise


class DatabaseFactory:
    _instance: Optional["DatabaseFactory"] = None
    _settings: Optional[DatabaseSettings] = None
    _engine = None
    _session_maker = None

    def __init__(self):
        print("Initializing DatabaseFactory")
        # Import settings here to avoid circular import
        from app.config import settings

        # Use settings instead of os.getenv
        db_type = settings.DB_TYPE.lower()
        print(f"Selected database type: {db_type}")

        self._settings = SQLiteSettings() if db_type == "sqlite" else PostgresSettings()
        print(f"Using settings class: {type(self._settings).__name__}")
        print(f"Database URL: {self._settings.DATABASE_URL}")

        # Create database if it doesn't exist
        self._settings.create_database_if_not_exists()

    @classmethod
    def get_instance(cls) -> "DatabaseFactory":
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    @property
    def engine(self):
        if self._engine is None:
            print("Creating new database engine...")
            self._engine = create_engine(
                self._settings.DATABASE_URL, **self._settings.engine_settings
            )
            print(f"Engine created successfully: {self._engine}")
        return self._engine

    @property
    def session_maker(self):
        if self._session_maker is None:
            print("Creating new session maker...")
            self._session_maker = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            print("Session maker created successfully")
        return self._session_maker

    def get_db(self) -> Generator:
        session = self.session_maker()
        try:
            yield session
        finally:
            session.close()


class CustomBase:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


Base = declarative_base(cls=CustomBase)


def get_db() -> Generator:
    return DatabaseFactory.get_instance().get_db()


def verify_database() -> bool:
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False


def init_database():
    """Initialize database and create tables"""
    print("=== Starting Database Initialization ===")
    factory = DatabaseFactory.get_instance()

    # Print all available metadata tables before creation
    print("Available tables in metadata:")
    for table in Base.metadata.sorted_tables:
        print(f"- {table.name}")

    # Check if User model is properly registered
    print("\nChecking User model registration...")
    try:
        from app.db.models.models_user import User

        print(f"User model table name: {User.__table__.name}")
        print(f"User model columns: {[c.name for c in User.__table__.columns]}")
    except Exception as e:
        print(f"Error importing User model: {str(e)}")

    print("\nAttempting to create tables...")
    Base.metadata.create_all(bind=factory.engine)

    # Verify tables after creation
    inspector = inspect(factory.engine)
    actual_tables = inspector.get_table_names()
    print(f"\nActual tables in database after creation: {actual_tables}")
