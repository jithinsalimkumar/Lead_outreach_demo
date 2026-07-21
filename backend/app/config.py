"""
Application configuration — loads settings from environment variables.

Uses pydantic-settings to validate and type-check all env vars at startup.
If a required variable is missing, the app will fail fast with a clear error.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str  # e.g. postgresql+asyncpg://user:pass@host:port/dbname

    # --- Redis ---
    REDIS_URL: str = "redis://redis:6379/0"

    # --- JWT ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Encryption (Fernet key for API key storage) ---
    ENCRYPTION_KEY: str = ""

    class Config:
        # Load from .env file if present (Docker sets these via env_file)
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars like POSTGRES_USER etc.


# Singleton instance — import this wherever you need settings
settings = Settings()
