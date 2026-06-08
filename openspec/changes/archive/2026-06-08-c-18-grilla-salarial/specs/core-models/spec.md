## ADDED Requirements

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
