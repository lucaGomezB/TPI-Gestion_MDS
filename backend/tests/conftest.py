"""Shared pytest fixtures for backend tests."""

import os
from typing import Any

import pytest

# Set development defaults before any imports that use settings
os.environ.setdefault("SECRET_KEY", "a" * 32)
os.environ.setdefault("ENCRYPTION_KEY", "b" * 32)


@pytest.fixture(autouse=True)
def _reset_database_singletons() -> Any:
    """Reset database module singletons before each test.

    This prevents test order dependencies since ``get_engine()`` and
    ``get_session_maker()`` cache their results in module-level globals.
    """
    import app.core.database as dbmod

    dbmod._engine = None
    dbmod._session_maker = None
    yield
