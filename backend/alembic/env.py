"""
Alembic env.py — configures the migration environment.

This file is executed every time you run an alembic command.
It connects to the database and tells Alembic about our models
so it can auto-generate migrations.
"""

import asyncio
from logging.config import fileConfig
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import our models so Alembic can see all tables
# This import triggers app.models.__init__.py which imports every model
from app.database import Base
from app.models import *  # noqa: F401, F403
from app.config import settings

# Alembic Config object — provides access to alembic.ini values
config = context.config

# Set up Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Tell Alembic which metadata to compare against (our Base.metadata has all tables)
target_metadata = Base.metadata

# Override the sqlalchemy.url from alembic.ini with our actual database URL.
# Strip ?sslmode=... — asyncpg does not accept it as a URL query param.
alembic_db_url = settings.DATABASE_URL
parsed = urlparse(alembic_db_url)
query_params = parse_qs(parsed.query)
ssl_mode = query_params.pop("sslmode", [None])[0]
cleaned_query = urlencode(query_params, doseq=True)
alembic_db_url = urlunparse(parsed._replace(query=cleaned_query))

# Build connect_args for SSL if needed
alembic_connect_args = {}
if ssl_mode:
    alembic_connect_args["ssl"] = ssl_mode  # e.g. "require"

config.set_main_option("sqlalchemy.url", alembic_db_url)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode — generates SQL without connecting to DB.
    Useful for generating migration scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Helper that runs migrations within a connection context."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with an async engine.
    We create an async engine, get a sync connection from it,
    and run migrations through that connection.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=alembic_connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations — delegates to async runner."""
    asyncio.run(run_async_migrations())


# Choose offline or online mode based on how Alembic was invoked
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

