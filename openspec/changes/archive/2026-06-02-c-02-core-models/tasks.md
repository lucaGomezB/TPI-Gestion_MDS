## 1. Dependencies and configuration

- [x] 1.1 Add `cryptography` library to `backend/requirements.txt` (already present from C-01)
- [x] 1.2 Create `backend/tests/__init__.py` if not present (for test discovery)

## 2. Refactor mixins in `models/mixins.py`

- [x] 2.1 Create `EstadoRegistro` enum (`Activo` | `Inactivo`) in `models/mixins.py`
- [x] 2.2 Replace `SoftDeleteMixin` with `AuditMixin`: swap `is_active: bool` for `estado: EstadoRegistro` (default `Activo`), keep `deleted_at`
- [x] 2.3 Update `TenantMixin` to default `tenant_id` to nullable=True but document that domain models MUST override to nullable=False
- [x] 2.4 Verify `AppModel` in `models/base.py` remains unchanged (already provides UUID id + auto tablename)
- [x] 2.5 Update `models/__init__.py` to export all mixins and enums

## 3. Implement AES-256-GCM encryption in `core/security.py`

- [x] 3.1 Import `AESGCM` from `cryptography.hazmat.primitives.ciphers.aead` and `base64`
- [x] 3.2 Implement `aes_encrypt(plaintext: str, key: bytes) -> str` — generates random 12-byte nonce, encrypts with AESGCM, returns URL-safe base64(nonce + ciphertext + tag)
- [x] 3.3 Implement `aes_decrypt(ciphertext: str, key: bytes) -> str` — decodes base64, extracts nonce (first 12 bytes), decrypts with AESGCM, returns plaintext
- [x] 3.4 Validate `key` length (must be exactly 32 bytes), raise `ValueError` otherwise
- [x] 3.5 Add `get_encryption_key() -> bytes` helper that reads `ENCRYPTION_KEY` from settings
- [x] 3.6 Write unit tests for: encrypt/decrypt roundtrip, different ciphertext per call, wrong key raises error, invalid key length raises ValueError

## 4. Create `EncryptedString` TypeDecorator in `models/types.py`

- [x] 4.1 Create `backend/app/models/types.py` with `EncryptedString(TypeDecorator)` — `impl = Text`, `process_bind_param` calls `aes_encrypt`, `process_result_value` calls `aes_decrypt`
- [x] 4.2 Handle `None` values (pass through)
- [x] 4.3 Update `models/__init__.py` to export `EncryptedString`

## 5. Create `Tenant` model

- [x] 5.1 Create `backend/app/models/tenant.py` with `Tenant(AppModel, TimestampMixin)` — attributes: `nombre`, `configuracion` (JSONB, default `{}`), `activo` (default `True`)
- [x] 5.2 Override `__tablename__` to `"tenants"` explicitly (to avoid automatic plural issues)
- [x] 5.3 Define indexes: no unique constraint yet (single-tenant starter)
- [x] 5.4 Update `models/__init__.py` to export `Tenant`

## 6. Create `Usuario` model

- [x] 6.1 Create `backend/app/models/usuario.py` with `Usuario(AppModel, TimestampMixin, AuditMixin, TenantMixin)` — all attributes from E4 spec
- [x] 6.2 Override `tenant_id` to `nullable=False, ForeignKey("tenants.id")`
- [x] 6.3 Declare PII fields (`email`, `dni`, `cuil`, `cbu`, `alias_cbu`) as `EncryptedString` type
- [x] 6.4 Add `email_hash: str` column — SHA-256 hex digest of plaintext email, NOT encrypted
- [x] 6.5 Add unique constraint: `(tenant_id, email_hash)` — enables unique email per tenant
- [x] 6.6 Add index on `(tenant_id, email_hash)` for login lookups
- [x] 6.7 Update `models/__init__.py` to export `Usuario`

## 7. Create `BaseRepository[T]` in `repositories/base.py`

- [x] 7.1 Create `backend/app/repositories/base.py` with generic `BaseRepository[T: AppModel]`
- [x] 7.2 Implement constructor: accepts `session: AsyncSession`, `tenant_id: str | None`
- [x] 7.3 Implement `_stmt()` — base `select(self.model_class)` with optional `WHERE tenant_id = ...` and default `WHERE estado != 'Inactivo'`
- [x] 7.4 Implement `get(id) -> T | None` — scoped by tenant
- [x] 7.5 Implement `list(**filters) -> list[T]` — scoped by tenant, excludes inactive
- [x] 7.6 Implement `create(data: dict) -> T` — sets `tenant_id` automatically if applicable
- [x] 7.7 Implement `update(id, data: dict) -> T | None` — partial update, sets `updated_at`
- [x] 7.8 Implement `soft_delete(id)` — sets `estado='Inactivo'` and `deleted_at=now()`
- [x] 7.9 Add `model_class` property derived from `Generic[T]` or constructor parameter
- [x] 7.10 Update `repositories/__init__.py` to export `BaseRepository`

## 8. Generate Alembic migration 001

- [x] 8.1 Set up `backend/alembic/env.py` to use the async engine and `AppModel.metadata` (verify from C-01)
- [x] 8.2 Write manual migration `d715beceafc3_001_tenants_usuarios.py` creating both tables
- [x] 8.3 Reviewed migration for correctness: `tenants` table, `usuarios` table, foreign keys, indexes, unique constraints
- [x] 8.4 Encrypted columns use `sa.Text()` (not `sa.String()` with length)
- [x] 8.5 Downgrade drops both tables (tested via code review)

## 9. Create seed script

- [x] 9.1 Create `backend/app/seeds/__init__.py`
- [x] 9.2 Create `backend/app/seeds/seed_001.py` — function `seed_initial_data(session: AsyncSession)`
- [x] 9.3 Insert tenant TUPAD with `configuracion={}` if not exists (idempotent)
- [x] 9.4 Insert ADMIN user: `email="admin@tupad.edu.ar"`, `nombre="Admin"`, `apellidos="Sistema"`, `facturador=False`
- [x] 9.5 Add `if __name__ == "__main__"` block for standalone execution

## 10. Write integration tests

- [x] 10.1 Create `backend/tests/models/test_tenant.py` — model structure tests (DB roundtrip requires PostgreSQL)
- [x] 10.2 Create `backend/tests/models/test_usuario.py` — model structure, PII encryption types, email_hash, unique constraint (DB roundtrip requires PostgreSQL)
- [x] 10.3 Create `backend/tests/repositories/test_base_repository.py` — structure, _stmt() scoping tests (async CRUD requires PostgreSQL)
- [x] 10.4 Create `backend/tests/core/test_security.py` — AES encrypt/decrypt roundtrip, wrong key, invalid key (fully tested)
