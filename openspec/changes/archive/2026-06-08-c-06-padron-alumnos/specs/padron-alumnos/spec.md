# Padron de Alumnos

> **Purpose**: Define the versioned student roster (padron) system for each subject. Provides import from .xlsx/.csv, versioned history with destructive upsert semantics, and query of active entries.

---

## ADDED Requirements

### Requirement: The system SHALL have a VersionPadron model for versioned student rosters

The system MUST provide a `VersionPadron` SQLAlchemy model that represents a version of the student roster for a specific subject and cohort. Only one version can be active per `(materia_id, cohorte_id)` at any time.

The model MUST inherit from `AppModel`, `TimestampMixin`, and `TenantMixin`.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `materia_id` | UUID (string) | FK -> materias.id, NOT NULL |
| `cohorte_id` | UUID (string) | FK -> cohortes.id, NOT NULL |
| `cargado_por` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `cargado_at` | DateTime(tz) | server default now() |
| `activa` | Boolean | NOT NULL, default `True` |

#### Scenario: Create new active version
- **WHEN** a new VersionPadron is created with `materia_id=M1`, `cohorte_id=C1`, `activa=True`
- **THEN** the version SHALL be persisted with an auto-generated UUID `id`
- **THEN** `cargado_at` SHALL default to the current timestamp
- **THEN** the previous active version for `(M1, C1)` SHALL have `activa=False`

#### Scenario: Only one active version per materia+cohorte
- **WHEN** two VersionPadron records exist for `(M1, C1)` with `activa=True`
- **THEN** the system MUST enforce that at most one is active at any time (application-level constraint in service)

#### Scenario: List versions in descending order
- **WHEN** querying versions for a materia
- **THEN** results SHALL be ordered by `cargado_at` descending (newest first)

### Requirement: The system SHALL have an EntradaPadron model for individual student entries

The system MUST provide an `EntradaPadron` SQLAlchemy model representing a single student entry within a version of the roster. The model links to a version and optionally to an existing user account.

The model MUST inherit from `AppModel`, `TimestampMixin`, and `TenantMixin`.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `version_id` | UUID (string) | FK -> versiones_padron.id, NOT NULL |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `usuario_id` | UUID (string) | FK -> usuarios.id, Nullable |
| `nombre` | String(100) | NOT NULL |
| `apellidos` | String(100) | NOT NULL |
| `email` | `EncryptedString` (TEXT) | NOT NULL, AES-256-GCM encrypted |
| `comision` | String(50) | Nullable |
| `regional` | String(100) | Nullable |

#### Scenario: Create EntradaPadron with email encrypted
- **WHEN** an EntradaPadron is created with `email='alumno@example.com'`
- **THEN** the `email` column SHALL contain the AES-256-GCM encrypted value (not plaintext)
- **THEN** reading the EntradaPadron back SHALL return the original plaintext `email`

#### Scenario: EntradaPadron without linked user
- **WHEN** an EntradaPadron is created without setting `usuario_id`
- **THEN** the column SHALL be `NULL`
- **THEN** the entry SHALL still be queryable and visible in the active roster

#### Scenario: EntradaPadron with linked user
- **WHEN** an EntradaPadron is created with `usuario_id=UUID`
- **THEN** the entry SHALL be associated to that user for future cross-referencing (e.g., calificaciones)

#### Scenario: Cascade delete with version
- **WHEN** a VersionPadron is deleted (if supported)
- **THEN** all associated EntradaPadron records SHALL also be deleted (CASCADE)

### Requirement: The system SHALL provide POST /api/materias/{id}/padron/importar to import student roster

The system MUST provide an endpoint to upload an .xlsx or .csv file containing student data for a subject. The import SHALL create a new VersionPadron, deactivate the previous active version, and create new EntradaPadron entries.

The process SHALL be transactional: if any part fails, the entire import SHALL roll back.

#### Scenario: Successful import with .xlsx
- **WHEN** a PROFESOR uploads a valid .xlsx file with columns `nombre`, `apellidos`, `email`, `comision` for `materia_id=M1`
- **THEN** a new VersionPadron SHALL be created with `activa=True`
- **THEN** the previous active version for `M1` SHALL have `activa=False`
- **THEN** EntradaPadron records SHALL be created for each row in the file
- **THEN** the response SHALL include `{ "version_id": "...", "total_importados": N }`

#### Scenario: Import with missing required column
- **WHEN** the uploaded file is missing the `nombre` or `email` column
- **THEN** the endpoint SHALL return `400` with a descriptive error message
- **THEN** no version or entries SHALL be created

#### Scenario: Import with empty file
- **WHEN** the uploaded .xlsx file contains only headers and no data rows
- **THEN** the endpoint SHALL return `400` with message "El archivo no contiene datos de alumnos"

#### Scenario: Import with .csv file (comma delimiter)
- **WHEN** a .csv file with comma delimiter and headers `nombre;apellidos;email;comision` is uploaded
- **THEN** the system SHALL parse columns correctly using `;` as delimiter (semicolon fallback detection)
- **THEN** EntradaPadron records SHALL be created for each row

#### Scenario: Import with unsupported file format
- **WHEN** a file with extension other than .xlsx or .csv is uploaded
- **THEN** the endpoint SHALL return `400` with message "Formato de archivo no soportado. Use .xlsx o .csv"

#### Scenario: Permission denied for non-authorized user
- **WHEN** a PROFESOR who is NOT assigned to `materia_id=M1` attempts to import
- **THEN** the endpoint SHALL return `403`
- **THEN** no version or entries SHALL be created

#### Scenario: COORDINADOR imports for any materia
- **WHEN** a COORDINADOR uploads a valid roster for any materia in the tenant
- **THEN** the import SHALL succeed as if they were the assigned PROFESOR

### Requirement: The system SHALL provide GET /api/materias/{id}/padron to list active entries

The system MUST provide an endpoint to retrieve all EntradaPadron entries belonging to the currently active VersionPadron for a subject.

#### Scenario: List active entries
- **WHEN** a PROFESOR assigned to `materia_id=M1` calls GET /api/materias/{id}/padron
- **THEN** the response SHALL include all EntradaPadron entries from the active VersionPadron
- **THEN** the response SHALL NOT include entries from inactive versions

#### Scenario: No padron loaded for materia
- **WHEN** no VersionPadron exists for the requested materia
- **THEN** the response SHALL return `200` with an empty list
- **THEN** the response SHALL include `{ "items": [], "total": 0 }`

### Requirement: The system SHALL provide GET /api/materias/{id}/padron/versiones to list version history

The system MUST provide an endpoint to retrieve all VersionPadron records for a subject, ordered by `cargado_at` descending.

#### Scenario: List version history
- **WHEN** querying version history for a materia with 3 versions
- **THEN** the response SHALL include all 3 versions ordered by `cargado_at` descending
- **THEN** each version entry SHALL include `id`, `cargado_at`, `cargado_por`, `activa`, `total_entradas`

#### Scenario: No versions exist
- **WHEN** no VersionPadron exists for the requested materia
- **THEN** the response SHALL return `200` with an empty list

### Requirement: The import operation SHALL be audited

When a new padron version is created via import, the system SHALL register an audit log entry with action code `PADRON_CARGAR`.

#### Scenario: Audit log on successful import
- **WHEN** a padron import succeeds
- **THEN** an AuditLog record SHALL be created with `accion='PADRON_CARGAR'`
- **THEN** the audit record SHALL include `actor_id`, `materia_id`, `filas_afectadas=N`
