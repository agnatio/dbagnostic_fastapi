# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


print(f"Current working directory: {os.getcwd()}")
print(f".env file exists: {os.path.exists('.env')}")
print(f"Full path to .env: {os.path.abspath('.env')}")


class Settings(BaseSettings):
    # Application settings
    # DB_TYPE: str = "sqlite"

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        print("=== Settings Initialization ===")
        print(f"Loading from .env file")
        print(f"DB_TYPE setting: {self.DB_TYPE}")
        print("============================")

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Create settings instance
settings = get_settings()
