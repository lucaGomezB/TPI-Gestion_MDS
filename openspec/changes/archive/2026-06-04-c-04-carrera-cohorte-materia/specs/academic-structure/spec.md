## ADDED Requirements

### Requirement: The system SHALL provide CRUD for Carrera (academic programs)

The system MUST provide a `Carrera` model and REST endpoints to manage academic programs within a tenant. Each tenant has its own catalog of carreras with unique program codes.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL |
| `codigo` | String(20) | NOT NULL, uppercase alphanumeric with underscores |
| `nombre` | String(255) | NOT NULL |
| `estado` | String(20) | NOT NULL, default `'Activa'` values `Activa`/`Inactiva` |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Unique constraint on `(tenant_id, codigo)`.

#### Scenario: Create Carrera with minimal required fields
- **WHEN** a POST request is sent to `/api/admin/carreras` with valid `codigo='TUPAD'` and `nombre='Tecnicatura Universitaria en Programación y Análisis de Datos'`
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain `id`, `codigo`, `nombre`, `estado='Activa'`, `tenant_id`, `created_at`, `updated_at`

#### Scenario: Create Carrera with duplicate codigo in same tenant
- **WHEN** a POST request is sent to `/api/admin/carreras` with `codigo='TUPAD'` that already exists in the same tenant
- **THEN** the response SHALL have status `409`
- **THEN** the response SHALL contain `detail: "A carrera with codigo 'TUPAD' already exists in this tenant"`

#### Scenario: Create Carrera with same codigo in different tenant
- **WHEN** two POST requests are sent from different tenants, each with the same `codigo='TUPAD'`
- **THEN** both requests SHALL succeed with status `201`
- **THEN** each carrera SHALL be scoped to its respective tenant

#### Scenario: List all carreras for the tenant
- **WHEN** a GET request is sent to `/api/admin/carreras` from an authenticated ADMIN user
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain a list of carreras belonging to the current tenant only

#### Scenario: Get single Carrera by ID
- **WHEN** a GET request is sent to `/api/admin/carreras/{id}` with a valid carrera ID
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain the full carrera object

#### Scenario: Get Carrera by ID from a different tenant
- **WHEN** a GET request is sent to `/api/admin/carreras/{id}` where the carrera belongs to a different tenant
- **THEN** the response SHALL have status `404`

#### Scenario: Update Carrera nombre and estado
- **WHEN** a PUT request is sent to `/api/admin/carreras/{id}` with updated `nombre` and `estado='Inactiva'`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL reflect the updated values

#### Scenario: Update Carrera codigo to an existing one
- **WHEN** a PUT request is sent to `/api/admin/carreras/{id}` with a `codigo` that already belongs to another carrera in the same tenant
- **THEN** the response SHALL have status `409`

#### Scenario: Unauthenticated request for Carrera endpoints
- **WHEN** a request without a valid JWT is sent to any Carrera endpoint
- **THEN** the response SHALL have status `401`

#### Scenario: Non-admin user requests Carrera endpoints
- **WHEN** a user without `estructura_academica:gestionar` permission (e.g., PROFESOR) sends a request to any Carrera endpoint
- **THEN** the response SHALL have status `403`
- **THEN** the response SHALL contain `detail: "Not enough permissions"`

### Requirement: The system SHALL provide CRUD for Cohorte (cohorts)

The system MUST provide a `Cohorte` model and REST endpoints to manage cohorts within a carrera. Each cohort belongs to exactly one carrera.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL |
| `carrera_id` | UUID (string) | FK → carreras.id, NOT NULL |
| `nombre` | String(100) | NOT NULL, e.g. `'MAR-2025'`, `'AGO-2026'` |
| `anio` | Integer | NOT NULL |
| `vig_desde` | Date | NOT NULL |
| `vig_hasta` | Date | Nullable |
| `estado` | String(20) | NOT NULL, default `'Activa'` |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Unique constraint on `(tenant_id, carrera_id, nombre)`.

#### Scenario: Create Cohorte with required fields
- **WHEN** a POST request is sent to `/api/admin/cohortes` with valid `carrera_id`, `nombre='MAR-2025'`, `anio=2025`, `vig_desde='2025-03-01'`
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain `id`, `nombre`, `anio`, `vig_desde`, `vig_hasta=null`, `estado='Activa'`, `tenant_id`, `carrera_id`

#### Scenario: Create Cohorte with vig_hasta (closed cohort)
- **WHEN** a POST request is sent to `/api/admin/cohortes` with `vig_desde='2024-03-01'` and `vig_hasta='2025-02-28'`
- **THEN** the response SHALL have status `201`
- **THEN** `vig_hasta` SHALL be set to the provided date

#### Scenario: Create Cohorte with duplicate nombre in same carrera and tenant
- **WHEN** a POST request is sent to `/api/admin/cohortes` with a `nombre` that already exists in the same carrera and tenant
- **THEN** the response SHALL have status `409`

#### Scenario: Create Cohorte referencing a carrera from another tenant
- **WHEN** a POST request is sent to `/api/admin/cohortes` where the `carrera_id` belongs to a different tenant
- **THEN** the response SHALL have status `404`

#### Scenario: Create Cohorte with vig_desde after vig_hasta
- **WHEN** a POST request is sent to `/api/admin/cohortes` with `vig_desde='2025-06-01'` and `vig_hasta='2025-03-01'`
- **THEN** the response SHALL have status `422`
- **THEN** the response SHALL contain a validation error for the date range

#### Scenario: List cohortes filtered by carrera_id
- **WHEN** a GET request is sent to `/api/admin/cohortes?carrera_id={id}`
- **THEN** the response SHALL have status `200`
- **THEN** only cohortes belonging to that carrera SHALL be returned

#### Scenario: Update Cohorte estado and vigencia dates
- **WHEN** a PUT request is sent to `/api/admin/cohortes/{id}` with updated `estado='Inactiva'`, `vig_hasta='2025-12-31'`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL reflect the updated values

### Requirement: The system SHALL provide CRUD for Materia (subject catalog)

The system MUST provide a `Materia` model and REST endpoints to manage the tenant-wide subject catalog. A materia is a unique definition in the catalog — not tied to a specific carrera or cohorte (that relationship is managed via Asignacion E5 and ProgramaMateria E16 in future changes).

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL |
| `codigo` | String(20) | NOT NULL, uppercase alphanumeric with underscores |
| `nombre` | String(255) | NOT NULL |
| `estado` | String(20) | NOT NULL, default `'Activa'` |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Unique constraint on `(tenant_id, codigo)`.

#### Scenario: Create Materia with valid fields
- **WHEN** a POST request is sent to `/api/admin/materias` with `codigo='PROG_I'`, `nombre='Programación I'`
- **THEN** the response SHALL have status `201`
- **THEN** `codigo` SHALL be stored uppercased

#### Scenario: Create Materia with duplicate codigo in same tenant
- **WHEN** a POST request is sent with an existing `codigo` in the same tenant
- **THEN** the response SHALL have status `409`

#### Scenario: List all materias for the tenant
- **WHEN** a GET request is sent to `/api/admin/materias`
- **THEN** the response SHALL contain only materias from the current tenant

#### Scenario: Update Materia to inactive
- **WHEN** a PUT request sets `estado='Inactiva'` for a materia
- **THEN** the response SHALL have status `200`
- **THEN** the materia SHALL NOT appear in active-only queries (future feature)

### Requirement: The system SHALL provide ProgramaMateria upload and management

The system MUST provide a `ProgramaMateria` model and endpoints to manage official syllabus documents (PDFs) linked to a specific materia + carrera + cohorte combination.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL |
| `materia_id` | UUID (string) | FK → materias.id, NOT NULL |
| `carrera_id` | UUID (string) | FK → carreras.id, NOT NULL |
| `cohorte_id` | UUID (string) | FK → cohortes.id, NOT NULL |
| `titulo` | String(255) | NOT NULL |
| `referencia_archivo` | String(500) | NOT NULL, storage reference |
| `cargado_at` | DateTime(tz) | server default now() |

#### Scenario: Upload a programa PDF
- **WHEN** a POST request is sent to `/api/admin/programas-materia/upload` with `titulo='Programa 2025'`, `materia_id`, `carrera_id`, `cohorte_id`, and a PDF file
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain `id`, `titulo`, `referencia_archivo`, `materia_id`, `carrera_id`, `cohorte_id`, `cargado_at`

#### Scenario: List programas by materia
- **WHEN** a GET request is sent to `/api/admin/programas-materia?materia_id={id}`
- **THEN** only programas for that materia SHALL be returned

#### Scenario: Delete a programa record
- **WHEN** a DELETE request is sent to `/api/admin/programas-materia/{id}`
- **THEN** the response SHALL have status `204`
- **THEN** the record SHALL be removed from the database

#### Scenario: Delete programa from another tenant
- **WHEN** a DELETE request targets a programa belonging to a different tenant
- **THEN** the response SHALL have status `404`

### Requirement: The system SHALL enforce multi-tenant isolation for all academic entities

All academic entities (Carrera, Cohorte, Materia, ProgramaMateria) MUST be scoped to a tenant. The `tenant_id` is resolved from the JWT, never from request parameters. Queries must never return data from a different tenant.

#### Scenario: Cross-tenant data isolation on list
- **WHEN** two users from different tenants each list their carreras
- **THEN** each user SHALL only see carreras belonging to their own tenant
- **THEN** no carrera from tenant A SHALL appear in the response for tenant B

#### Scenario: Cross-tenant isolation on single entity access
- **WHEN** a user from tenant A requests a specific Carrera or Cohorte or Materia or ProgramaMateria belonging to tenant B
- **THEN** the response SHALL have status `404` (entity not found — no information leakage)

### Requirement: The system SHALL validate codigo format for Carrera and Materia

The `codigo` field for both Carrera and Materia MUST enforce a format constraint: uppercase alphanumeric characters and underscores only, 1-20 characters.

#### Scenario: Create Carrera with lowercase codigo
- **WHEN** a POST request sends `codigo='tupad'` (lowercase)
- **THEN** the system SHALL automatically uppercase it to `'TUPAD'`
- **THEN** the carrera SHALL be created successfully
