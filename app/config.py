# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os
from app.db.database import DatabaseFactory


class Settings(BaseSettings):
    # Application settings
    PROJECT_NAME: str = "FastAPI Auth System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:8080"]

    # Database settings are accessed through DatabaseFactory
    _db_factory: DatabaseFactory = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._db_factory = DatabaseFactory.get_instance()

    @property
    def db(self) -> DatabaseFactory:
        return self._db_factory

    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Create settings instance
settings = get_settings()
