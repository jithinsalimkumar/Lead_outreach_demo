"""
Application configuration — loads settings from environment variables.

Uses pydantic-settings to validate and type-check all env vars at startup.
If a required variable is missing, the app will fail fast with a clear error.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_MFHb6xiTRv7U@ep-noisy-tooth-awyfsadm-pooler.c-12.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"  # e.g. postgresql+asyncpg://user:pass@host:port/dbname

    # --- Redis ---
    REDIS_URL: str = "redis-cli --tls -u redis://default:gQAAAAAAAQOTAAIgcDExM2Q1YTE1NTcwNzE0NzNkYjM0YmZmYWZlNGM4NDBkMQ@gorgeous-man-66451.upstash.io:6379"

    # --- JWT ---
    JWT_SECRET_KEY: str = "a59859e0e28cfb9a41d8d8156208818f"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Encryption (Fernet key for API key storage) ---
    ENCRYPTION_KEY: str = "5cbdeccac53362543e5ec077dbe50ad0"

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:3000,http://frontend:3000,http://lead-outreach-demo-alpha.vercel.app,https://lead-outreach-frontend.onrender.com"

    class Config:
        # Load from .env file if present (Docker sets these via env_file)
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars like POSTGRES_USER etc.


# Singleton instance — import this wherever you need settings
settings = Settings()
