from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import get_settings

# asyncpg rejects these psycopg2/libpq-style query params outright.
# SSL mode is handled separately via connect_args; channel_binding has no
# asyncpg equivalent and can be dropped safely for Neon connections.
_STRIP_PARAMS = {"sslmode", "channel_binding"}


def _build_async_url(url: str) -> str:
    """
    Convert a postgres:// URL to the asyncpg dialect and remove any query
    parameters that asyncpg doesn't understand.

    Regex-based stripping breaks when the removed param is first in the query
    string — the leftover & makes the next param look like part of the db name.
    urlparse handles this correctly regardless of param order.
    """
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    params = {k: v[0] for k, v in parse_qs(parsed.query).items() if k not in _STRIP_PARAMS}
    return urlunparse(parsed._replace(query=urlencode(params)))


def _get_ssl_args(url: str) -> dict:
    """
    Return asyncpg connect_args for SSL when the original URL requests it.

    ssl=True uses Python's default CA store, which fails on macOS because the
    python.org installer doesn't link to the system keychain.  We build an
    explicit SSLContext from certifi's Mozilla CA bundle so it works everywhere.
    """
    parsed = urlparse(url)
    sslmode = parse_qs(parsed.query).get("sslmode", [None])[0]
    if sslmode in ("require", "verify-ca", "verify-full"):
        import ssl
        import certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        return {"ssl": ctx}
    return {}


settings = get_settings()

# NullPool is required for Vercel serverless — each invocation gets its own
# connection rather than borrowing from a shared pool that won't persist.
engine = create_async_engine(
    _build_async_url(settings.database_url),
    connect_args=_get_ssl_args(settings.database_url),
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
