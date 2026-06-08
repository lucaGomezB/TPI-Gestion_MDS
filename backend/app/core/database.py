"""Async database engine and session factory.

Uses DATABASE_URL from settings to create a SQLAlchemy async engine
and provides ``get_session()`` for FastAPI dependency injection.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the singleton async engine, creating it if necessary."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            str(settings.database_url),
            echo=settings.debug,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Return the singleton async sessionmaker, creating it if necessary."""
    global _session_maker  # noqa: PLW0603
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
        )
    return _session_maker


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Async generator yielding a database session.

    Intended for use as a FastAPI dependency:
    ``async def get_db_session(session: AsyncSession = Depends(get_session))``.
    """
    maker = get_session_maker()
    async with maker() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db() -> None:
    """Initialize the database engine (lazy — engine is created but not connected)."""
    get_engine()


async def close_db() -> None:
    """Dispose the database engine and release all connections."""
    global _engine, _session_maker  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_maker = None
