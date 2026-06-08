# Calificaciones

> **Purpose**: Define the grade import, threshold configuration, listing, and scoped deletion system for subject activities. Provides import from .xlsx/.csv with activity detection preview, configurable approval thresholds per (assignment x subject), and scope-isolated data clearing.

---

## ADDED Requirements

### Requirement: The system SHALL have a Calificacion model for activity grades

The system MUST provide a `Calificacion` SQLAlchemy model that represents a grade or status for a student on an evaluable activity within a subject. The model links to an `EntradaPadron` (from padron-alumnos) to identify the student.

The model MUST inherit from `AppModel`, `TimestampMixin`, and `TenantMixin`.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `entrada_padron_id` | UUID (string) | FK -> entradas_padron.id, NOT NULL |
| `materia_id` | UUID (string) | FK -> materias.id, NOT NULL |
| `actividad` | String(200) | NOT NULL, name of the evaluable activity |
| `nota_numerica` | Numeric(5,2) | Nullable, numeric grade value |
| `nota_textual` | String(100) | Nullable, qualitative grade (e.g., "Satisfactorio") |
| `aprobado` | Boolean | NOT NULL, derived at import time (see RN-03/RN-02 rules) |
| `origen` | Enum('Importado', 'Manual') | NOT NULL, default 'Importado' |
| `cargado_por` | UUID (string) | FK -> usuarios.id, NOT NULL, who imported this grade |
| `importado_at` | DateTime(tz) | server default now() |

#### Scenario: Create Calificacion with numeric grade
- **WHEN** a Calificacion is created with `nota_numerica=75.50`, `entrada_padron_id=EP1`, `materia_id=M1`, `actividad="TP 1"`
- **THEN** the record SHALL be persisted with an auto-generated UUID `id`
- **THEN** `importado_at` SHALL default to the current timestamp
- **THEN** `origen` SHALL default to `'Importado'`

#### Scenario: Create Calificacion with textual grade
- **WHEN** a Calificacion is created with `nota_textual="Satisfactorio"`, no `nota_numerica`
- **THEN** `nota_numerica` SHALL be `NULL`
- **THEN** the record SHALL still be persisted successfully

#### Scenario: Calificacion without any grade is invalid
- **WHEN** a Calificacion is created with both `nota_numerica=NULL` and `nota_textual=NULL`
- **THEN** the system SHALL raise a validation error (at least one grade field required)

#### Scenario: Cascade delete with EntradaPadron
- **WHEN** an EntradaPadron is deleted
- **THEN** all associated Calificacion records SHALL also be deleted (CASCADE)

### Requirement: The system SHALL have an UmbralMateria model for configurable approval thresholds

The system MUST provide an `UmbralMateria` SQLAlchemy model representing the approval threshold configuration for a specific (asignacion x materia) pair.

The model MUST inherit from `AppModel`, `TimestampMixin`, and `TenantMixin`.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `asignacion_id` | UUID (string) | FK -> asignaciones.id, NOT NULL |
| `materia_id` | UUID (string) | FK -> materias.id, NOT NULL |
| `umbral_pct` | Integer | NOT NULL, default 60, min 0, max 100 |
| `valores_aprobatorios` | JSONB | NOT NULL, default `["Satisfactorio", "Supera lo esperado"]` |

#### Scenario: Create threshold with defaults
- **WHEN** an UmbralMateria is created with only `asignacion_id` and `materia_id`
- **THEN** `umbral_pct` SHALL default to `60`
- **THEN** `valores_aprobatorios` SHALL default to `["Satisfactorio", "Supera lo esperado"]`

#### Scenario: Create threshold with custom values
- **WHEN** an UmbralMateria is created with `umbral_pct=70` and `valores_aprobatorios=["Aprobado", "Promocionado"]`
- **THEN** the custom values SHALL be persisted

#### Scenario: Only one threshold per (asignacion x materia)
- **WHEN** creating a second UmbralMateria for the same `(asignacion_id, materia_id)`
- **THEN** the system SHALL upsert (replace the existing one)

#### Scenario: Threshold validation
- **WHEN** an UmbralMateria is created with `umbral_pct=-1`
- **THEN** the system SHALL reject with validation error
- **WHEN** an UmbralMateria is created with `umbral_pct=101`
- **THEN** the system SHALL reject with validation error

### Requirement: The system SHALL derive `aprobado` at import time

The `aprobado` field on Calificacion SHALL be derived at the moment of import according to RN-03 and RN-02 rules:

1. If `nota_numerica` is present: compare against the configured threshold for the user's assignment in this materia (default 60%). If `nota_numerica >= umbral_pct`, then `aprobado = True`.
2. If only `nota_textual` is present: evaluate against the configured `valores_aprobatorios` list. If `nota_textual` is in the list, then `aprobado = True`.

#### Scenario: Numeric grade above threshold
- **WHEN** a Calificacion has `nota_numerica=75.00` and the threshold is `60`
- **THEN** `aprobado` SHALL be `True`

#### Scenario: Numeric grade below threshold
- **WHEN** a Calificacion has `nota_numerica=45.00` and the threshold is `60`
- **THEN** `aprobado` SHALL be `False`

#### Scenario: Textual grade in approved values
- **WHEN** a Calificacion has `nota_textual="Satisfactorio"` and `valores_aprobatorios=["Satisfactorio", "Supera lo esperado"]`
- **THEN** `aprobado` SHALL be `True`

#### Scenario: Textual grade not in approved values
- **WHEN** a Calificacion has `nota_textual="No satisfactorio"`
- **THEN** `aprobado` SHALL be `False`

### Requirement: The system SHALL provide POST /api/materias/{id}/calificaciones/importar to import grades

The system MUST provide an endpoint to upload an .xlsx or .csv file containing grades for a subject. The endpoint SHALL support two modes via the `preview` query parameter:

1. **Preview mode** (`?preview=true`): Parse the file, detect activities and columns, return metadata without persisting any data.
2. **Confirm mode** (`?preview=false` or omitted): Parse the file, filter by selected activities, derive `aprobado` for each student, persist atomically.

The process SHALL be transactional in confirm mode: if any part fails, the entire import SHALL roll back.

#### Scenario: Preview returns detected activities
- **WHEN** a PROFESOR uploads a valid .xlsx file with columns `"TP 1 (Real)"`, `"TP 1"`, `"TP 2"` with `?preview=true`
- **THEN** the response SHALL include detected activities with type info
- **THEN** the response SHALL NOT persist any data
- **THEN** `"TP 1 (Real)"` SHALL be detected as numeric column, activity name `"TP 1"`
- **THEN** `"TP 1"` SHALL be detected as textual column, same activity `"TP 1"` (numeric takes priority)
- **THEN** `"TP 2"` SHALL be detected as textual column

#### Scenario: Confirm import with selected activities
- **WHEN** the user calls the same endpoint with `actividades_seleccionadas=["TP 1"]` and `?preview=false`
- **THEN** the system SHALL persist Calificacion records only for activity `"TP 1"`
- **THEN** the response SHALL include `{ "total_importados": N, "actividades": ["TP 1"] }`

#### Scenario: Import with .csv (comma delimiter)
- **WHEN** a .csv file with comma delimiter and headers `TP 1 (Real);TP 2` is uploaded
- **THEN** the system SHALL parse columns correctly with semicolon fallback detection
- **THEN** Calificacion records SHALL be created for each row

#### Scenario: Import with unsupported file format
- **WHEN** a file with extension other than .xlsx or .csv is uploaded
- **THEN** the endpoint SHALL return `400` with message "Formato de archivo no soportado. Use .xlsx o .csv"

#### Scenario: Permission denied for non-authorized user
- **WHEN** a PROFESOR who is NOT assigned to `materia_id=M1` attempts to import
- **THEN** the endpoint SHALL return `403`
- **THEN** no Calificacion records SHALL be created

#### Scenario: COORDINADOR imports for any materia
- **WHEN** a COORDINADOR uploads a valid grades file for any materia in the tenant
- **THEN** the import SHALL succeed as if they were the assigned PROFESOR

#### Scenario: Import without activities detected
- **WHEN** the uploaded file has no recognizable grade columns (no column ending in `(Real)` and no textual column headers)
- **THEN** the endpoint SHALL return `400` with a descriptive error message

#### Scenario: Empty activities_seleccionadas in confirm mode
- **WHEN** the user sends `actividades_seleccionadas=[]` in confirm mode
- **THEN** the endpoint SHALL return `400` with message "Debe seleccionar al menos una actividad"

### Requirement: The system SHALL provide GET /api/materias/{id}/calificaciones to list grades

The system MUST provide an endpoint to retrieve all Calificacion records for a subject. The results SHALL be filterable by optional query parameters.

#### Scenario: List all grades for a materia
- **WHEN** a PROFESOR assigned to `materia_id=M1` calls GET /api/materias/{id}/calificaciones
- **THEN** the response SHALL include all Calificacion records for that materia
- **THEN** each record SHALL include `id`, `entrada_padron_id`, `actividad`, `nota_numerica`, `nota_textual`, `aprobado`, `origen`, `importado_at`

#### Scenario: No grades imported yet
- **WHEN** no Calificacion records exist for the requested materia
- **THEN** the response SHALL return `200` with `{ "items": [], "total": 0 }`

#### Scenario: Filter by activity
- **WHEN** GET /api/materias/{id}/calificaciones?actividad=TP+1
- **THEN** the response SHALL only include records for activity "TP 1"

#### Scenario: Filter by approval status
- **WHEN** GET /api/materias/{id}/calificaciones?aprobado=true
- **THEN** the response SHALL only include records with `aprobado=True`

### Requirement: The system SHALL provide DELETE /api/materias/{id}/calificaciones to clear grades (scope-isolated)

The system MUST provide an endpoint to delete Calificacion records for a subject. The deletion scope follows RN-04:

- For PROFESOR: deletes only records where `cargado_por` matches the current user.
- For COORDINADOR: deletes all records for the materia.

#### Scenario: PROFESOR clears own grades
- **WHEN** a PROFESOR calls DELETE for a materia where they have imported grades
- **THEN** only Calificacion records with `cargado_por` matching the PROFESOR's user ID SHALL be deleted
- **THEN** grades imported by other users for the same materia SHALL NOT be affected

#### Scenario: COORDINADOR clears all grades for a materia
- **WHEN** a COORDINADOR calls DELETE for any materia
- **THEN** ALL Calificacion records for that materia SHALL be deleted (regardless of `cargado_por`)

#### Scenario: Delete requires confirmation
- **WHEN** DELETE is called without confirmation header/parameter
- **THEN** the endpoint SHALL require an explicit confirmation (query param `?confirmar=true`)
- **THEN** without confirmation, SHALL return `400` with message "Debe confirmar la operacion"

#### Scenario: Permission denied for non-authorized user
- **WHEN** a PROFESOR not assigned to the materia attempts to delete
- **THEN** the endpoint SHALL return `403`

### Requirement: The system SHALL provide POST /api/materias/{id}/calificaciones/umbral to configure threshold

The system MUST provide an endpoint to create or update the UmbralMateria for the current user's assignment in a subject.

#### Scenario: Create threshold
- **WHEN** a PROFESOR sends `{ "umbral_pct": 70 }` for an assigned materia
- **THEN** an UmbralMateria record SHALL be created with `umbral_pct=70`

#### Scenario: Update existing threshold
- **WHEN** the same PROFESOR sends `{ "umbral_pct": 65 }` for the same materia
- **THEN** the existing UmbralMateria record SHALL be updated (upsert behavior)

#### Scenario: Set custom approved values
- **WHEN** a PROFESOR sends `{ "valores_aprobatorios": ["Aprobado", "Excelente"] }`
- **THEN** the UmbralMateria SHALL store the custom values
- **THEN** future grade imports SHALL use these values for textual approval evaluation

#### Scenario: Permission denied
- **WHEN** a PROFESOR not assigned to the materia attempts to configure threshold
- **THEN** the endpoint SHALL return `403`

### Requirement: The system SHALL provide GET /api/materias/{id}/calificaciones/umbral to read threshold

The system MUST provide an endpoint to retrieve the current UmbralMateria configuration for the user's assignment in a subject.

#### Scenario: Get configured threshold
- **WHEN** a PROFESOR with an existing UmbralMateria calls GET threshold
- **THEN** the response SHALL include `umbral_pct` and `valores_aprobatorios`

#### Scenario: Get default threshold when not configured
- **WHEN** a PROFESOR without an UmbralMateria calls GET threshold
- **THEN** the response SHALL return `{ "umbral_pct": 60, "valores_aprobatorios": ["Satisfactorio", "Supera lo esperado"] }` (defaults)

### Requirement: The import operation SHALL be audited

When grades are imported (confirm mode), the system SHALL register an audit log entry with action code `CALIFICACIONES_IMPORTAR`.

#### Scenario: Audit log on successful import
- **WHEN** a grade import in confirm mode succeeds
- **THEN** an AuditLog record SHALL be created with `accion='CALIFICACIONES_IMPORTAR'`
- **THEN** the audit record SHALL include `actor_id`, `materia_id`, `filas_afectadas=N`

#### Scenario: No audit log on preview mode
- **WHEN** a grade import in preview mode is requested
- **THEN** NO AuditLog record SHALL be created
