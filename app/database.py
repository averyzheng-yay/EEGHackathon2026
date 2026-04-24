from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings


def _build_async_url(url: str) -> str:
    """Convert a standard postgres:// URL to the asyncpg dialect."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


settings = get_settings()

# NullPool is required for Vercel serverless — each invocation gets its own
# connection rather than borrowing from a shared pool that won't persist.
engine = create_async_engine(
    _build_async_url(settings.database_url),
    poolclass=NullPool,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency: yields a database session and ensures it closes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
