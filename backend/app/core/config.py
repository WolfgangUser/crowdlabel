"""
Конфигурация приложения через переменные окружения.
12-factor App: Factor III — Config stored in the environment.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_NAME: str = "CrowdLabel"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database (Factor IV — Backing services)
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@host/db

    # Redis (Factor IV)
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # First admin
    FIRST_ADMIN_EMAIL: str = "admin@crowdlabel.io"
    FIRST_ADMIN_PASSWORD: str = "Admin123!"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
