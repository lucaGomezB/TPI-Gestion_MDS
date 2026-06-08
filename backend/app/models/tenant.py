"""Tenant model — root multi-tenant entity.

Every other entity in the system belongs to a tenant. The Tenant model
represents an institution (e.g., "TUPAD") and stores configuration.

Attributes:
    nombre: Institution name.
    configuracion: JSONB configuration blob (per-tenant settings).
    activo: Whether the tenant is active.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import AppModel
from app.models.mixins import TimestampMixin


class Tenant(AppModel, TimestampMixin):
    """An institution or organization that uses the system.

    This is the root multi-tenancy entity. Most other models reference
    a tenant via ``TenantMixin.tenant_id``.
    """

    __tablename__ = "tenants"

    nombre: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    configuracion: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    config_moodle: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
