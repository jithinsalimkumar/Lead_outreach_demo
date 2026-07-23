"""
Async SQLAlchemy 2.0 database setup.

Creates the async engine and session factory. The `get_db` dependency
yields a session per request and ensures cleanup.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

import urllib.parse


def sanitize_asyncpg_url(url: str) -> str:
    """
    Normalizes database connection strings for asyncpg:
    1. Converts postgres:// or postgresql:// to postgresql+asyncpg://
    2. Converts sslmode parameter to ssl
    3. Strips unsupported libpq parameters (e.g. channel_binding, gssencmode, target_session_attrs)
    """
    if not url:
        return url

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parts = urllib.parse.urlsplit(url)
    query_params = urllib.parse.parse_qs(parts.query, keep_blank_values=True)

    if "sslmode" in query_params and "ssl" not in query_params:
        mode = query_params["sslmode"][0].lower()
        if mode in ("require", "verify-ca", "verify-full", "prefer"):
            query_params["ssl"] = ["require"]
        elif mode in ("disable", "allow"):
            query_params["ssl"] = [mode]

    ALLOWED_ASYNCPG_PARAMS = {
        "ssl",
        "timeout",
        "connect_timeout",
        "command_timeout",
        "statement_cache_size",
        "max_cached_statement_lifetime",
        "max_cacheable_statement_size",
        "server_settings",
        "options",
        "direct_connection",
    }

    filtered_params = {
        k: v for k, v in query_params.items() if k.lower() in ALLOWED_ASYNCPG_PARAMS
    }
    new_query = urllib.parse.urlencode(filtered_params, doseq=True)
    return urllib.parse.urlunsplit(parts._replace(query=new_query))


database_url = sanitize_asyncpg_url(settings.DATABASE_URL)

# Create the async engine — echo=False in production, True for debugging SQL
engine = create_async_engine(
    database_url,
    echo=False,
    pool_size=20,         # Max persistent connections
    max_overflow=10,      # Extra connections allowed beyond pool_size
    pool_pre_ping=True,   # Verify connections are alive before using them
)

# Session factory — each call creates a new async session
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit (avoids lazy-load issues)
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    All models inherit from this so Alembic can auto-detect them.
    """
    pass


async def get_db():
    """
    FastAPI dependency that provides a database session.
    Usage: db: AsyncSession = Depends(get_db)

    The session is automatically closed when the request finishes,
    even if an error occurs.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
