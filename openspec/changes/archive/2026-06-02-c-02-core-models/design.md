## Context

C-01 (foundation-setup) established the project scaffold: FastAPI app with health check, async DB engine (`database.py`), `AppModel` DeclarativeBase with UUID PK and auto tablename, composable mixins (`TimestampMixin`, `SoftDeleteMixin`, `TenantMixin`), security stubs, and structured logging. No models, no migrations, no seed data exist yet.

C-02 builds the **data foundation** that every subsequent feature depends on. The key work is:

1. Refine the mixin layer to match the domain's audit/soft-delete semantics (estado enum instead of boolean `is_active`).
2. Implement `Tenant` and `Usuario` models — the root entities of the multi-tenant model.
3. Implement real AES-256-GCM encryption for PII fields (`core/security.py`).
4. Create a generic `BaseRepository[T]` with automatic tenant scoping.
5. Generate the first Alembic migration (`001_tenants_usuarios`).
6. Provide a seed script for the initial tenant (TUPAD) and ADMIN user.

**Stakeholders / consumers:** All later changes (C-03 auth-rbac through C-27) depend on these models, mixins, and encryption.

## Goals / Non-Goals

**Goals:**
- Establish `AuditMixin` with `estado` (Activo/Inactivo) replacing the existing `SoftDeleteMixin.is_active` boolean — representing canonical soft-delete semantics.
- Create `Tenant` model as the root multi-tenant entity with configurable JSONB.
- Create `Usuario` model with all domain attributes; PII fields (email, dni, cuil, cbu, alias_cbu) stored encrypted.
- Implement AES-256-GCM encryption in `core/security.py` with `aes_encrypt` and `aes_decrypt`.
- Create an `EncryptedString` SQLAlchemy TypeDecorator for transparent encryption at the model field level.
- Implement `BaseRepository[T]` generic with scope-by-tenant, default CRUD + soft delete.
- Generate Alembic migration 001 for `tenants` and `usuarios` tables.
- Provide a repeatable seed script for the initial tenant + ADMIN user.
- All code conforms to project conventions (snake_case, max 500 LOC/file, `extra='forbid'`, soft delete).

**Non-Goals:**
- Not implementing any API routers or endpoints (those start in C-03).
- Not implementing password hashing (Argon2id) — that belongs in C-03 (auth-rbac).
- Not implementing full permission checking (that uses `require_permission` from C-03).
- Not implementing the `Asignacion` model or RBAC roles (those are C-03/C-05).
- Not implementing composite indexes beyond what migration 001 requires.

## Decisions

### D1: Mixin architecture — composable over monolithic

Rather than a single `BaseMixin` class that combines id + tenant_id + timestamps, we keep the **composable mixin** approach already established in C-01 (`models/mixins.py`). This is more Pythonic and allows models to opt into only what they need (e.g., `Tenant` itself does not have a `tenant_id` because it is the root).

**What we add / change:**
- Replace `SoftDeleteMixin` with `AuditMixin` — uses an `EstadoRegistro` enum (`Activo` | `Inactivo`) instead of `is_active: bool`.
- Keep `deleted_at` timestamp on `AuditMixin` for soft-delete tracking.
- Keep `TimestampMixin` (created_at, updated_at) unchanged.
- Keep `TenantMixin` (tenant_id FK) unchanged but make the column non-nullable for domain models.
- `AppModel` (id + auto tablename) remains the ORM base.

**Concrete models** will use: `class Usuario(AppModel, TimestampMixin, AuditMixin, TenantMixin)`. The `tenant_id` column is overridden to `nullable=False` on the model.

### D2: `estado` enum (AuditMixin) over boolean `is_active`

**Rationale:**
- `estado` with `Activo/Inactivo` is the domain language used throughout the knowledge base (see `04_modelo_de_datos.md`), not a generic `is_active` flag.
- An enum is self-documenting at the database level. It also allows future states (e.g., `Suspendido`, `Bloqueado`) without schema changes.
- Backward compatibility: C-01's `SoftDeleteMixin` is replaced because no models use it yet.

**Implementation:**
```python
class EstadoRegistro(str, enum.Enum):
    ACTIVO = "Activo"
    INACTIVO = "Inactivo"
```

`AuditMixin` has:
- `estado: EstadoRegistro` (default `ACTIVO`)
- `deleted_at: datetime | None` (nullable, set on soft-delete)

### D3: AES-256-GCM via `cryptography` library

**Library:** `cryptography` (the de-facto Python crypto library, actively maintained).

**Algorithm:** AES-256-GCM — an authenticated encryption (AEAD) algorithm that provides both confidentiality and integrity. GCM produces a 12-byte nonce (unique IV per encryption), ciphertext, and a 16-byte authentication tag.

**Key:** The `ENCRYPTION_KEY` from settings (32 bytes). The setting is already declared in `config.py` with `min_length=32`.

**API:**
```python
def aes_encrypt(plaintext: str, key: bytes) -> str:
    """Returns URL-safe base64-encoded (nonce + ciphertext + tag)."""
def aes_decrypt(ciphertext: str, key: bytes) -> str:
    """Takes URL-safe base64 string, returns plaintext."""
```

**Storage format:** `base64(nonce || ciphertext || tag)` — single string stored in a `TEXT` column. The `||` denotes concatenation. Nonce is 12 bytes, tag is 16 bytes, ciphertext is variable.

### D4: `EncryptedString` TypeDecorator — transparent model encryption

An `EncryptedString` SQLAlchemy `TypeDecorator` that wraps the AES-256-GCM functions:

```python
class EncryptedString(TypeDecorator):
    impl = Text
    def process_bind_param(self, value, dialect) -> str | None:
        return aes_encrypt(value, get_encryption_key()) if value else None
    def process_result_value(self, value, dialect) -> str | None:
        return aes_decrypt(value, get_encryption_key()) if value else None
```

**Rationale:** Without a TypeDecorator, every read/write of PII fields would require explicit encrypt/decrypt calls in the service layer — error-prone and violating DRY. With TypeDecorator, models declare `email: Mapped[str] = mapped_column(EncryptedString)` and encryption is transparent.

**Query limitation:** Encrypted fields cannot be filtered with `WHERE email = '...'`. This is acceptable because:
- Tenant-scoped lookups filter by `tenant_id` + `id`.
- Login will be by email (C-03), which MUST be resolved via an index on the plaintext value. For this, we add a **deterministic hash column** `email_hash` to the `Usuario` model, which is a SHA-256 hash of the plaintext email. This enables `WHERE email_hash = sha256('user@example.com')` without exposing the email.

### D5: Deterministic hash for email lookups

For C-03 (login), the system needs to find a user by email. Since the email column is encrypted and AES-GCM is non-deterministic (each encryption produces different ciphertext), querying by encrypted email is impossible.

**Solution:** Add a `email_hash` column on `Usuario` — a SHA-256 hex digest of the plaintext (lowercased) email. This is stored in a separate `TEXT` column, NOT encrypted (it's a hash). The hash is deterministic and searchable.

This is a **necessary trade-off**: the email is hashed (one-way), but the hash is deterministic and can be used for equality lookups. Since the hash is of the full email (high entropy), rainbow table attacks are impractical.

### D6: `BaseRepository[T]` — generic with automatic tenant scope

```python
T = TypeVar("T", bound=AppModel)

class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, tenant_id: str | None = None):
        self.session = session
        self.tenant_id = tenant_id  # None for models without tenant scope (e.g., Tenant itself)

    def _stmt(self) -> Select:
        """Base select statement, automatically scoped by tenant_id if present."""
        stmt = select(self.model_class)
        if self.tenant_id and hasattr(self.model_class, "tenant_id"):
            stmt = stmt.where(self.model_class.tenant_id == self.tenant_id)
        return stmt

    async def get(self, id: str) -> T | None: ...
    async def list(self, **filters) -> list[T]: ...
    async def create(self, data: dict) -> T: ...
    async def update(self, id: str, data: dict) -> T | None: ...
    async def soft_delete(self, id: str) -> None: ...
```

**Design decisions:**
- `tenant_id` is injected from the authenticated session, never from request parameters.
- For models that don't have a tenant_id (e.g., `Tenant` itself), `TenantRepository` subclasses `BaseRepository` and overrides the scope behavior.
- `soft_delete` sets `estado = EstadoRegistro.INACTIVO` and `deleted_at = now()`.
- All list queries exclude soft-deleted records by default (`estado != INACTIVO`).

### D7: Seed data — standalone script, not in migration

Ate `app/seeds/seed_001.py` that uses the async session factory directly. Idempotent (checks if TUPAD tenant exists before inserting).

**Seed values:**
- Tenant: `nombre="TUPAD", configuracion={}, activo=True`
- Usuario: `nombre="Admin", apellidos="Sistema", email="admin@tupad.edu.ar"` (encrypted), role implied for C-03 (no roles table yet, but we'll create the user).

### D8: Migration naming and structure

Alembic migration `001_tenants_usuarios.py`:
- Creates `tenants` table with: id (UUID PK), nombre, configuracion (JSONB), activo, created_at, updated_at
- Creates `usuarios` table with all columns from E4 model definition
- All PII columns use `TEXT` as the storage type (they hold base64-encoded encrypted data)
- `email_hash` column for deterministic lookup (SHA-256)
- Indexes: PK on id, unique `(tenant_id, email_hash)`, FK `tenant_id → tenants.id`, FK `created_by → usuarios.id` (nullable)
- Upgrade and downgrade functions

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| **R1: Key rotation** — If `ENCRYPTION_KEY` changes, all encrypted data becomes unreadable. | Document explicitly that `ENCRYPTION_KEY` is immutable once data exists. The security module will log a clear error if decryption fails. Key rotation is a separate feature not in scope. |
| **R2: Encrypted field query performance** — Filtering on encrypted fields (email, dni) is impossible. | Solved via `email_hash` for email lookups. Other fields (dni, cuil) are rarely queried directly — they're displayed after loading by id. |
| **R3: TypeDecorator transparency can hide crypto failures** — If encryption silently fails, data is stored in plaintext. | The `EncryptedString` TypeDecorator raises a clear exception if `aes_encrypt` returns empty or raises. Unit tests verify the roundtrip. |
| **R4: Seed script runs outside Alembic** — seed is not automatically versioned with the schema. | The seed script checks the schema version before running. It's a documented manual step after running migrations: `python -m app.seeds.seed_001`. |
| **R5: Estado enum as string** — Stored as string in the DB, not a native PostgreSQL enum. | PostgreSQL enums are painful to alter in migrations. A string column with a Python enum on the ORM layer gives us flexibility at the cost of one layer of validation. Application code enforces valid values. |

## Migration Plan

**Step-by-step deployment:**

1. **Schema changes:**
   ```bash
   cd backend
   alembic upgrade head
   ```
   This runs migration 001, creating `tenants` and `usuarios` tables.

2. **Seed data:**
   ```bash
   python -m app.seeds.seed_001
   ```
   Inserts TUPAD tenant + ADMIN user if they don't exist.

3. **Rollback:**
   ```bash
   alembic downgrade -1
   ```
   Drops both tables (destructive — removes all data).

4. **Environment:** Add `ENCRYPTION_KEY` with a 32-char value to `.env`. Example from `.env.example`:
   ```
   ENCRYPTION_KEY=0123456789abcdef0123456789abcdef
   ```

## Open Questions

1. **ADR-002 confirmed**: Row-level multi-tenancy with `tenant_id` column — confirmed from the ARCHITECTURE.md. No changes needed.

2. **UUID strategy**: UUIDs are stored as `UUID(as_uuid=False)` — strings. This is already the pattern in `AppModel`. Keep it for SQLAlchemy simplicity. No open question.

3. **Encrypted field length**: PII fields (email, dni, cuil, cbu, alias_cbu) are stored as `TEXT` in PostgreSQL because AES-GCM output is variable-length and larger than the input. No constraint on the stored column — validation happens at the schema (Pydantic) layer.
