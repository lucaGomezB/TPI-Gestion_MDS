"""Seed script for initial data: TUPAD tenant + ADMIN user + 7 roles.

Idempotent — safe to run multiple times. Checks existence before inserting.

Usage:
    python -m app.seeds.seed_001

Requires a running PostgreSQL database with the schema already applied
(via ``alembic upgrade head``).
"""

import asyncio
import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session_maker
from app.core.permissions import ROL_PERMISSIONS
from app.core.security import hash_password
from app.models.rol import Rol
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.usuario_rol import UsuarioRol

TUPAD_NOMBRE = "TUPAD"
ADMIN_EMAIL = "admin@tupad.edu.ar"

# 7 roles as defined in the permissions matrix
ROLES_DATA = [
    {"nombre": "ALUMNO", "descripcion": "Estudiante que cursa materias"},
    {"nombre": "TUTOR", "descripcion": "Auxiliar / ayudante de cátedra"},
    {"nombre": "PROFESOR", "descripcion": "Docente a cargo de una o más comisiones"},
    {"nombre": "COORDINADOR", "descripcion": "Responsable de un conjunto de materias o cohorte"},
    {"nombre": "NEXO", "descripcion": "Rol de articulación / enlace transversal"},
    {"nombre": "ADMIN", "descripcion": "Administrador del sistema dentro del tenant"},
    {"nombre": "FINANZAS", "descripcion": "Responsable de liquidaciones y honorarios"},
]


async def seed_initial_data(session: AsyncSession) -> None:
    """Insert initial tenant (TUPAD), 7 roles, and ADMIN user.

    Idempotent: checks if the TUPAD tenant, roles, and ADMIN user exist
    before inserting.

    Args:
        session: An active SQLAlchemy ``AsyncSession``.
    """
    # ── Tenant ───────────────────────────────────────────────────────
    result = await session.execute(
        select(Tenant).where(Tenant.nombre == TUPAD_NOMBRE)
    )
    tenant = result.scalar_one_or_none()

    if tenant is None:
        tenant = Tenant(
            nombre=TUPAD_NOMBRE,
            configuracion={},
            activo=True,
        )
        session.add(tenant)
        await session.flush()
        print(f"Created tenant: {TUPAD_NOMBRE} (id={tenant.id})")
    else:
        print(f"Tenant already exists: {TUPAD_NOMBRE} (id={tenant.id})")

    # ── Roles ────────────────────────────────────────────────────────
    created_roles: dict[str, Rol] = {}
    for role_data in ROLES_DATA:
        result = await session.execute(
            select(Rol).where(
                Rol.tenant_id == tenant.id,
                Rol.nombre == role_data["nombre"],
            )
        )
        existing_rol = result.scalar_one_or_none()

        if existing_rol is None:
            rol = Rol(
                tenant_id=tenant.id,
                nombre=role_data["nombre"],
                descripcion=role_data["descripcion"],
                permisos=list(ROL_PERMISSIONS.get(role_data["nombre"], [])),
            )
            session.add(rol)
            await session.flush()
            created_roles[role_data["nombre"]] = rol
            print(f"Created role: {role_data['nombre']} (id={rol.id})")
        else:
            created_roles[role_data["nombre"]] = existing_rol
            print(f"Role already exists: {role_data['nombre']} (id={existing_rol.id})")

    # ── Admin user ───────────────────────────────────────────────────
    email_hash = Usuario.compute_email_hash(ADMIN_EMAIL)
    result = await session.execute(
        select(Usuario).where(
            Usuario.tenant_id == tenant.id,
            Usuario.email_hash == email_hash,
        )
    )
    admin = result.scalar_one_or_none()

    if admin is None:
        # Get default password from env or use fallback
        admin_password = os.environ.get("ADMIN_DEFAULT_PASSWORD", "admin123456")
        password_hash_value = hash_password(admin_password)

        admin = Usuario(
            tenant_id=tenant.id,
            email=ADMIN_EMAIL,
            email_hash=email_hash,
            nombre="Admin",
            apellidos="Sistema",
            password_hash=password_hash_value,
            facturador=False,
        )
        session.add(admin)
        await session.flush()
        print(f"Created admin user: {ADMIN_EMAIL} (id={admin.id})")
    else:
        print(f"Admin user already exists: {ADMIN_EMAIL} (id={admin.id})")

    # ── Assign ADMIN role to admin user ─────────────────────────────
    admin_rol = created_roles.get("ADMIN")
    if admin_rol is not None:
        result = await session.execute(
            select(UsuarioRol).where(
                UsuarioRol.usuario_id == admin.id,
                UsuarioRol.rol_id == admin_rol.id,
            )
        )
        existing_assignment = result.scalar_one_or_none()

        if existing_assignment is None:
            assignment = UsuarioRol(
                usuario_id=admin.id,
                rol_id=admin_rol.id,
                tenant_id=tenant.id,
            )
            session.add(assignment)
            await session.flush()
            print(f"Assigned ADMIN role to {ADMIN_EMAIL}")
        else:
            print(f"ADMIN role already assigned to {ADMIN_EMAIL}")

    await session.commit()
    print("Seed completed successfully.")


async def _main() -> None:
    """Standalone entry point for the seed script."""
    print("Starting seed...")
    settings = get_settings()
    print(f"Environment: {settings.environment}")
    session_maker = get_session_maker()
    async with session_maker() as session:
        await seed_initial_data(session)


if __name__ == "__main__":
    asyncio.run(_main())
