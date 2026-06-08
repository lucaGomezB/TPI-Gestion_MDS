"""Tests for BaseRepository[T] — generic CRUD with tenant scoping."""

import re
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.base import AppModel
from app.models.mixins import EstadoRegistro
from app.models.usuario import Usuario
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class TestBaseRepositoryStructure:
    """BaseRepository class structure and initialization."""

    def test_class_is_generic(self):
        """BaseRepository should be a generic class."""
        assert hasattr(BaseRepository, "__orig_bases__") or hasattr(BaseRepository, "__parameters__")

    def test_constructor_accepts_session(self):
        """Constructor should accept session and optional tenant_id."""
        session = MagicMock(spec=AsyncSession)
        repo = BaseRepository[Usuario](session=session, tenant_id="tenant-a")
        assert repo.session is session
        assert repo.tenant_id == "tenant-a"

    def test_constructor_without_tenant_id(self):
        """Constructor should work without tenant_id."""
        session = MagicMock(spec=AsyncSession)
        repo = BaseRepository[Usuario](session=session)
        assert repo.tenant_id is None

    def test_model_class_property(self):
        """model_class should return the bound model class."""
        session = MagicMock(spec=AsyncSession)
        repo = BaseRepository[Usuario](session=session)
        assert repo.model_class is Usuario


class TestBaseRepositoryMethods:
    """BaseRepository CRUD method signatures and basic behavior."""

    @pytest.fixture
    def repo(self):
        session = MagicMock(spec=AsyncSession)
        return BaseRepository[Usuario](session=session, tenant_id="tenant-a")

    def test_has_get_method(self, repo):
        assert hasattr(repo, "get")

    def test_has_list_method(self, repo):
        assert hasattr(repo, "list")

    def test_has_create_method(self, repo):
        assert hasattr(repo, "create")

    def test_has_update_method(self, repo):
        assert hasattr(repo, "update")

    def test_has_soft_delete_method(self, repo):
        assert hasattr(repo, "soft_delete")

    # ── get, list, create, update, soft_delete are coroutine functions ─

    def test_get_is_coroutine_function(self, repo):
        """get should be a coroutine function (async def)."""
        import asyncio
        assert asyncio.iscoroutinefunction(repo.get)

    def test_list_is_coroutine_function(self, repo):
        import asyncio
        assert asyncio.iscoroutinefunction(repo.list)

    def test_create_is_coroutine_function(self, repo):
        import asyncio
        assert asyncio.iscoroutinefunction(repo.create)

    def test_update_is_coroutine_function(self, repo):
        import asyncio
        assert asyncio.iscoroutinefunction(repo.update)

    def test_soft_delete_is_coroutine_function(self, repo):
        import asyncio
        assert asyncio.iscoroutinefunction(repo.soft_delete)


class TestBaseRepositoryStmt:
    """_stmt() method generates correctly scoped SQL."""

    def test_stmt_returns_select_object(self):
        """_stmt should return a SQLAlchemy Select object."""
        session = MagicMock(spec=AsyncSession)
        repo = BaseRepository[Usuario](session=session, tenant_id="tenant-a")
        stmt = repo._stmt()
        from sqlalchemy import Select
        assert isinstance(stmt, Select)

    def test_stmt_includes_estado_filter(self):
        """_stmt should have WHERE conditions against estado."""
        session = MagicMock(spec=AsyncSession)
        repo = BaseRepository[Usuario](session=session, tenant_id="tenant-a")
        stmt = repo._stmt()
        compiled = stmt.compile(compile_kwargs={"literal_binds": True})
        sql = str(compiled)
        # Should reference the usuarios table and estado
        assert "usuarios" in sql
        assert "estado" in sql

    def test_stmt_without_tenant_does_not_crash(self):
        """_stmt with tenant_id=None should not raise."""
        session = MagicMock(spec=AsyncSession)
        repo = BaseRepository[Usuario](session=session, tenant_id=None)
        stmt = repo._stmt()
        from sqlalchemy import Select
        assert isinstance(stmt, Select)

    def test_stmt_on_model_without_tenant_id(self):
        """For a model without tenant_id, _stmt should skip tenant scope."""
        from app.models.tenant import Tenant

        session = MagicMock(spec=AsyncSession)
        repo = BaseRepository[Tenant](session=session, tenant_id="tenant-a")
        stmt = repo._stmt()
        from sqlalchemy import Select
        assert isinstance(stmt, Select)
