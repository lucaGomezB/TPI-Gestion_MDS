"""Tests for core.rate_limiter — in-memory sliding window rate limiter."""

import time

import pytest
from app.core.rate_limiter import RateLimiter, reset_rate_limiter


class TestRateLimiter:
    """In-memory sliding window rate limiter (Tasks 5.1, 5.2)."""

    def setup_method(self) -> None:
        """Reset the rate limiter before each test."""
        reset_rate_limiter()

    def test_first_attempt_allowed(self):
        """First attempt for a key should always be allowed."""
        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        assert limiter.check("ip123:email_hash_abc") is True

    def test_under_limit_allowed(self):
        """Up to max_attempts attempts should be allowed."""
        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        key = "ip123:email_hash_abc"
        for _ in range(5):
            assert limiter.check(key) is True

    def test_exceeds_limit_blocked(self):
        """The 6th attempt should be blocked."""
        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        key = "ip123:email_hash_abc"
        for _ in range(5):
            limiter.check(key)
        assert limiter.check(key) is False

    def test_reset_clears_counter(self):
        """After reset, attempts should be allowed again."""
        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        key = "ip123:email_hash_abc"
        for _ in range(5):
            limiter.check(key)
        limiter.reset(key)
        assert limiter.check(key) is True

    def test_different_keys_independent(self):
        """Rate limit should be per-key."""
        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        key_a = "ip1:hash_a"
        key_b = "ip2:hash_b"
        # Exhaust key_a
        for _ in range(5):
            limiter.check(key_a)
        assert limiter.check(key_a) is False
        # key_b should still be allowed
        assert limiter.check(key_b) is True

    def test_window_slides(self):
        """After window_seconds passes, old attempts should expire."""
        limiter = RateLimiter(max_attempts=2, window_seconds=1)
        key = "ip123:email_hash_abc"
        limiter.check(key)  # 1st
        limiter.check(key)  # 2nd
        assert limiter.check(key) is False  # 3rd blocked
        # Wait for window to slide
        time.sleep(1.1)
        assert limiter.check(key) is True  # Should be allowed now

    def test_reset_limiter_clears_all(self):
        """reset_rate_limiter() should clear all stored state."""
        limiter = RateLimiter(max_attempts=5, window_seconds=60)
        key = "ip123:email_hash_abc"
        for _ in range(5):
            limiter.check(key)
        reset_rate_limiter()
        # New RateLimiter should start fresh
        limiter2 = RateLimiter(max_attempts=5, window_seconds=60)
        assert limiter2.check(key) is True
