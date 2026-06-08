## Why

C-01 established the project scaffold (FastAPI app, DB engine, config, empty layers). C-02 builds the **data foundation** that every feature in the system depends on: the base model mixins (id, tenant_id, timestamps, soft-delete), the first two concrete models (`Tenant` and `Usuario`), a generic tenant-scoped repository, and the AES-256 encryption layer for PII fields. Without this change, no subsequent change (auth, materias, calificaciones, etc.) can persist data.

## What Changes

- **Refactor `models/mixins.py`**: unify mixin contracts — `TimestampMixin`, `TenantMixin` (non-nullable column interface), and a new `AuditMixin` with `estado` enum (Activo/Inactivo) replacing the existing boolean `SoftDeleteMixin.is_active`.
- **Create `models/tenant.py`**: `Tenant` model with `nombre`, `configuracion` (JSONB), `activo` flag.
- **Create `models/usuario.py`**: `Usuario` model with all domain attributes (nombre, apellidos, email, dni, cuil, cbu, alias_cbu, banco, regional, legajo, legajo_profesional, facturador). PII fields (email, dni, cuil, cbu, alias_cbu) stored encrypted via the security layer.
- **Implement AES-256-GCM encryption** in `core/security.py` using the `cryptography` library (Fernet-compatible / AES-GCM). Functions: `aes_encrypt(plaintext, key) -> str`, `aes_decrypt(ciphertext, key) -> str`. Key derived from the `ENCRYPTION_KEY` setting.
- **Create `repositories/base.py`**: generic `BaseRepository[T]` with automatic tenant scope from the authenticated session, default CRUD operations (get, list, create, update, soft-delete).
- **Create `migrations/versions/001_tenants_usuarios.py`**: Alembic migration creating `tenants` and `usuarios` tables with indexes and constraints.
- **Create `seeds/seed_001.py`** (or integrate with Alembic): seed script inserting 1 tenant (TUPAD) and 1 ADMIN user (with encrypted PII).
- **Soft-delete always**: the `Usuario` model uses soft delete via `AuditMixin` — never hard delete.

## Capabilities

### New Capabilities
- `core-models`: Base model mixins (`BaseMixin`, `AuditMixin`), `Tenant` model, `Usuario` model with encrypted PII, and the generic `BaseRepository[T]` with automatic tenant scoping.
- `pii-encryption`: AES-256-GCM encryption and decryption for sensitive personal data at rest.
- `base-repository`: Generic repository pattern providing `get`, `list`, `create`, `update`, `soft_delete` with implicit tenant filter.

### Modified Capabilities
None — this is the first data-layer change.

## Impact

- **Backend**: `app/core/security.py` — implement real AES-256-GCM; `app/models/` — add Tenant and Usuario; `app/repositories/base.py` — generic repository; `alembic/versions/001_*` — migration; `app/seeds/` — seed data.
- **Dependencies**: The `cryptography` library must be added to `requirements.txt`.
- **Config**: `ENCRYPTION_KEY` env var is already in `.env.example` (from C-01) — must be validated to be exactly 32 bytes for AES-256.
- **Governance**: This is a **CRITICO** change. It defines the data foundation. Design decisions (PII encryption strategy, repository pattern, soft-delete semantics) must be reviewed before implementation.
