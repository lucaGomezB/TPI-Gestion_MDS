"""Auth service — login, refresh, logout, password recovery.

Implements the core authentication flows:

- **Login**: Password verification with optional TOTP 2FA
- **Refresh**: Token rotation with family-wide theft detection
- **Logout**: Single token revocation
- **Password recovery**: Forgot + reset with single-use tokens
"""

import hashlib
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pyotp

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_temp_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.core.unit_of_work import UnitOfWork
from app.models.mixins import AuditMixin, EstadoRegistro
from app.models.usuario import Usuario
from app.schemas.auth import (
    TokenResponse,
    TwoFactorRequired,
)


class AuthService:
    """Authentication and authorization business logic.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    # ── Login flow ────────────────────────────────────────────────────

    async def login(
        self, email: str, password: str, tenant_id: str
    ) -> TokenResponse | TwoFactorRequired:
        """Authenticate a user with email and password.

        Args:
            email: The user's email address.
            password: The plaintext password.
            tenant_id: The tenant UUID.

        Returns:
            ``TokenResponse`` (if no 2FA) or ``TwoFactorRequired`` (if 2FA enabled).

        Raises:
            HTTPException(401): If credentials are invalid or user is inactive.
        """
        from fastapi import HTTPException
        from starlette.status import HTTP_401_UNAUTHORIZED

        user = await self.uow.auth.find_by_email(tenant_id, email)

        # Generic error — don't reveal whether email exists or password is wrong
        if user is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if user is active (soft-delete check)
        if hasattr(user, "estado") and user.estado != EstadoRegistro.ACTIVO:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if 2FA is enabled
        if user.totp_enabled:
            temp_token = create_temp_token(
                sub=user.id,
                purpose="totp_verification",
                expiry_minutes=2,
            )
            return TwoFactorRequired(
                requires_2fa=True,
                temp_token=temp_token,
            )

        # No 2FA — issue tokens directly
        return await self._issue_tokens(user)

    async def verify_totp(
        self, temp_token: str, totp_code: str, tenant_id: str
    ) -> TokenResponse:
        """Complete the 2FA login flow by verifying a TOTP code.

        Args:
            temp_token: The short-lived JWT from the first login step.
            totp_code: The 6-digit TOTP code from the authenticator app.
            tenant_id: The tenant UUID.

        Returns:
            ``TokenResponse`` with access and refresh tokens.

        Raises:
            HTTPException(401): If the temp_token is invalid or the TOTP code is wrong.
        """
        from fastapi import HTTPException
        from starlette.status import HTTP_401_UNAUTHORIZED

        # Decode and validate temp_token
        try:
            payload = decode_access_token(temp_token)
        except pyjwt.PyJWTError:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired verification token",
            )

        if payload.get("purpose") != "totp_verification":
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid verification token purpose",
            )

        user_id = payload.get("sub", "")
        user = await self.uow.auth.get_user_by_id(user_id)

        if user is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # TOTP verification
        if not user.totp_secret:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="TOTP not configured",
            )

        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(totp_code):
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code",
            )

        return await self._issue_tokens(user)

    # ── Token refresh with rotation (D-03) ────────────────────────────

    async def refresh(self, raw_token: str, tenant_id: str) -> TokenResponse:
        """Refresh an access token using a refresh token (rotation).

        Implements theft detection: if a revoked token is reused, the
        entire token family is revoked.

        Args:
            raw_token: The opaque refresh token string.
            tenant_id: The tenant UUID.

        Returns:
            ``TokenResponse`` with new access and refresh tokens.

        Raises:
            HTTPException(401): If the token is revoked, expired, or invalid.
        """
        from fastapi import HTTPException
        from starlette.status import HTTP_401_UNAUTHORIZED

        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        stored_token = await self.uow.auth.find_refresh_token(token_hash)

        if stored_token is None:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Theft detection: if token was already revoked, revoke entire family
        if stored_token.revoked_at is not None:
            await self.uow.auth.revoke_token_family(stored_token.token_family)
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        # Check expiry
        now = datetime.now(tz=timezone.utc)
        if stored_token.expires_at < now:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
            )

        # Revoke old token
        await self.uow.auth.revoke_refresh_token(token_hash)

        # Issue new tokens (same family)
        raw_new, new_hash, _ = create_refresh_token()
        settings = get_settings()
        expires_at = now + timedelta(days=settings.refresh_token_expire_days)
        await self.uow.auth.store_refresh_token(
            usuario_id=stored_token.usuario_id,
            token_hash=new_hash,
            expires_at=expires_at,
            token_family=stored_token.token_family,
            tenant_id=tenant_id,
        )

        # Get user roles for the new access token
        roles = await self.uow.auth.get_roles_for_user(stored_token.usuario_id)
        access_token = create_access_token(
            sub=stored_token.usuario_id,
            tenant_id=tenant_id,
            roles=roles,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_new,
            token_type="bearer",
        )

    # ── Logout (single token revocation) ──────────────────────────────

    async def logout(self, raw_token: str) -> None:
        """Revoke a single refresh token (logout).

        Args:
            raw_token: The opaque refresh token string.
        """
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        await self.uow.auth.revoke_refresh_token(token_hash)

    # ── Password recovery flow (D-08) ─────────────────────────────────

    async def forgot_password(self, email: str, tenant_id: str) -> dict:
        """Generate a password reset token.

        Idempotent: always returns the same success message regardless
        of whether the email exists (no information leakage).

        Args:
            email: The user's email address.
            tenant_id: The tenant UUID.

        Returns:
            A dict with ``message`` and, in MVP, the raw ``token``.
            In production, the token would be sent via email instead.
        """
        user = await self.uow.auth.find_by_email(tenant_id, email)

        if user is None:
            return {
                "message": "If the email exists, a recovery link has been sent",
            }

        # Generate reset token
        raw_token = __import__("os").urandom(32).hex()
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)

        await self.uow.auth.create_password_reset_token(
            usuario_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        # MVP: return token in response (no email service yet)
        return {
            "message": "If the email exists, a recovery link has been sent",
            "token": raw_token,
        }

    async def reset_password(self, token: str, new_password: str, tenant_id: str) -> dict:
        """Reset a user's password using a valid reset token.

        Args:
            token: The raw password reset token.
            new_password: The new plaintext password (will be hashed).
            tenant_id: The tenant UUID.

        Returns:
            A dict with success ``message``.

        Raises:
            HTTPException(400): If the token is invalid, expired, or already used.
        """
        from fastapi import HTTPException
        from starlette.status import HTTP_400_BAD_REQUEST

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        stored_token = await self.uow.auth.find_password_reset_token(token_hash)

        if stored_token is None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Invalid reset token",
            )

        if stored_token.used_at is not None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Reset token has already been used",
            )

        now = datetime.now(tz=timezone.utc)
        if stored_token.expires_at < now:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="Reset token has expired",
            )

        # Update password
        password_hash_value = hash_password(new_password)
        user = await self.uow.auth.get_user_by_id(stored_token.usuario_id)
        if user is None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="User not found",
            )

        user.password_hash = password_hash_value
        await self.uow.auth.flush()

        # Mark token as used
        await self.uow.auth.mark_reset_token_used(stored_token.id)

        # Revoke all existing refresh tokens for the user
        await self.uow.auth.revoke_all_user_tokens(stored_token.usuario_id)

        return {"message": "Password has been reset successfully"}

    # ── Internal helpers ──────────────────────────────────────────────

    async def _issue_tokens(self, user: Usuario) -> TokenResponse:
        """Issue access and refresh tokens for a user.

        Args:
            user: The authenticated ``Usuario`` instance.

        Returns:
            A ``TokenResponse`` with JWT access token and refresh token.
        """
        roles = await self.uow.auth.get_roles_for_user(user.id)

        # Create access token
        access_token = create_access_token(
            sub=user.id,
            tenant_id=user.tenant_id,
            roles=roles,
        )

        # Create refresh token
        raw_token, token_hash, token_family = create_refresh_token()
        settings = get_settings()
        expires_at = datetime.now(tz=timezone.utc) + timedelta(
            days=settings.refresh_token_expire_days
        )
        await self.uow.auth.store_refresh_token(
            usuario_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            token_family=token_family,
            tenant_id=user.tenant_id,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_token,
            token_type="bearer",
        )
