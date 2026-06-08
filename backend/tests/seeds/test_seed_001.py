"""Tests for seed_001 script — structure and function signature."""

import inspect

import pytest
from app.seeds.seed_001 import seed_initial_data


class TestSeed001:
    """Seed function structure and contract."""

    def test_seed_initial_data_is_async_function(self):
        """seed_initial_data should be an async function."""
        assert inspect.iscoroutinefunction(seed_initial_data)

    def test_seed_initial_data_accepts_session(self):
        """seed_initial_data should accept a session parameter."""
        sig = inspect.signature(seed_initial_data)
        assert "session" in sig.parameters
