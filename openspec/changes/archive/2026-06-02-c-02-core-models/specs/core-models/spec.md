## ADDED Requirements

### Requirement: The system SHALL provide composable model mixins for common entity patterns

The system MUST provide a set of composable SQLAlchemy mixins that encapsulate recurring entity patterns. All domain models MUST inherit from `AppModel` (the DeclarativeBase providing UUID `id` and automatic snake_case tablename). Domain models MUST compose additional mixins as needed.

#### Scenario: TimestampMixin provides created_at and updated_at
- **WHEN** a model class inherits from `TimestampMixin`
- **THEN** the resulting table SHALL have non-nullable columns `created_at` and `updated_at` of type `DateTime(timezone=True)`
- **THEN** `created_at` SHALL default to `func.now()` on insert
- **THEN** `updated_at` SHALL update to `func.now()` on every row update

#### Scenario: AuditMixin provides estado and soft-delete
- **WHEN** a model class inherits from `AuditMixin`
- **THEN** the resulting table SHALL have a column `estado` of type `String(20)` with default `'Activo'`
- **THEN** the resulting table SHALL have a nullable column `deleted_at` of type `DateTime(timezone=True)` defaulting to `None`
- **THEN** soft-deleting a row MUST set `estado = 'Inactivo'` and `deleted_at = now()`

#### Scenario: TenantMixin provides tenant_id foreign key
- **WHEN** a domain model class inherits from `TenantMixin`
- **THEN** the resulting table SHALL have a column `tenant_id` of type `UUID` (as string) referencing `tenants.id` with `ON DELETE CASCADE`
- **THEN** for domain models (not `Tenant` itself), the `tenant_id` column MUST be non-nullable

### Requirement: The system SHALL have a Tenant model as the multi-tenant root entity

The system MUST provide a `Tenant` SQLAlchemy model representing an institution. Every other entity in the system references a tenant. The model MUST have the following attributes:

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `nombre` | String(255) | NOT NULL |
| `configuracion` | JSONB | NOT NULL, default `{}` |
| `activo` | Boolean | NOT NULL, default `True` |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

#### Scenario: Create Tenant with minimal fields
- **WHEN** a new Tenant is created with `nombre='TUPAD'`
- **THEN** the tenant SHALL have an auto-generated UUID `id`
- **THEN** the tenant SHALL have `configuracion` defaulting to `{}`
- **THEN** the tenant SHALL have `activo` defaulting to `True`

#### Scenario: List all active tenants
- **WHEN** querying all tenants with `estado=Activo`
- **THEN** only tenants with `activo=True` SHALL be returned

### Requirement: The system SHALL have a Usuario model with encrypted PII fields

The system MUST provide a `Usuario` SQLAlchemy model representing a person (natural person) who interacts with the system. The model inherits from `AppModel`, `TimestampMixin`, `AuditMixin`, and `TenantMixin`.

| Attribute | Type | Constraints | Encrypted |
|-----------|------|-------------|-----------|
| `id` | UUID (string) | PK | No |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL | No |
| `nombre` | String(100) | NOT NULL | No |
| `apellidos` | String(100) | NOT NULL | No |
| `email` | `EncryptedString` | Unique per tenant | **Yes** (AES-256-GCM) |
| `email_hash` | String(64) | NOT NULL, unique per tenant, SHA-256(plaintext email) | No |
| `dni` | `EncryptedString` | Nullable | **Yes** |
| `cuil` | `EncryptedString` | Nullable | **Yes** |
| `cbu` | `EncryptedString` | Nullable | **Yes** |
| `alias_cbu` | `EncryptedString` | Nullable | **Yes** |
| `banco` | String(100) | Nullable | No |
| `regional` | String(100) | Nullable | No |
| `legajo` | String(50) | Nullable | No |
| `legajo_profesional` | String(50) | Nullable | No |
| `facturador` | Boolean | NOT NULL, default `False` | No |
| `estado` | String(20) | Default `'Activo'` | No |

Encrypted fields MUST be stored as `TEXT` columns in PostgreSQL (they hold base64-encoded nonce + ciphertext + tag).

#### Scenario: Create Usuario with PII
- **WHEN** a Usuario is created with `email='admin@tupad.edu.ar'`, `nombre='Admin'`, `apellidos='Sistema'`
- **THEN** the `email` column SHALL contain the AES-256-GCM encrypted value (not plaintext)
- **THEN** the `email_hash` column SHALL contain the SHA-256 hex digest of `'admin@tupad.edu.ar'`
- **THEN** reading the Usuario back SHALL return the original plaintext `email`

#### Scenario: Find Usuario by email hash for login
- **WHEN** the system needs to find a user by email during login
- **THEN** it MUST compute SHA-256(plaintext_email) and query the `email_hash` column
- **THEN** the system MUST NOT query the encrypted `email` column directly

#### Scenario: Soft-delete Usuario
- **WHEN** a Usuario is soft-deleted
- **THEN** `estado` MUST be set to `'Inactivo'`
- **THEN** `deleted_at` MUST be set to the current timestamp
- **THEN** the record MUST NOT appear in default list queries

#### Scenario: Unique email constraint per tenant
- **WHEN** two usuarios are created with the same `email_hash` within the same `tenant_id`
- **THEN** the second insert MUST fail with a unique constraint violation
- **WHEN** two usuarios have the same `email_hash` in different tenants
- **THEN** both inserts MUST succeed
