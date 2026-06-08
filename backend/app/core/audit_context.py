"""Helpers to extract request metadata for audit logging.

Provides ``extract_request_metadata()`` to get the client IP and
User-Agent from a FastAPI ``Request`` object.

Usage in services::

    from app.core.audit_context import extract_request_metadata

    async def my_action(request: Request, ...):
        meta = extract_request_metadata(request)
        await audit_service.log_action(
            ...,
            ip=meta["ip"],
            user_agent=meta["user_agent"],
        )
"""

from fastapi import Request


def extract_request_metadata(request: Request) -> dict[str, str | None]:
    """Extract client IP and User-Agent from a FastAPI request.

    Handles proxy headers (``X-Forwarded-For``) and gracefully falls back
    to ``None`` when the header is absent.

    Args:
        request: The FastAPI ``Request`` object.

    Returns:
        A dict with:
        - ``ip``: The client IP address (or ``None``).
        - ``user_agent``: The User-Agent header value (or ``None``).
    """
    # Try X-Forwarded-For first (proxied requests), fall back to client.host
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None

    user_agent = request.headers.get("user-agent")

    return {"ip": ip, "user_agent": user_agent}
