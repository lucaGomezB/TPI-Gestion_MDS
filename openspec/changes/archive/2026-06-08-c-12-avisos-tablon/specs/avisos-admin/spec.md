## ADDED Requirements

### Requirement: Admin CRUD for system notices (avisos)

COORDINADOR and ADMIN users SHALL be able to create, read, update, and deactivate system notices (avisos) via a dedicated administrative API at `/api/admin/avisos`. Each aviso SHALL support configurable alcance, severidad, vigencia, orden, and require_ack flag.

#### Scenario: Create a new aviso with full configuration
- **WHEN** an authenticated user with `avisos:publicar` permission sends a POST request to `/api/admin/avisos` with a valid body containing titulo, cuerpo, alcance, severidad, inicio_en, fin_en, orden, activo, and optionally materia_id, cohorte_id, rol_destino, and requiere_ack
- **THEN** the system SHALL create a new Aviso record with the provided data, auto-assign tenant_id from the JWT, and return HTTP 201 with the created aviso including its id and timestamps

#### Scenario: Create aviso validates required fields
- **WHEN** a POST request to `/api/admin/avisos` omits required fields (titulo, cuerpo, alcance, severidad, inicio_en, fin_en)
- **THEN** the system SHALL reject the request with HTTP 422 and a Pydantic validation error indicating which fields are missing

#### Scenario: Create aviso validates alcance-specific context
- **WHEN** alcance is "PorMateria" and materia_id is not provided
- **THEN** the system SHALL reject the request with HTTP 422 indicating materia_id is required when alcance is PorMateria
- **WHEN** alcance is "PorCohorte" and cohorte_id is not provided
- **THEN** the system SHALL reject the request with HTTP 422 indicating cohorte_id is required when alcance is PorCohorte
- **WHEN** alcance is "Global" and both materia_id and cohorte_id are provided
- **THEN** the system SHALL store the aviso with alcance Global and ignore the context fields

#### Scenario: Create aviso validates vigencia range
- **WHEN** inicio_en is later than fin_en
- **THEN** the system SHALL reject the request with HTTP 422 indicating that inicio_en must be before fin_en

#### Scenario: List all avisos with admin filters
- **WHEN** an authenticated user with `avisos:publicar` permission sends a GET request to `/api/admin/avisos`
- **THEN** the system SHALL return HTTP 200 with a paginated list of all avisos for the tenant, ordered by orden ASC, created_at DESC

#### Scenario: List avisos supports query filters
- **WHEN** a GET request to `/api/admin/avisos` includes query parameters such as `activo=true`, `alcance=Global`, `severidad=Critico`
- **THEN** the system SHALL filter results by the provided parameters before returning

#### Scenario: Get single aviso by id
- **WHEN** an authenticated user with `avisos:publicar` permission sends a GET request to `/api/admin/avisos/{id}`
- **THEN** the system SHALL return HTTP 200 with the full aviso details
- **WHEN** the aviso does not exist or belongs to a different tenant
- **THEN** the system SHALL return HTTP 404

#### Scenario: Update an existing aviso
- **WHEN** an authenticated user with `avisos:publicar` permission sends a PUT request to `/api/admin/avisos/{id}` with valid fields to update
- **THEN** the system SHALL update only the provided fields on the aviso record and return HTTP 200 with the updated aviso
- **WHEN** the aviso does not exist or belongs to a different tenant
- **THEN** the system SHALL return HTTP 404

#### Scenario: Delete (deactivate) an aviso
- **WHEN** an authenticated user with `avisos:publicar` permission sends a DELETE request to `/api/admin/avisos/{id}`
- **THEN** the system SHALL set `activo=false` on the aviso (soft deactivation) and return HTTP 204
- **WHEN** the aviso does not exist or belongs to a different tenant
- **THEN** the system SHALL return HTTP 404

#### Scenario: Admin endpoints require avisos:publicar permission
- **WHEN** a user without `avisos:publicar` permission sends any request to `/api/admin/avisos`
- **THEN** the system SHALL reject the request with HTTP 403

#### Scenario: Multi-tenant isolation for admin CRUD
- **WHEN** two avisos with the same id exist in different tenants
- **THEN** an admin user from tenant A SHALL only see and operate on tenant A's aviso
- **WHEN** an admin user from tenant A tries to access tenant B's aviso by id
- **THEN** the system SHALL return HTTP 404 (not 403, to avoid leaking existence across tenants)
