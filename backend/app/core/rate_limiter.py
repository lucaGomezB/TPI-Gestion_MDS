"""In-memory sliding window rate limiter for login attempts.

Keyed by ``{ip}:{email_hash}`` with a 60-second window and max 5 attempts.
Resets on successful login. State is lost on process restart (acceptable for MVP).

In production, this should be replaced with Redis-based rate limiting.
"""

import time

from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

# Module-level store: key → list of attempt timestamps
_attempts: dict[str, list[float]] = {}


def reset_rate_limiter() -> None:
    """Clear all rate limiter state. Used in tests and after successful login."""
    _attempts.clear()


class RateLimiter:
    """In-memory sliding window rate limiter.

    Args:
        max_attempts: Maximum number of attempts allowed in the window (default 5).
        window_seconds: Duration of the sliding window in seconds (default 60).
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    def check(self, key: str) -> bool:
        """Check if an attempt is allowed for the given key.

        Returns:
            ``True`` if the attempt is allowed, ``False`` if rate limited.
        """
        now = time.time()
        window_start = now - self.window_seconds

        if key not in _attempts:
            _attempts[key] = []

        # Remove attempts outside the window
        _attempts[key] = [t for t in _attempts[key] if t > window_start]

        if len(_attempts[key]) >= self.max_attempts:
            return False

        _attempts[key].append(now)
        return True

    def reset(self, key: str) -> None:
        """Reset the rate limit counter for a specific key.

        Called after a successful login for the user's IP+email key.
        """
        _attempts.pop(key, None)


# Singleton instance used by FastAPI dependency
_login_limiter = RateLimiter()


def check_login_rate_limit(request: Request, email: str) -> None:
    """FastAPI dependency that checks the login rate limit.

    Args:
        request: The incoming HTTP request (used to extract client IP).
        email: The email address being used for login (used for hashing).

    Raises:
        HTTPException(429): If the rate limit is exceeded.
    """
    import hashlib

    client_ip = request.client.host if request.client else "unknown"
    email_hash = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    key = f"{client_ip}:{email_hash}"

    if not _login_limiter.check(key):
        raise HTTPException(
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again in 60 seconds.",
        )


def reset_login_attempts(request: Request, email: str) -> None:
    """Reset the login rate counter after a successful login.

    Args:
        request: The incoming HTTP request (used to extract client IP).
        email: The email address that just logged in successfully.
    """
    import hashlib

    client_ip = request.client.host if request.client else "unknown"
    email_hash = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()
    key = f"{client_ip}:{email_hash}"
    _login_limiter.reset(key)
