"""Auth router — login, refresh, logout, password recovery, and user profile.

Endpoints:
- ``POST /api/auth/login`` — Email + password authentication (with optional 2FA)
- ``POST /api/auth/login/totp`` — Complete 2FA flow with TOTP code
- ``POST /api/auth/refresh`` — Rotate refresh token (with theft detection)
- ``POST /api/auth/logout`` — Revoke refresh token
- ``POST /api/auth/forgot-password`` — Request password reset token
- ``POST /api/auth/reset-password`` — Complete password reset
- ``GET /api/auth/me`` — Get current user profile
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
)

from app.core.dependencies import get_current_user, get_db, require_permission
from app.core.rate_limiter import (
    check_login_rate_limit,
    reset_login_attempts,
)
from app.core.unit_of_work import UnitOfWork
from app.models.usuario import Usuario
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LoginTotpRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    TwoFactorRequired,
    UserMeResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/api/auth/login")
async def login(
    request: Request,
    body: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[None, Depends(check_login_rate_limit)],
) -> TokenResponse | TwoFactorRequired:
    """Authenticate with email and password.

    If the user has TOTP 2FA enabled, returns ``TwoFactorRequired`` (HTTP 202)
    with a temporary token for the second step.

    Rate-limited: 5 attempts per 60 seconds per IP+email.
    """
    # In MVP, tenant_id is resolved from JWT or subdomain. For login,
    # there is no JWT yet, so we use a default approach. The frontend
    # would typically send a tenant hint; for now we query by tenant
    # name derived from email domain or use the TUPAD tenant.
    # This is a known limitation: multi-tenant login will be refined
    # in a future change with tenant resolution.
    from app.models.tenant import Tenant
    from sqlalchemy import select

    # For MVP, find the first active tenant
    result = await db.execute(
        select(Tenant).where(Tenant.activo.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No active tenant found")

    async with UnitOfWork(db, tenant.id) as uow:
        service = AuthService(uow)

        try:
            result_auth = await service.login(
                email=body.email,
                password=body.password,
                tenant_id=tenant.id,
            )
            # Reset rate limiter on successful login
            reset_login_attempts(request, body.email)

            if isinstance(result_auth, TwoFactorRequired):
                return JSONResponse(
                    status_code=202,
                    content=result_auth.model_dump(),
                )

            return result_auth
        except HTTPException:
            raise


@router.post("/api/auth/login/totp")
async def login_totp(
    body: LoginTotpRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Complete the 2FA login flow with a TOTP code.

    Requires a valid ``temp_token`` from the first login step and a
    6-digit TOTP code from the user's authenticator app.
    """
    from app.models.tenant import Tenant
    from sqlalchemy import select

    # Find active tenant (same limitation as login)
    result = await db.execute(
        select(Tenant).where(Tenant.activo.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No active tenant found")

    async with UnitOfWork(db, tenant.id) as uow:
        service = AuthService(uow)
        return await service.verify_totp(
            temp_token=body.temp_token,
            totp_code=body.totp_code,
            tenant_id=tenant.id,
        )


@router.post("/api/auth/refresh")
async def refresh(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Rotate a refresh token.

    The old token is revoked and a new access+refresh pair is issued.
    If a revoked token is reused, the entire token family is revoked
    (theft detection).
    """
    from app.models.tenant import Tenant
    from sqlalchemy import select

    result = await db.execute(
        select(Tenant).where(Tenant.activo.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No active tenant found")

    async with UnitOfWork(db, tenant.id) as uow:
        service = AuthService(uow)
        return await service.refresh(
            raw_token=body.refresh_token,
            tenant_id=tenant.id,
        )


@router.post("/api/auth/logout", status_code=HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _current_user: Annotated[dict, Depends(get_current_user)],
) -> None:
    """Revoke a refresh token (logout).

    Requires authentication (valid JWT in Authorization header).
    """
    async with UnitOfWork(db, "") as uow:
        service = AuthService(uow)
        await service.logout(raw_token=body.refresh_token)


@router.post("/api/auth/forgot-password")
async def forgot_password(
    body: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Request a password reset token.

    Always returns the same generic message regardless of whether the
    email exists (no information leakage). In MVP, the token is returned
    in the response body.
    """
    from app.models.tenant import Tenant
    from sqlalchemy import select

    result = await db.execute(
        select(Tenant).where(Tenant.activo.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No active tenant found")

    async with UnitOfWork(db, tenant.id) as uow:
        service = AuthService(uow)
        return await service.forgot_password(
            email=body.email,
            tenant_id=tenant.id,
        )


@router.post("/api/auth/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Reset a password using a valid reset token.

    The new password must be at least 8 characters long.
    """
    from app.models.tenant import Tenant
    from sqlalchemy import select

    result = await db.execute(
        select(Tenant).where(Tenant.activo.is_(True))
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="No active tenant found")

    async with UnitOfWork(db, tenant.id) as uow:
        service = AuthService(uow)
        return await service.reset_password(
            token=body.token,
            new_password=body.new_password,
            tenant_id=tenant.id,
        )


@router.get("/api/auth/me", response_model=UserMeResponse)
async def get_me(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserMeResponse:
    """Get the current user's profile.

    Requires a valid JWT in the Authorization header.
    Returns id, nombre, apellidos, email, roles, and tenant_id.
    Sensitive fields (password_hash, totp_secret, deleted_at) are NOT exposed.
    """
    user_id = current_user.get("id", "")
    result = await db.get(Usuario, user_id)
    if result is None:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    roles = current_user.get("roles", [])

    return UserMeResponse(
        id=result.id,
        nombre=result.nombre,
        apellidos=result.apellidos,
        email=result.email,
        roles=roles,
        tenant_id=result.tenant_id,
    )
