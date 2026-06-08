# Core Models

> **Purpose**: Define the foundational SQLAlchemy models, mixins, and patterns that all domain entities build upon. Establishes the multi-tenant base, audit trail semantics, and the Usuario identity model with encrypted PII.

---

## Requirements

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

---

### Requirement: Usuario SHALL have password_hash for Argon2id authentication

The `Usuario` model MUST gain a `password_hash` column for storing Argon2id password hashes. The column MUST be nullable initially to allow existing seed data to migrate without a password.

#### Scenario: Usuario with password set
- **WHEN** a Usuario is created with `password_hash='$argon2id$v=19$...'`
- **THEN** the `password_hash` column SHALL store the full Argon2id PHC string
- **THEN** reading it back SHALL return the same string

#### Scenario: Usuario without password
- **WHEN** a Usuario record is created without setting `password_hash`
- **THEN** the column SHALL be `NULL`
- **THEN** the user SHALL NOT be able to log in via password

### Requirement: Usuario SHALL support optional TOTP 2FA

The `Usuario` model MUST gain two columns for TOTP two-factor authentication.

| Column | Type | Constraints |
|--------|------|-------------|
| `totp_secret` | EncryptedString (TEXT) | Nullable, encrypted via AES-256-GCM |
| `totp_enabled` | Boolean | NOT NULL, default `False` |

#### Scenario: Enable TOTP on Usuario
- **WHEN** a Usuario has `totp_secret` set and `totp_enabled=True`
- **THEN** the login flow SHALL require a TOTP code after password verification
- **WHEN** `totp_enabled` is `False` (default)
- **THEN** the login flow SHALL skip TOTP verification

#### Scenario: TOTP secret encrypted at rest
- **WHEN** a `totp_secret` value is assigned to a Usuario
- **THEN** the stored column value SHALL be AES-256-GCM encrypted (via `EncryptedString`)

### Requirement: The system SHALL have a Rol model for the role catalog

The system MUST provide a `Rol` SQLAlchemy model representing a named role within a tenant. Each role groups a set of permissions (`modulo:accion` strings).

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL |
| `nombre` | String(50) | NOT NULL |
| `descripcion` | String(255) | Nullable |
| `permisos` | JSONB (list of strings) | NOT NULL, default `[]` |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Unique constraint on `(tenant_id, nombre)`.

#### Scenario: Create Rol with permissions
- **WHEN** a Rol is created with `nombre='ADMIN'`, `permisos=['usuario:gestionar', 'tenant:configurar']`
- **THEN** the rol SHALL be persisted with those attributes
- **THEN** a second rol with same `nombre` in the same tenant SHALL violate the unique constraint

### Requirement: The system SHALL have a UsuarioRol model for role assignments

The system MUST provide a `UsuarioRol` SQLAlchemy model that assigns a role to a user within a tenant, with optional temporal validity.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `usuario_id` | UUID (string) | FK → usuarios.id, NOT NULL |
| `rol_id` | UUID (string) | FK → roles.id, NOT NULL |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL |
| `vigencia_desde` | DateTime(tz) | Nullable |
| `vigencia_hasta` | DateTime(tz) | Nullable |
| `created_at` | DateTime(tz) | server default now() |

Unique constraint on `(usuario_id, rol_id)`.

#### Scenario: Assign role to user
- **WHEN** a UsuarioRol is created linking `usuario_id=A`, `rol_id=B`, `tenant_id=C`
- **THEN** the user A SHALL have the permissions of role B when computing effective permissions

#### Scenario: Role assignment with vigencia
- **WHEN** a UsuarioRol has `vigencia_desde` and `vigencia_hasta` set
- **THEN** the assignment SHALL be considered active only if `now()` falls between both dates (inclusive)

### Requirement: The system SHALL have a RefreshToken model for JWT refresh rotation

The system MUST provide a `RefreshToken` SQLAlchemy model that tracks issued refresh tokens and supports rotation with theft detection via token families.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `usuario_id` | UUID (string) | FK → usuarios.id, NOT NULL |
| `token_hash` | String(64) | NOT NULL, SHA-256 of the raw token |
| `expires_at` | DateTime(tz) | NOT NULL |
| `revoked_at` | DateTime(tz) | Nullable |
| `token_family` | UUID (string) | NOT NULL |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL |
| `created_at` | DateTime(tz) | server default now() |

Indexed on `token_hash` (for lookup) and `token_family` (for family-wide revocation).

#### Scenario: Create refresh token entry
- **WHEN** a new refresh token is issued
- **THEN** a RefreshToken record SHALL be created with the SHA-256 hash of the raw token
- **THEN** `token_family` SHALL be a new UUID (first token in family) or the existing family UUID (rotation)

#### Scenario: Revoke refresh token
- **WHEN** a refresh token is consumed during rotation
- **THEN** `revoked_at` SHALL be set to the current timestamp
- **THEN** the token SHALL NOT be usable for future refreshes

#### Scenario: Family-wide revocation on theft detection
- **WHEN** a refresh with a token whose `revoked_at` is NOT NULL is attempted
- **THEN** ALL tokens in the same `token_family` SHALL have `revoked_at` set to current timestamp

### Requirement: The system SHALL have a PasswordResetToken model

The system MUST provide a `PasswordResetToken` SQLAlchemy model for single-use password recovery tokens.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `usuario_id` | UUID (string) | FK → usuarios.id, NOT NULL |
| `token_hash` | String(64) | NOT NULL, SHA-256 of raw token |
| `expires_at` | DateTime(tz) | NOT NULL |
| `used_at` | DateTime(tz) | Nullable |
| `created_at` | DateTime(tz) | server default now() |

Indexed on `token_hash`.

#### Scenario: Create password reset token
- **WHEN** a forgot-password request is processed
- **THEN** a PasswordResetToken record SHALL be created with `token_hash=SHA-256(token)` and `expires_at=now()+1hour`

#### Scenario: Use password reset token
- **WHEN** a reset-password request succeeds
- **THEN** `used_at` SHALL be set to the current timestamp
- **THEN** the token SHALL NOT be usable again

#### Scenario: Expired token validation
- **WHEN** a reset-password request uses a token whose `expires_at` is in the past
- **THEN** the request SHALL be rejected with `400`

### Requirement: The system SHALL have a VersionPadron model for versioned student rosters

The system MUST provide a `VersionPadron` SQLAlchemy model representing a version of the student roster for a specific subject and cohort. The model inherits from `AppModel`, `TimestampMixin`, and `TenantMixin`.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `materia_id` | UUID (string) | FK -> materias.id, NOT NULL |
| `cohorte_id` | UUID (string) | FK -> cohortes.id, NOT NULL |
| `cargado_por` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `cargado_at` | DateTime(tz) | server default now() |
| `activa` | Boolean | NOT NULL, default `True` |

#### Scenario: VersionPadron inherits AppModel mixins
- **WHEN** a VersionPadron model class is defined
- **THEN** it SHALL have an auto-generated UUID `id` (from AppModel)
- **THEN** it SHALL have `created_at` and `updated_at` (from TimestampMixin)
- **THEN** it SHALL have a non-nullable `tenant_id` (from TenantMixin)

### Requirement: The system SHALL have an EntradaPadron model for individual student entries

The system MUST provide an `EntradaPadron` SQLAlchemy model representing a single student entry within a version of the roster. The model inherits from `AppModel`, `TimestampMixin`, and `TenantMixin`.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK |
| `version_id` | UUID (string) | FK -> versiones_padron.id, NOT NULL |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `usuario_id` | UUID (string) | FK -> usuarios.id, Nullable |
| `nombre` | String(100) | NOT NULL |
| `apellidos` | String(100) | NOT NULL |
| `email` | `EncryptedString` (TEXT) | NOT NULL |
| `comision` | String(50) | Nullable |
| `regional` | String(100) | Nullable |

#### Scenario: EntradaPadron inherits AppModel mixins
- **WHEN** an EntradaPadron model class is defined
- **THEN** it SHALL have an auto-generated UUID `id` (from AppModel)
- **THEN** it SHALL have `created_at` and `updated_at` (from TimestampMixin)
- **THEN** it SHALL have a non-nullable `tenant_id` (from TenantMixin)

#### Scenario: EntradaPadron email uses EncryptedString
- **WHEN** the `email` column is written to the database
- **THEN** it SHALL be transparently encrypted using the existing `EncryptedString` TypeDecorator (AES-256-GCM)

#### Scenario: EntradaPadron usuario_id is nullable
- **WHEN** an EntradaPadron is created without a linked user
- **THEN** `usuario_id` SHALL be `NULL`
- **THEN** the entry SHALL remain valid and queryable

### Requirement: The system SHALL have a SalarioBase model for per-role base salary

The system MUST provide a `SalarioBase` SQLAlchemy model (E17) inheriting from `AppModel`, `TimestampMixin`, and `TenantMixin`. It represents the base salary amount for a specific role with temporal validity.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `rol` | String(20) | NOT NULL, CHECK IN ('COORDINADOR','NEXO','PROFESOR','TUTOR') |
| `monto` | Numeric(12,2) | NOT NULL |
| `desde` | Date | NOT NULL |
| `hasta` | Date | Nullable |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Unique constraint on `(tenant_id, rol, desde)`.

#### Scenario: SalarioBase inherits AppModel mixins
- **WHEN** a SalarioBase model class is defined
- **THEN** it SHALL have an auto-generated UUID `id` (from AppModel)
- **THEN** it SHALL have `created_at` and `updated_at` (from TimestampMixin)
- **THEN** it SHALL have a non-nullable `tenant_id` (from TenantMixin)

#### Scenario: SalarioBase stores base amount for a role
- **WHEN** a SalarioBase is created with rol=PROFESOR, monto=150000.00, desde=2026-01-01
- **THEN** the record SHALL be persisted with those values
- **THEN** `hasta` SHALL default to `NULL` (open-ended)

#### Scenario: SalarioBase unique constraint on (tenant, rol, desde)
- **WHEN** two records are created with the same tenant_id, rol and desde
- **THEN** the second insert SHALL fail with a unique constraint violation

### Requirement: The system SHALL have a SalarioPlus model for bonus pay per group x role

The system MUST provide a `SalarioPlus` SQLAlchemy model (E18) inheriting from `AppModel`, `TimestampMixin`, and `TenantMixin`. It represents an additional bonus amount for a combination of subject group and role.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `grupo` | String(50) | NOT NULL |
| `rol` | String(20) | NOT NULL, CHECK IN ('COORDINADOR','NEXO','PROFESOR','TUTOR') |
| `descripcion` | String(255) | NOT NULL |
| `monto` | Numeric(12,2) | NOT NULL |
| `desde` | Date | NOT NULL |
| `hasta` | Date | Nullable |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Unique constraint on `(tenant_id, grupo, rol, desde)`.

#### Scenario: SalarioPlus inherits AppModel mixins
- **WHEN** a SalarioPlus model class is defined
- **THEN** it SHALL have an auto-generated UUID `id` (from AppModel)
- **THEN** it SHALL have `created_at` and `updated_at` (from TimestampMixin)
- **THEN** it SHALL have a non-nullable `tenant_id` (from TenantMixin)

#### Scenario: SalarioPlus stores bonus for group+rol
- **WHEN** a SalarioPlus is created with grupo=PROG, rol=PROFESOR, monto=5000.00, desde=2026-01-01
- **THEN** the record SHALL be persisted with those values
- **THEN** `hasta` SHALL default to `NULL`

#### Scenario: SalarioPlus unique constraint on (tenant, grupo, rol, desde)
- **WHEN** two records are created with the same tenant_id, grupo, rol and desde
- **THEN** the second insert SHALL fail with a unique constraint violation

### Requirement: The system SHALL have a GrupoMateria model for configurable subject groups

The system MUST provide a `GrupoMateria` SQLAlchemy model representing a group key that categorizes subjects (e.g., "PROG" for programming subjects). Groups are tenant-scoped and configurable.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `grupo` | String(20) | NOT NULL |
| `descripcion` | String(255) | Nullable |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Unique constraint on `(tenant_id, grupo)`.

#### Scenario: GrupoMateria minimal attributes
- **WHEN** a GrupoMateria is created with tenant_id and grupo='PROG'
- **THEN** the record SHALL be persisted with an auto-generated UUID `id`

#### Scenario: GrupoMateria unique constraint within tenant
- **WHEN** two GrupoMateria records are created with the same tenant_id and grupo key
- **THEN** the second insert SHALL fail with a unique constraint violation

#### Scenario: Different tenants can use same group key
- **WHEN** two GrupoMateria records are created in different tenants with the same grupo='PROG'
- **THEN** both inserts SHALL succeed

### Requirement: The system SHALL have a MateriaGrupo model for N:N relationship between subjects and groups

The system MUST provide a `MateriaGrupo` SQLAlchemy model representing the many-to-many relationship between subjects and subject groups. A subject can belong to multiple groups; a group can contain multiple subjects.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK |
| `materia_id` | UUID (string) | FK -> materias.id, NOT NULL |
| `grupo_id` | UUID (string) | FK -> grupos_materia.id, NOT NULL |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `created_at` | DateTime(tz) | server default now() |

Unique constraint on `(materia_id, grupo_id)`.

#### Scenario: MateriaGrupo creates subject-group association
- **WHEN** a MateriaGrupo record is created linking materia_id=X and grupo_id=Y
- **THEN** subject X SHALL be queryable as part of group Y
- **THEN** a second link between the same materia_id and grupo_id SHALL fail with unique constraint violation

#### Scenario: Query subjects by group id
- **WHEN** querying MateriaGrupo by grupo_id
- **THEN** the system SHALL return all materias associated with that group via joined query
