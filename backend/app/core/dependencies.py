"""FastAPI dependency injection for auth, DB, and RBAC.

Provides:
- ``get_db``: yields an async database session
- ``get_current_user``: extracts and validates JWT from Authorization header
- ``require_permission``: factory that returns a dependency checking user permissions
"""

from collections.abc import AsyncGenerator, Callable
from typing import Annotated

import jwt as pyjwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from app.core.database import get_session
from app.core.permissions import ROL_PERMISSIONS
from app.core.security import decode_access_token
from app.models.usuario import Usuario

# ── DB session dependency ────────────────────────────────────────────────────


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Dependency that provides a database session.

    Usage in routers::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async for session in get_session():
        yield session


# ── JWT auth scheme ──────────────────────────────────────────────────────────

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Extract and validate the JWT from the Authorization header.

    Returns a dict with the user's identity:
        ``{"id": str, "tenant_id": str, "roles": list[str]}``

    Raises:
        HTTPException(401): If the token is missing, expired, or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except pyjwt.PyJWTError:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    return {
        "id": payload.get("sub", ""),
        "tenant_id": payload.get("tenant_id", ""),
        "roles": payload.get("roles", []),
    }


# ── Permission check dependency ──────────────────────────────────────────────


def require_permission(permission: str) -> Callable[[dict], None]:
    """Factory that returns a FastAPI dependency checking a specific permission.

    Usage::

        @router.get("/calificaciones")
        async def list_calificaciones(
            _: Annotated[None, Depends(require_permission("calificaciones:importar"))],
        ):
            ...

    Args:
        permission: The permission string (e.g. ``"calificaciones:importar"``).

    Returns:
        A FastAPI dependency that extracts the current user's roles from JWT
        and checks them against the permissions matrix. Raises 403 or 401.
    """

    async def _check_permission(
        current_user: Annotated[dict, Depends(get_current_user)],
    ) -> None:
        """Check if the current user has the required permission."""
        user_roles = current_user.get("roles", [])

        for role in user_roles:
            role_perms = ROL_PERMISSIONS.get(role, set())
            if permission in role_perms:
                return

        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    return _check_permission
