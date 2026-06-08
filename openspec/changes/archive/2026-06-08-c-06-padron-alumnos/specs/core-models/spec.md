# Core Models — Delta Spec

> **Purpose**: Add VersionPadron and EntradaPadron models to the core domain model catalog, establishing the padron-alumnos capability as a first-class domain entity at the model layer.

---

## ADDED Requirements

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
