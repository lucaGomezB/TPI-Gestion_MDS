"""Tests for core.database — async engine and session factory."""

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.database import close_db, get_engine, get_session, init_db
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession


class TestDatabaseEngine:
    """Engine creation and lifecycle."""

    def test_get_engine_returns_async_engine(self):
        """get_engine should return an AsyncEngine instance."""
        engine = get_engine()
        assert isinstance(engine, AsyncEngine)

    def test_init_db_does_not_raise(self):
        """init_db() should run without error (creates the engine)."""
        init_db()
        engine = get_engine()
        assert isinstance(engine, AsyncEngine)

    @pytest.mark.asyncio
    async def test_close_db_does_not_raise(self):
        """close_db() should run without error (disposes the engine)."""
        init_db()
        await close_db()

    def test_get_session_is_async_generator(self):
        """get_session() should return an async generator yielding AsyncSession."""
        gen = get_session()
        assert inspect.isasyncgen(gen)

    @pytest.mark.asyncio
    async def test_get_session_yields_async_session(self):
        """Iterating get_session() should yield an AsyncSession (uses mock)."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.__aenter__.return_value = mock_session
        mock_session.close = AsyncMock()

        mock_maker = MagicMock()
        mock_maker.return_value = mock_session

        with patch("app.core.database.get_session_maker", return_value=mock_maker):
            gen = get_session()
            async for session in gen:
                assert isinstance(session, AsyncSession)
                break
            await gen.aclose()  # clean up the generator

    def test_engine_uses_postgresql_driver(self):
        """Engine URL should use the asyncpg driver (from default settings)."""
        engine = get_engine()
        url = str(engine.url)
        assert "postgresql" in url
        assert "asyncpg" in url
