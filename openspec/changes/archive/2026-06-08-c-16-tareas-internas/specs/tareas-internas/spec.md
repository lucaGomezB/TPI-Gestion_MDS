## ADDED Requirements

### Requirement: The system SHALL provide the Tarea model for internal task tracking

The system MUST provide a `Tarea` model representing an internal task assigned between teaching or coordination staff. Each task has a traceable lifecycle with explicit state transitions.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `materia_id` | UUID (string) | FK -> materias.id, nullable |
| `asignado_a` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `asignado_por` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `estado` | String(20) | NOT NULL, default 'Pendiente', values: Pendiente, En progreso, Resuelta, Cancelada |
| `descripcion` | Text | NOT NULL |
| `contexto_id` | UUID (string) | Nullable, reference to any domain entity |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Indexes:
- `ix_tareas_tenant_estado` on (tenant_id, estado)
- `ix_tareas_asignado_a` on (asignado_a)
- `ix_tareas_materia_id` on (materia_id)

#### Scenario: Create task as PROFESOR with valid data
- **WHEN** a POST request is sent to `/api/tareas` with valid body `{ "materia_id": "<uuid>", "asignado_a": "<uuid>", "descripcion": "Preparar informe de avance" }` by a user with `tareas:asignar` permission
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain `id`, `materia_id`, `asignado_a`, `asignado_por` (equals the authenticated user), `estado: "Pendiente"`, `descripcion`, `created_at`, `updated_at`

#### Scenario: Create task without tareas:asignar permission returns 403
- **WHEN** a POST request is sent to `/api/tareas` by a user without `tareas:asignar` permission
- **THEN** the response SHALL have status `403`

#### Scenario: Create task with invalid materia_id returns 422
- **WHEN** a POST request is sent to `/api/tareas` with a non-existent `materia_id`
- **THEN** the response SHALL have status `422`

#### Scenario: Create institutional task (materia_id = null) as COORDINADOR
- **WHEN** a POST request is sent to `/api/tareas` without `materia_id` (or null) by a user with COORDINADOR role
- **THEN** the response SHALL have status `201`
- **THEN** the response SHALL contain `materia_id: null`

### Requirement: The system SHALL provide task state transitions with forward-only flow

The system MUST enforce that task estado transitions follow this order: `Pendiente -> En progreso -> Resuelta`. Cancelada is allowed from any state. No backward transitions are permitted (e.g., Resuelta -> En progreso).

#### Scenario: Advance task from Pendiente to En progreso
- **WHEN** a PUT request is sent to `/api/tareas/{id}/estado` with `{ "estado": "En progreso" }` for a task currently in `Pendiente` state
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `estado: "En progreso"`

#### Scenario: Advance task from En progreso to Resuelta
- **WHEN** a PUT request is sent to `/api/tareas/{id}/estado` with `{ "estado": "Resuelta" }` for a task currently in `En progreso` state
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `estado: "Resuelta"`

#### Scenario: Cancel task from any state
- **WHEN** a PUT request is sent to `/api/tareas/{id}/estado` with `{ "estado": "Cancelada" }` for a task in any state
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `estado: "Cancelada"`

#### Scenario: Reject backward transition from Resuelta to En progreso
- **WHEN** a PUT request is sent to `/api/tareas/{id}/estado` with `{ "estado": "En progreso" }` for a task currently in `Resuelta` state
- **THEN** the response SHALL have status `422`
- **THEN** the response body SHALL contain a `detail` explaining the invalid transition

#### Scenario: Change state of non-existent task returns 404
- **WHEN** a PUT request is sent to `/api/tareas/{id}/estado` with a non-existent UUID
- **THEN** the response SHALL have status `404`

#### Scenario: Change state without tareas:admin and not being the asignado returns 403
- **WHEN** a PUT request is sent to `/api/tareas/{id}/estado` by a user who is NOT the `asignado_a` and does NOT have `tareas:admin` permission
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL provide the ComentarioTarea model for task comments

The system MUST provide a `ComentarioTarea` model for asynchronous comments on a task. Comments are immutable after creation (no edit, no delete).

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `tarea_id` | UUID (string) | FK -> tareas.id, NOT NULL |
| `autor_id` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `texto` | Text | NOT NULL |
| `creado_at` | DateTime(tz) | server default now() |

Indexes:
- `ix_comentarios_tarea_tarea_id` on (tarea_id)

#### Scenario: Add comment to existing task
- **WHEN** a POST request is sent to `/api/tareas/{id}/comentarios` with valid body `{ "texto": "Ya lo estoy revisando" }`
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain `id`, `tarea_id`, `autor_id`, `texto`, `creado_at`

#### Scenario: Add comment to non-existent task returns 404
- **WHEN** a POST request is sent to `/api/tareas/{id}/comentarios` with a non-existent task UUID
- **THEN** the response SHALL have status `404`

#### Scenario: Add empty comment returns 422
- **WHEN** a POST request is sent to `/api/tareas/{id}/comentarios` with `{ "texto": "" }`
- **THEN** the response SHALL have status `422`

### Requirement: The system SHALL provide a personal task list view for the authenticated user

The system MUST provide an endpoint that returns tasks assigned to the authenticated user (`asignado_a = current_user.id`).

#### Scenario: Get my tasks returns only assigned tasks
- **WHEN** a GET request is sent to `/api/tareas` by a user with `tareas:ver` permission
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain a paginated list of tasks where `asignado_a` equals the authenticated user's id
- **THEN** each task SHALL include `id`, `descripcion`, `estado`, `materia_id`, `asignado_por`, `created_at`, `updated_at` and the last comment text if any

#### Scenario: Get my tasks filtered by estado
- **WHEN** a GET request is sent to `/api/tareas?estado=Pendiente`
- **THEN** the response SHALL only include tasks with `estado: "Pendiente"`

#### Scenario: Get my tasks filtered by materia_id
- **WHEN** a GET request is sent to `/api/tareas?materia_id={uuid}`
- **THEN** the response SHALL only include tasks with the given `materia_id`

#### Scenario: Get my tasks without tareas:ver permission returns 403
- **WHEN** a GET request is sent to `/api/tareas` by a user without `tareas:ver` permission
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL provide a global admin task view for COORDINADOR and ADMIN

The system MUST provide an endpoint that returns all tasks across the tenant with filtering capabilities.

#### Scenario: View all tasks as COORDINADOR
- **WHEN** a GET request is sent to `/api/admin/tareas` by a user with COORDINADOR role and `tareas:admin` permission
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain a paginated list of tasks across all materias of the tenant
- **THEN** each task SHALL include `id`, `descripcion`, `estado`, `materia_id`, `asignado_a` (with user name), `asignado_por` (with user name), `created_at`, `updated_at`, and comment count

#### Scenario: Filter tasks by asignado_a
- **WHEN** a GET request is sent to `/api/admin/tareas?asignado_a={uuid}`
- **THEN** the response SHALL only include tasks assigned to the given user

#### Scenario: Filter tasks by asignado_por
- **WHEN** a GET request is sent to `/api/admin/tareas?asignado_por={uuid}`
- **THEN** the response SHALL only include tasks assigned by the given user

#### Scenario: Filter tasks by materia_id
- **WHEN** a GET request is sent to `/api/admin/tareas?materia_id={uuid}`
- **THEN** the response SHALL only include tasks for the given materia

#### Scenario: Filter tasks by estado
- **WHEN** a GET request is sent to `/api/admin/tareas?estado=Pendiente`
- **THEN** the response SHALL only include tasks with `estado: "Pendiente"`

#### Scenario: Free text search in tasks
- **WHEN** a GET request is sent to `/api/admin/tareas?q=informe`
- **THEN** the response SHALL only include tasks whose `descripcion` contains the search term (case-insensitive)

#### Scenario: Combined filters
- **WHEN** a GET request is sent to `/api/admin/tareas?estado=Pendiente&asignado_a={uuid}&q=informe`
- **THEN** the response SHALL apply all filters conjunctively

#### Scenario: View all tasks without tareas:admin permission returns 403
- **WHEN** a GET request is sent to `/api/admin/tareas` by a user without `tareas:admin` permission
- **THEN** the response SHALL have status `403`

## MODIFIED Requirements

### Requirement: The system SHALL manage the core data models (E1 through E21)

The core-models spec MUST be updated to include the following new models:

**ADDED E12 — Tarea interna**

A task assigned between teaching or coordination staff with lifecycle tracking.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID | PK, auto-generated |
| `tenant_id` | UUID | FK -> tenants.id, NOT NULL |
| `materia_id` | UUID | FK -> materias.id, nullable |
| `asignado_a` | UUID | FK -> usuarios.id, NOT NULL |
| `asignado_por` | UUID | FK -> usuarios.id, NOT NULL |
| `estado` | enum | Pendiente, En progreso, Resuelta, Cancelada |
| `descripcion` | text | NOT NULL |
| `contexto_id` | UUID | nullable, reference to any domain entity |

Relationships:
- Materia (1) <-> (N) Tarea
- Usuario (1) <-> (N) Tarea (asignado a)
- Usuario (1) <-> (N) Tarea (asignado por)
- Tarea (1) <-> (N) ComentarioTarea

**ADDED ComentarioTarea**

A comment on a task, authored by a user.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID | PK, auto-generated |
| `tenant_id` | UUID | FK -> tenants.id, NOT NULL |
| `tarea_id` | UUID | FK -> Tarea.id, NOT NULL |
| `autor_id` | UUID | FK -> Usuario.id, NOT NULL |
| `texto` | text | NOT NULL |
| `creado_at` | datetime | NOT NULL, server default |

Relationships:
- Tarea (1) <-> (N) ComentarioTarea
- Usuario (1) <-> (N) ComentarioTarea (autor)
