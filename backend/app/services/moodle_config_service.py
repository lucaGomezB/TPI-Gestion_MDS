"""Service for per-tenant Moodle configuration management.

Handles loading, saving, and querying Moodle Web Services configuration
with automatic AES-256 encryption/decryption of sensitive fields.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.security import decrypt_moodle_config, encrypt_moodle_config
from app.core.unit_of_work import UnitOfWork
from app.models.tenant import Tenant
from app.schemas.moodle_config import MoodleConfigSchema, MoodleConfigUpdateSchema

logger = logging.getLogger(__name__)


class MoodleConfigService:
    """Manages per-tenant Moodle WS configuration with encrypted storage.

    Configuration is stored in the ``Tenant.config_moodle`` JSONB column.
    Sensitive fields (ws_url, ws_token) are AES-256 encrypted at rest.
    """

    async def get_moodle_config(
        self, uow: UnitOfWork, tenant_id: str
    ) -> MoodleConfigSchema | None:
        """Load and decrypt the Moodle configuration for a tenant.

        Args:
            uow: The ``UnitOfWork`` instance for data access.
            tenant_id: The tenant UUID.

        Returns:
            A ``MoodleConfigSchema`` with decrypted values, or ``None``
            if no configuration exists.
        """
        result = await uow._session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            return None

        raw_config = getattr(tenant, "config_moodle", None)
        if not raw_config:
            return None

        decrypted = decrypt_moodle_config(raw_config)
        return MoodleConfigSchema(**decrypted)

    async def set_moodle_config(
        self,
        uow: UnitOfWork,
        tenant_id: str,
        config_in: MoodleConfigUpdateSchema,
    ) -> MoodleConfigSchema:
        """Encrypt and save the Moodle configuration for a tenant.

        Args:
            uow: The ``UnitOfWork`` instance for data access.
            tenant_id: The tenant UUID.
            config_in: The configuration update data.

        Returns:
            The saved ``MoodleConfigSchema`` with decrypted values.
        """
        result = await uow._session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise ValueError(f"Tenant not found: {tenant_id}")

        current_config = getattr(tenant, "config_moodle", None) or {}

        # Merge existing config with updates
        update_data = config_in.model_dump(exclude_unset=True)
        merged = {**current_config, **update_data}

        # If ws_enabled is being set to None or not provided, keep existing
        if "ws_enabled" not in update_data:
            merged.setdefault("ws_enabled", True)

        # Encrypt sensitive fields before saving
        encrypted_config = encrypt_moodle_config(merged)

        tenant.config_moodle = encrypted_config  # type: ignore[attr-defined]
        await uow._session.flush()

        # Return decrypted version
        decrypted = decrypt_moodle_config(encrypted_config)
        return MoodleConfigSchema(**decrypted)

    async def is_moodle_enabled(
        self, uow: UnitOfWork, tenant_id: str
    ) -> bool:
        """Quick check if Moodle WS is enabled for a tenant.

        Args:
            uow: The ``UnitOfWork`` instance for data access.
            tenant_id: The tenant UUID.

        Returns:
            ``True`` if Moodle WS is configured and enabled.
        """
        config = await self.get_moodle_config(uow, tenant_id)
        if config is None:
            return False
        return bool(config.ws_enabled and config.ws_url and config.ws_token)

    async def clear_moodle_config(
        self, uow: UnitOfWork, tenant_id: str
    ) -> None:
        """Remove the Moodle configuration for a tenant.

        Args:
            uow: The ``UnitOfWork`` instance for data access.
            tenant_id: The tenant UUID.
        """
        result = await uow._session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise ValueError(f"Tenant not found: {tenant_id}")

        tenant.config_moodle = None  # type: ignore[attr-defined]
        await uow._session.flush()

    async def get_all_enabled_tenants(
        self, uow: UnitOfWork
    ) -> list[tuple[str, MoodleConfigSchema]]:
        """Get all tenants with Moodle WS enabled.

        Returns:
            A list of ``(tenant_id, config)`` tuples.
        """
        result = await uow._session.execute(select(Tenant).where(Tenant.activo == True))  # noqa: E712
        tenants = result.scalars().all()

        enabled: list[tuple[str, MoodleConfigSchema]] = []
        for tenant in tenants:
            raw_config = getattr(tenant, "config_moodle", None)
            if not raw_config:
                continue
            decrypted = decrypt_moodle_config(raw_config)
            config = MoodleConfigSchema(**decrypted)
            if config.ws_enabled and config.ws_url and config.ws_token:
                enabled.append((tenant.id, config))

        return enabled


moodle_config_service = MoodleConfigService()
