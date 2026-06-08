# Core Models

> **Purpose**: Delta spec for C-03-auth-rbac. Adds auth-related fields to the `Usuario` model and introduces new domain models: `Rol`, `UsuarioRol`, `RefreshToken`, and `PasswordResetToken`.

---

## ADDED Requirements

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
