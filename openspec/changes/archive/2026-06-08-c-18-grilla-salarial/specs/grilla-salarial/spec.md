## ADDED Requirements

### Requirement: The system SHALL allow FINANZAS to manage salary base amounts per role

The system MUST provide CRUD endpoints under `/api/admin/salarios/base` that allow users with permission `liquidaciones:configurar-salarios` to manage `SalarioBase` records. Each record defines a base salary amount for a specific role (COORDINADOR, NEXO, PROFESOR, TUTOR) with temporal validity (`desde` = start date, `hasta` = nullable end date).

#### Scenario: Create salary base entry
- **WHEN** a user with `liquidaciones:configurar-salarios` sends a POST to `/api/admin/salarios/base` with `{"rol": "PROFESOR", "monto": 150000.00, "desde": "2026-01-01"}`
- **THEN** the system SHALL return `201` with the created record including auto-generated UUID `id` and `tenant_id`
- **THEN** the record SHALL have `hasta` defaulting to `null`

#### Scenario: Create salary base with explicit hasta
- **WHEN** a user sends a POST with `{"rol": "PROFESOR", "monto": 140000.00, "desde": "2025-06-01", "hasta": "2025-12-31"}`
- **THEN** the system SHALL return `201` with `hasta` set to `"2025-12-31"`

#### Scenario: Reject overlapping date ranges for same role
- **WHEN** a user creates a SalarioBase for rol=PROFESOR with `desde` that falls within an existing record's date range for the same role and tenant
- **THEN** the system SHALL return `409 Conflict` with a message indicating overlapping vigencia

#### Scenario: List all salary base entries for tenant
- **WHEN** a user sends GET to `/api/admin/salarios/base`
- **THEN** the system SHALL return `200` with a paginated list of all SalarioBase records for the current tenant, ordered by `desde` descending

#### Scenario: Get single salary base entry by id
- **WHEN** a user sends GET to `/api/admin/salarios/base/{id}`
- **THEN** the system SHALL return `200` with the matching record
- **WHEN** the id does not exist
- **THEN** the system SHALL return `404`

#### Scenario: Update salary base entry
- **WHEN** a user sends PUT to `/api/admin/salarios/base/{id}` with `{"monto": 160000.00}`
- **THEN** the system SHALL return `200` with the updated record
- **THEN** `updated_at` SHALL be updated

#### Scenario: Reject overlapping on update
- **WHEN** a user updates a SalarioBase's `desde` or `hasta` causing overlap with another record for the same role and tenant
- **THEN** the system SHALL return `409 Conflict`

#### Scenario: Reject unknown rol value
- **WHEN** a user sends POST with `{"rol": "INEXISTENTE", "monto": 1000, "desde": "2026-01-01"}`
- **THEN** the system SHALL return `422` with validation error

#### Scenario: Reject missing monto or desde
- **WHEN** a user sends POST without `monto` or without `desde`
- **THEN** the system SHALL return `422` with validation error

### Requirement: The system SHALL allow FINANZAS to manage bonus pay (plus) amounts per subject group and role

The system MUST provide CRUD endpoints under `/api/admin/salarios/plus` that allow users with permission `liquidaciones:configurar-salarios` to manage `SalarioPlus` records. Each record defines a bonus amount for a specific combination of subject group and role.

#### Scenario: Create salary plus entry
- **WHEN** a user sends POST to `/api/admin/salarios/plus` with `{"grupo": "PROG", "rol": "PROFESOR", "descripcion": "Plus Programacion", "monto": 5000.00, "desde": "2026-01-01"}`
- **THEN** the system SHALL return `201` with the created record

#### Scenario: List all plus entries for tenant
- **WHEN** a user sends GET to `/api/admin/salarios/plus`
- **THEN** the system SHALL return `200` with records ordered by `desde` descending

#### Scenario: Update plus entry
- **WHEN** a user sends PUT to `/api/admin/salarios/plus/{id}` with `{"monto": 6000.00}`
- **THEN** the system SHALL return `200` with the updated record

#### Scenario: Reject overlapping date range for same grupo+rol
- **WHEN** a user creates a SalarioPlus for (grupo="PROG", rol=PROFESOR) with `desde` that overlaps an existing record for the same tenant
- **THEN** the system SHALL return `409 Conflict`

#### Scenario: Reject unknown grupo reference
- **WHEN** a user sends POST with `grupo` that does not match any existing GrupoMateria for the tenant
- **THEN** the system SHALL return `422` with validation error

### Requirement: The system SHALL allow FINANZAS to manage subject groups per tenant

The system MUST provide CRUD endpoints under `/api/admin/salarios/grupos` for managing `GrupoMateria` records. A group is a key used to categorize subjects (e.g., "PROG", "BD", "MAT"). Groups are tenant-scoped.

#### Scenario: Create subject group
- **WHEN** a user sends POST to `/api/admin/salarios/grupos` with `{"grupo": "PROG", "descripcion": "Materias de Programacion"}`
- **THEN** the system SHALL return `201` with the created record

#### Scenario: Reject duplicate group key within tenant
- **WHEN** a user sends POST with an existing `grupo` key for the same tenant
- **THEN** the system SHALL return `409 Conflict`

#### Scenario: List all subject groups
- **WHEN** a user sends GET to `/api/admin/salarios/grupos`
- **THEN** the system SHALL return `200` with all groups for the current tenant

#### Scenario: Assign subjects to a group
- **WHEN** a user sends PUT to `/api/admin/salarios/grupos/{id}` with `{"materias": ["uuid-materia-1", "uuid-materia-2"]}`
- **THEN** the system SHALL return `200` with the updated group including the subject associations

#### Scenario: Get effective subjects for a group
- **WHEN** a user sends GET to `/api/admin/salarios/grupos/{id}/materias`
- **THEN** the system SHALL return `200` with the list of subjects assigned to that group

### Requirement: The system SHALL expose a service to query vigentes values for a given date

The system MUST provide a query method (not an HTTP endpoint, consumed by C-19 liquidaciones service) that returns the active SalarioBase and SalarioPlus records for a specific date.

#### Scenario: Get vigente base by rol and date
- **WHEN** querying SalarioBase for rol=PROFESOR on date `2026-06-15`
- **THEN** the system SHALL return the record where `desde <= 2026-06-15 AND (hasta IS NULL OR hasta >= 2026-06-15)`

#### Scenario: Get vigente base returns null when no matching record
- **WHEN** querying SalarioBase for a rol without any vigente entry for that date
- **THEN** the system SHALL return `None`

#### Scenario: Get vigente plus by grupo+rol and date
- **WHEN** querying SalarioPlus for (grupo="PROG", rol=PROFESOR) on date `2026-06-15`
- **THEN** the system SHALL return the record with matching grupo, rol, and vigente date range

#### Scenario: Get all vigentes plus for a date
- **WHEN** querying all vigente SalarioPlus for a given date
- **THEN** the system SHALL return all records whose `desde <= date AND (hasta IS NULL OR hasta >= date)`

### Requirement: The system SHALL enforce authorization via require_permission

All salary grid endpoints MUST be protected.

#### Scenario: Reject request without authentication
- **WHEN** an unauthenticated request is sent to any `/api/admin/salarios/*` endpoint
- **THEN** the system SHALL return `401`

#### Scenario: Reject request without FINANZAS role
- **WHEN** an authenticated user without permission `liquidaciones:configurar-salarios` sends a request to any `/api/admin/salarios/*` endpoint
- **THEN** the system SHALL return `403`

#### Scenario: Accept request with correct permission
- **WHEN** a FINANZAS user with `liquidaciones:configurar-salarios` sends a request
- **THEN** the system SHALL process the request and return the appropriate status code
