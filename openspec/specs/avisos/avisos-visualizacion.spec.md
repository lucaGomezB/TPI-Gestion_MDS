## ADDED Requirements

### Requirement: Visible avisos for authenticated user (RN-18, RN-20)

The system SHALL provide a public endpoint at `GET /api/avisos` that returns avisos visible to the authenticated user. Visibility is determined by alcance, vigencia, rol_destino, and severidad as defined in RN-20. Avisos outside their vigencia window (RN-18) SHALL NOT be returned.

#### Scenario: Returns only avisos within vigencia window (RN-18)
- **WHEN** an authenticated user sends GET to `/api/avisos`
- **THEN** the system SHALL only return avisos where `inicio_en <= now() AND fin_en >= now()`
- **WHEN** an aviso has `inicio_en` in the future
- **THEN** it SHALL NOT appear in the response
- **WHEN** an aviso has `fin_en` in the past
- **THEN** it SHALL NOT appear in the response

#### Scenario: Returns only active avisos
- **WHEN** an authenticated user sends GET to `/api/avisos`
- **THEN** the system SHALL only return avisos where `activo = true`

#### Scenario: Filters by alcance Global (visible to all)
- **WHEN** there are avisos with `alcance = Global` within vigencia
- **THEN** they SHALL be returned for any authenticated user regardless of roles and assignments

#### Scenario: Filters by alcance PorRol (RN-20)
- **WHEN** there are avisos with `alcance = PorRol` and `rol_destino = PROFESOR`
- **THEN** they SHALL only be returned to users whose roles include PROFESOR
- **WHEN** the user's roles do not include the specified `rol_destino`
- **THEN** those avisos SHALL NOT be returned

#### Scenario: Filters by alcance PorMateria (RN-20)
- **WHEN** there are avisos with `alcance = PorMateria` and a specific `materia_id`
- **THEN** they SHALL only be returned to users who have an active assignment to that materia
- **WHEN** the user has no assignment to the specified materia
- **THEN** those avisos SHALL NOT be returned

#### Scenario: Filters by alcance PorCohorte (RN-20)
- **WHEN** there are avisos with `alcance = PorCohorte` and a specific `cohorte_id`
- **THEN** they SHALL only be returned to users whose materias belong to that cohorte
- **WHEN** the user has no materias in the specified cohorte
- **THEN** those avisos SHALL NOT be returned

#### Scenario: Results ordered by orden ASC, then created_at DESC
- **WHEN** avisos are returned from GET /api/avisos
- **THEN** they SHALL be sorted by `orden` ascending (lower = higher priority), and for avisos with the same `orden`, by `created_at` descending (newest first)

#### Scenario: Empty response when no visible avisos
- **WHEN** an authenticated user sends GET to `/api/avisos` and no avisos match their scope, vigencia, or role
- **THEN** the system SHALL return HTTP 200 with an empty array (not 404)

#### Scenario: Severidad filter parameter
- **WHEN** an authenticated user sends GET to `/api/avisos?severidad=Critico`
- **THEN** the system SHALL only return avisos with that severidad level
- **WHEN** no severidad filter is provided
- **THEN** all severidad levels SHALL be included

#### Scenario: Multi-tenant isolation
- **WHEN** two tenants each have avisos with the same configuration
- **THEN** users from tenant A SHALL only see tenant A's avisos, and users from tenant B SHALL only see tenant B's avisos
