"""
Alembic migration environment — configured for async SQLAlchemy (asyncpg).

Run migrations:
    alembic upgrade head

Create a new migration:
    alembic revision --autogenerate -m "description"
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# Import all models so Alembic can detect schema changes via autogenerate
from app.database import Base, _build_async_url, _get_ssl_args
from app.models import *  # noqa: F401, F403 — registers all mapped classes

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_raw_url() -> str:
    import os
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        from app.config import get_settings
        url = get_settings().database_url
    return url


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (outputs SQL)."""
    context.configure(
        url=_build_async_url(_get_raw_url()),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against a live DB using an async engine."""
    raw_url = _get_raw_url()
    engine = create_async_engine(
        _build_async_url(raw_url),
        connect_args=_get_ssl_args(raw_url),
    )
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
