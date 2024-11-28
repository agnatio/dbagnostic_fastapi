from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declared_attr, declarative_base
from sqlalchemy.pool import StaticPool
from typing import Generator
import os


class DatabaseSettings:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.DB_DIR = os.path.join(self.BASE_DIR, "database")
        os.makedirs(self.DB_DIR, exist_ok=True)
        self.DATABASE_URL = f"sqlite:///{os.path.join(self.DB_DIR, 'app.db')}"
        self.ECHO_SQL = True

    @property
    def engine_settings(self):
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
            "echo": self.ECHO_SQL,
        }


class DatabaseFactory:
    _instance = None
    _engine = None
    _session_maker = None

    @classmethod
    def get_instance(cls) -> "DatabaseFactory":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.settings = DatabaseSettings()

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(
                self.settings.DATABASE_URL, **self.settings.engine_settings
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
