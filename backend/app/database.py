"""
Async SQLAlchemy 2.0 database setup.

Creates the async engine and session factory. The `get_db` dependency
yields a session per request and ensures cleanup.
"""

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# Ensure protocol uses asyncpg driver (Render defaults to postgres:// or postgresql://)
database_url = settings.DATABASE_URL
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Strip ?sslmode=... from the URL — asyncpg does not accept it as a query param.
# SSL is configured via connect_args below instead.
parsed = urlparse(database_url)
query_params = parse_qs(parsed.query)
ssl_mode = query_params.pop("sslmode", [None])[0]
cleaned_query = urlencode(query_params, doseq=True)
database_url = urlunparse(parsed._replace(query=cleaned_query))

# Build connect_args: pass SSL to asyncpg the way it expects
connect_args = {}
if ssl_mode:
    connect_args["ssl"] = ssl_mode  # e.g. "require"

# Create the async engine — echo=False in production, True for debugging SQL
engine = create_async_engine(
    database_url,
    echo=False,
    pool_size=20,         # Max persistent connections
    max_overflow=10,      # Extra connections allowed beyond pool_size
    pool_pre_ping=True,   # Verify connections are alive before using them
    connect_args=connect_args,
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
