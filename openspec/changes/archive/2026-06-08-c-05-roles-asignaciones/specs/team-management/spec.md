## ADDED Requirements

### Requirement: The system SHALL provide the Asignacion model for user-role-context linking

The system MUST provide an `Asignacion` model that links a user (Usuario) to a role within an academic context (Materia, Carrera, Cohorte, Comisiones) with temporal validity. This is the central model for the teaching team management capability.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `usuario_id` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `rol` | String(20) | NOT NULL, values: PROFESOR, TUTOR, COORDINADOR, NEXO, ADMIN, FINANZAS |
| `materia_id` | UUID (string) | FK -> materias.id, nullable |
| `carrera_id` | UUID (string) | FK -> carreras.id, nullable |
| `cohorte_id` | UUID (string) | FK -> cohortes.id, nullable |
| `comisiones` | JSONB | NOT NULL, default `[]`, list of string identifiers |
| `responsable_id` | UUID (string) | FK -> usuarios.id, nullable (supervisor) |
| `vig_desde` | Date | NOT NULL, start of validity |
| `vig_hasta` | Date | Nullable, end of validity (null = indefinitely valid) |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Indexes:
- `ix_asignaciones_tenant_rol` on (tenant_id, rol)
- `ix_asignaciones_usuario_id` on (usuario_id)
- `ix_asignaciones_materia_id` on (materia_id)
- `ix_asignaciones_cohorte_id` on (cohorte_id)
- `ix_asignaciones_responsable_id` on (responsable_id)
- `ix_asignaciones_vigencia` on (tenant_id, vig_desde, vig_hasta)

#### Scenario: Create Asignacion with all required fields
- **WHEN** a POST request is sent to `/api/admin/asignaciones` with valid `usuario_id`, `rol='PROFESOR'`, `materia_id`, `carrera_id`, `cohorte_id`, `comisiones=['A','B']`, `vig_desde='2026-03-01'`, `vig_hasta='2026-12-31'`
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain `id`, `usuario_id`, `rol`, `materia_id`, `carrera_id`, `cohorte_id`, `comisiones`, `vig_desde`, `vig_hasta`, `estado_vigencia='Vigente'` (if today is within range), `created_at`, `updated_at`
- **THEN** `tenant_id` SHALL match the authenticated user's tenant

#### Scenario: Create Asignacion without vig_hasta (indefinite validity)
- **WHEN** a POST request is sent to `/api/admin/asignaciones` with `vig_hasta=null`
- **THEN** the response SHALL have status `201`
- **THEN** `vig_hasta` SHALL be null
- **THEN** `estado_vigencia` SHALL be `'Vigente'` (if today >= vig_desde)

#### Scenario: Create Asignacion with future vig_desde (pending validity)
- **WHEN** a POST request is sent to `/api/admin/asignaciones` with `vig_desde` in the future
- **THEN** the response SHALL have status `201`
- **THEN** `estado_vigencia` SHALL be `'Pendiente'`

#### Scenario: Create Asignacion with vig_desde after vig_hasta
- **WHEN** a POST request is sent to `/api/admin/asignaciones` with `vig_desde='2026-12-31'` and `vig_hasta='2026-03-01'`
- **THEN** the response SHALL have status `422`
- **THEN** the response SHALL contain a validation error for the date range

#### Scenario: Create Asignacion with responsable_id
- **WHEN** a POST request is sent to `/api/admin/asignaciones` with a valid `responsable_id` pointing to an existing Usuario in the same tenant
- **THEN** the response SHALL have status `201`
- **THEN** `responsable_id` SHALL be set to the provided UUID

#### Scenario: Create Asignacion referencing entity from another tenant
- **WHEN** a POST request is sent to `/api/admin/asignaciones` where `materia_id` (or `carrera_id`, `cohorte_id`, `responsable_id`) belongs to a different tenant
- **THEN** the response SHALL have status `404`

#### Scenario: Create Asignacion with invalid rol
- **WHEN** a POST request is sent to `/api/admin/asignaciones` with `rol='INVALIDO'`
- **THEN** the response SHALL have status `422`
- **THEN** the response SHALL contain a validation error for the rol field

### Requirement: The system SHALL provide GET individual and list for Asignaciones

The system MUST provide endpoints to retrieve individual assignments and list assignments with filters.

#### Scenario: Get single Asignacion by ID
- **WHEN** a GET request is sent to `/api/admin/asignaciones/{id}` with a valid assignment ID
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain the full assignment object with `estado_vigencia` computed

#### Scenario: Get Asignacion by ID from a different tenant
- **WHEN** a GET request is sent to `/api/admin/asignaciones/{id}` where the assignment belongs to a different tenant
- **THEN** the response SHALL have status `404`

#### Scenario: List Asignaciones with filters
- **WHEN** a GET request is sent to `/api/admin/asignaciones?usuario_id={id}&materia_id={id}&cohorte_id={id}&rol=PROFESOR`
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain only assignments matching ALL provided filters
- **THEN** each assignment SHALL include the computed `estado_vigencia` field

#### Scenario: List Asignaciones without filters
- **WHEN** a GET request is sent to `/api/admin/asignaciones`
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain all assignments for the current tenant

### Requirement: The system SHALL provide PUT update for Asignaciones

The system MUST allow partial updates to existing assignments.

#### Scenario: Update Asignacion vigencia dates
- **WHEN** a PUT request is sent to `/api/admin/asignaciones/{id}` with updated `vig_hasta='2027-03-01'`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL reflect the updated `vig_hasta`
- **THEN** `estado_vigencia` SHALL be recomputed based on the new dates

#### Scenario: Update Asignacion comisiones
- **WHEN** a PUT request is sent to `/api/admin/asignaciones/{id}` with updated `comisiones=['A','C','D']`
- **THEN** the response SHALL have status `200`
- **THEN** `comisiones` SHALL be updated to the new list

#### Scenario: Update Asignacion responsable_id
- **WHEN** a PUT request is sent to `/api/admin/asignaciones/{id}` with updated `responsable_id`
- **THEN** the response SHALL have status `200`
- **THEN** `responsable_id` SHALL be updated

#### Scenario: Update Asignacion not found
- **WHEN** a PUT request is sent to `/api/admin/asignaciones/{id}` with a non-existent ID
- **THEN** the response SHALL have status `404`

### Requirement: The system SHALL provide bulk assignment of docentes

The system MUST allow a COORDINADOR or ADMIN to assign multiple docentes to the same academic context in a single operation.

#### Scenario: Bulk assign multiple usuarios to same context
- **WHEN** a POST request is sent to `/api/admin/asignaciones/masiva` with `usuario_ids=['uuid1','uuid2','uuid3']`, `rol='TUTOR'`, `materia_id`, `carrera_id`, `cohorte_id`, `vig_desde='2026-03-01'`, `vig_hasta='2026-12-31'`
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain a list of 3 created assignments with their IDs
- **THEN** each assignment SHALL have the common parameters from the request

#### Scenario: Bulk assign with non-existent usuario_id
- **WHEN** a POST request is sent to `/api/admin/asignaciones/masiva` with one or more `usuario_ids` that do not exist in the current tenant
- **THEN** the response SHALL have status `404`
- **THEN** NO assignments SHALL be created (transaction rollback)

#### Scenario: Bulk assign with all params null for tenant-level role
- **WHEN** a POST request is sent to `/api/admin/asignaciones/masiva` with `usuario_ids=['uuid1']`, `rol='ADMIN'` and no academic context FKs
- **THEN** the response SHALL have status `201`
- **THEN** the assignment SHALL have null materia_id, carrera_id, cohorte_id

### Requirement: The system SHALL provide clone of equipo entre cohortes (RN-12)

The system MUST allow cloning all Vigente assignments from a source academic context to a destination context. This is the primary mechanism for reusing team configurations across academic periods.

#### Scenario: Clone equipo between two cohorts
- **WHEN** a POST request is sent to `/api/admin/asignaciones/clonar` with `origen_materia_id`, `origen_carrera_id`, `origen_cohorte_id` and `destino_materia_id`, `destino_carrera_id`, `destino_cohorte_id`
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain `clonadas` (count of cloned assignments)
- **THEN** for each cloned assignment, `usuario_id`, `rol`, `comisiones`, and `responsable_id` SHALL be preserved from the source
- **THEN** `vig_desde` and `vig_hasta` SHALL be set to the destination cohorte's vigencia dates

#### Scenario: Clone equipo with no source assignments
- **WHEN** a POST request is sent to `/api/admin/asignaciones/clonar` with a source context that has no Vigente assignments
- **THEN** the response SHALL have status `201`
- **THEN** `clonadas` SHALL be 0

#### Scenario: Clone equipo with identical source and destination
- **WHEN** a POST request is sent to `/api/admin/asignaciones/clonar` where source equals destination
- **THEN** the response SHALL have status `422`
- **THEN** the response SHALL contain a validation error indicating source and destination must differ

### Requirement: The system SHALL provide bulk vigencia modification

The system MUST allow updating validity dates for all assignments within an academic context in a single operation.

#### Scenario: Bulk update vigencia for an equipo
- **WHEN** a PUT request is sent to `/api/admin/asignaciones/vigencia` with `materia_id`, `carrera_id`, `cohorte_id`, `vig_desde='2026-03-01'`, `vig_hasta='2026-12-31'`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `actualizadas` (count of updated assignments)
- **THEN** all assignments matching the academic context SHALL have their vigencia dates updated

#### Scenario: Bulk update vigencia with no matching assignments
- **WHEN** a PUT request is sent to `/api/admin/asignaciones/vigencia` with a context that has no assignments
- **THEN** the response SHALL have status `200`
- **THEN** `actualizadas` SHALL be 0

### Requirement: The system SHALL provide equipo docente export

The system MUST allow exporting the teaching team for a given academic context as a downloadable CSV file.

#### Scenario: Export equipo as CSV
- **WHEN** a GET request is sent to `/api/admin/equipos/export?materia_id={id}&carrera_id={id}&cohorte_id={id}`
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL have `Content-Type: text/csv`
- **THEN** the response SHALL have `Content-Disposition: attachment`
- **THEN** the CSV body SHALL contain columns: docente_nombre, docente_apellidos, docente_email, rol, comisiones, responsable_nombre, vig_desde, vig_hasta, estado_vigencia

#### Scenario: Export equipo with no assignments
- **WHEN** a GET request is sent to `/api/admin/equipos/export` with a context that has no assignments
- **THEN** the response SHALL have status `200`
- **THEN** the CSV SHALL contain only the header row

#### Scenario: Export equipo without filters
- **WHEN** a GET request is sent to `/api/admin/equipos/export` without any filter parameters
- **THEN** the response SHALL have status `422`
- **THEN** the response SHALL require at least one filter parameter

### Requirement: The system SHALL compute estado_vigencia at query time

The `estado_vigencia` field is not stored in the database. It is derived at query time based on the current date and the vig_desde/vig_hasta fields.

Values:
- **Pendiente**: Current date < vig_desde
- **Vigente**: Current date is within [vig_desde, vig_hasta] OR [vig_desde, inf) if vig_hasta is NULL
- **Vencida**: Current date > vig_hasta

#### Scenario: Derived state is Vigente for current date within range
- **WHEN** today's date is `2026-06-07`, and an assignment has `vig_desde='2026-03-01'`, `vig_hasta='2026-12-31'`
- **THEN** `estado_vigencia` SHALL be `'Vigente'`

#### Scenario: Derived state is Vencida for past vig_hasta
- **WHEN** today's date is `2026-06-07`, and an assignment has `vig_desde='2025-03-01'`, `vig_hasta='2025-12-31'`
- **THEN** `estado_vigencia` SHALL be `'Vencida'`

#### Scenario: Derived state is Pendiente for future vig_desde
- **WHEN** today's date is `2026-06-07`, and an assignment has `vig_desde='2026-09-01'`, `vig_hasta='2027-03-01'`
- **THEN** `estado_vigencia` SHALL be `'Pendiente'`

#### Scenario: Derived state is Vigente for indefinite validity (null vig_hasta)
- **WHEN** today's date is `2026-06-07`, and an assignment has `vig_desde='2026-03-01'`, `vig_hasta=null`
- **THEN** `estado_vigencia` SHALL be `'Vigente'`

### Requirement: The system SHALL enforce multi-tenant isolation for Asignaciones

All assignment queries MUST be scoped to the current tenant. The `tenant_id` is resolved from the JWT, never from request parameters.

#### Scenario: Cross-tenant isolation on list
- **WHEN** two users from different tenants each list their asignaciones
- **THEN** each user SHALL only see asignaciones belonging to their own tenant
- **THEN** no assignment from tenant A SHALL appear in the response for tenant B

#### Scenario: Cross-tenant isolation on single entity access
- **WHEN** a user from tenant A requests an Asignacion belonging to tenant B
- **THEN** the response SHALL have status `404`

#### Scenario: Cross-tenant isolation on clone
- **WHEN** a clone request specifies a source or destination context that belongs to another tenant
- **THEN** the response SHALL have status `404`

### Requirement: The system SHALL enforce permission-based access

All Asignacion endpoints MUST be protected by the `equipo_docente:asignar` permission (for mutating operations) and `equipo_docente:ver` (for read operations).

#### Scenario: Unauthenticated request returns 401
- **WHEN** a request without a valid JWT is sent to any Asignacion endpoint
- **THEN** the response SHALL have status `401`

#### Scenario: User without equipo_docente:asignar returns 403
- **WHEN** a user without `equipo_docente:asignar` permission (e.g., PROFESOR) sends a POST, PUT request to an Asignacion endpoint
- **THEN** the response SHALL have status `403`

#### Scenario: User with equipo_docente:ver can read assignments
- **WHEN** a user with `equipo_docente:ver` permission (e.g., COORDINADOR) sends a GET request to `/api/admin/asignaciones`
- **THEN** the response SHALL have status `200`
- **THEN** the user SHALL see assignments scoped to their tenant

#### Scenario: User without equipo_docente:ver cannot read assignments
- **WHEN** a user without read permission (e.g., ALUMNO) sends a GET request to `/api/admin/asignaciones`
- **THEN** the response SHALL have status `403`
