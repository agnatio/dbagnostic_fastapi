# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'app.db')}"

    # JWT
    SECRET_KEY: str = "your-secret-key-here"  # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Application
    PROJECT_NAME: str = "FastAPI Auth System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # CORS
    BACKEND_CORS_ORIGINS: list = ["http://localhost:8080"]

    class Config:
        case_sensitive = True
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
