"""Auth repository — user lookup, role queries, token persistence.

All email lookups use ``email_hash`` (SHA-256 of lowercased email) to
avoid decrypting the PII email column.

Refresh tokens are stored as SHA-256 hashes of the raw opaque token.
The raw token is never stored — only the hash.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_token import RefreshToken
from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol


class AuthRepository:
    """Repository for authentication and authorization queries.

    Args:
        db: An active SQLAlchemy ``AsyncSession``.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── User lookup (via email_hash) ──────────────────────────────────

    async def find_by_email(self, tenant_id: str, email: str) -> Usuario | None:
        """Find a user by email within a tenant, using email_hash lookup.

        Args:
            tenant_id: The tenant UUID to scope the search.
            email: The plain email address (will be hashed for lookup).

        Returns:
            The ``Usuario`` instance or ``None`` if not found.
        """
        email_hash = Usuario.compute_email_hash(email)
        result = await self.db.execute(
            select(Usuario).where(
                Usuario.tenant_id == tenant_id,
                Usuario.email_hash == email_hash,
            )
        )
        return result.scalar_one_or_none()

    # ── Role queries ──────────────────────────────────────────────────

    async def get_roles_for_user(self, usuario_id: str) -> list[str]:
        """Get all role names assigned to a user.

        Joins ``UsuarioRol`` → ``Rol`` and returns role names.

        Args:
            usuario_id: The user UUID.

        Returns:
            A list of role name strings (e.g. ``["ADMIN", "COORDINADOR"]``).
        """
        result = await self.db.execute(
            select(Rol.nombre).select_from(UsuarioRol).join(
                Rol, UsuarioRol.rol_id == Rol.id
            ).where(
                UsuarioRol.usuario_id == usuario_id,
            )
        )
        return list(result.scalars().all())

    # ── Refresh token operations ──────────────────────────────────────

    async def store_refresh_token(
        self,
        usuario_id: str,
        token_hash: str,
        expires_at: datetime,
        token_family: str,
        tenant_id: str,
    ) -> RefreshToken:
        """Persist a new refresh token record.

        Args:
            usuario_id: The user UUID.
            token_hash: SHA-256 hash of the raw token.
            expires_at: Expiration timestamp (UTC).
            token_family: UUID grouping tokens of the same session.
            tenant_id: The tenant UUID.

        Returns:
            The created ``RefreshToken`` instance.
        """
        now = datetime.now(tz=timezone.utc)
        token = RefreshToken(
            usuario_id=usuario_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked_at=None,
            token_family=token_family,
            tenant_id=tenant_id,
            created_at=now,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def find_refresh_token(self, token_hash: str) -> RefreshToken | None:
        """Find a refresh token record by its SHA-256 hash.

        Args:
            token_hash: SHA-256 hex digest of the raw token.

        Returns:
            The ``RefreshToken`` instance or ``None`` if not found.
        """
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        """Revoke a refresh token by setting ``revoked_at``.

        Args:
            token_hash: SHA-256 hex digest of the raw token.
        """
        now = datetime.now(tz=timezone.utc)
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(revoked_at=now)
        )
        await self.db.flush()

    async def revoke_token_family(self, token_family: str) -> None:
        """Revoke ALL tokens in a token family (theft detection).

        Args:
            token_family: The UUID string of the token family.
        """
        now = datetime.now(tz=timezone.utc)
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_family == token_family)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self.db.flush()

    async def revoke_all_user_tokens(self, usuario_id: str) -> None:
        """Revoke ALL active refresh tokens for a user.

        Used after password reset.

        Args:
            usuario_id: The user UUID.
        """
        now = datetime.now(tz=timezone.utc)
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.usuario_id == usuario_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await self.db.flush()

    # ── Password reset token operations ───────────────────────────────

    async def create_password_reset_token(
        self,
        usuario_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        """Create a password reset token record.

        Args:
            usuario_id: The user UUID.
            token_hash: SHA-256 hash of the raw reset token.
            expires_at: Expiration timestamp (UTC), typically now + 1 hour.

        Returns:
            The created ``PasswordResetToken`` instance.
        """
        now = datetime.now(tz=timezone.utc)
        reset_token = PasswordResetToken(
            usuario_id=usuario_id,
            token_hash=token_hash,
            expires_at=expires_at,
            used_at=None,
            created_at=now,
        )
        self.db.add(reset_token)
        await self.db.flush()
        return reset_token

    async def find_password_reset_token(
        self, token_hash: str
    ) -> PasswordResetToken | None:
        """Find a password reset token by its SHA-256 hash.

        Args:
            token_hash: SHA-256 hex digest of the raw reset token.

        Returns:
            The ``PasswordResetToken`` instance or ``None`` if not found.
        """
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash
            )
        )
        return result.scalar_one_or_none()

    # ── Direct session helpers (for UoW migration) ─────────────────────

    async def get_user_by_id(self, user_id: str) -> Usuario | None:
        """Get a Usuario by primary key.

        Args:
            user_id: The user UUID.

        Returns:
            The ``Usuario`` instance or ``None`` if not found.
        """
        return await self.db.get(Usuario, user_id)

    async def flush(self) -> None:
        """Flush pending changes to the database."""
        await self.db.flush()

    async def mark_reset_token_used(self, token_id: str) -> None:
        """Mark a password reset token as used.

        Args:
            token_id: The UUID of the reset token record.
        """
        now = datetime.now(tz=timezone.utc)
        await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used_at=now)
        )
        await self.db.flush()
