# Auditoria Log

> **Purpose**: Define the append-only audit log infrastructure — model, middleware, search, export, and panel views. Every significant write action in the system generates an immutable audit record (RN-23) with standardized action codes (RN-24). The log is searchable via full-text and filters, exportable, and tenant-isolated. PII-sensitive fields are never logged.

---

## ADDED Requirements

### Requirement: AuditLog SHALL be append-only at the database layer

The system MUST enforce append-only semantics for the `audit_log` table at the PostgreSQL level. UPDATE and DELETE operations on `audit_log` MUST be rejected via triggers.

#### Scenario: UPDATE on audit_log raises exception
- **WHEN** an UPDATE statement is executed against the `audit_log` table
- **THEN** the database SHALL raise an exception with message `audit_log is append-only: UPDATE and DELETE are forbidden`
- **THEN** the row SHALL remain unchanged

#### Scenario: DELETE on audit_log raises exception
- **WHEN** a DELETE statement is executed against the `audit_log` table
- **THEN** the database SHALL raise an exception with message `audit_log is append-only: UPDATE and DELETE are forbidden`
- **THEN** the row SHALL remain in the table

### Requirement: AuditLog SHALL be append-only at the application layer

The system MUST enforce append-only semantics at the repository and service layers. The `AuditRepository` MUST NOT expose `update()` or `delete()` methods. The `AuditService` MUST NOT expose update or delete operations.

#### Scenario: AuditRepository has no update/delete methods
- **WHEN** inspecting the `AuditRepository` class
- **THEN** it SHALL have a `create()` method
- **THEN** it SHALL have a `search()` method
- **THEN** it SHALL have a `count()` method
- **THEN** it SHALL NOT have an `update()` method
- **THEN** it SHALL NOT have a `delete()` method

#### Scenario: SQLAlchemy event prevents ORM-level UPDATE
- **WHEN** an ORM-level UPDATE is attempted on an `AuditLog` instance
- **THEN** SQLAlchemy SHALL raise an exception before emitting the SQL statement
- **THEN** the database row SHALL remain unchanged

### Requirement: The system SHALL define a closed catalog of action codes via StrEnum

The system MUST provide a `AccionAuditoria` StrEnum (closed catalog per RN-24) containing all standardized action codes. The catalog SHALL be extensible by adding new members in future changes.

#### Scenario: Action code enum contains standard codes
- **WHEN** inspecting `AccionAuditoria`
- **THEN** it SHALL contain at least: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`
- **THEN** each member SHALL have a string value matching its name (e.g., `AccionAuditoria.CALIFICACIONES_IMPORTAR.value == "CALIFICACIONES_IMPORTAR"`)

#### Scenario: Only valid action codes are accepted
- **WHEN** `audit_service.log_action()` is called with an `accion` that is not a member of `AccionAuditoria`
- **THEN** the system SHALL raise a `ValueError`
- **THEN** no audit record SHALL be created

### Requirement: The system SHALL provide an AuditLog SQLAlchemy model

The system MUST provide an `AuditLog` SQLAlchemy model matching the E-AUD entity from the data model. The model SHALL NOT inherit `TimestampMixin` or `AuditMixin` (it is immutable).

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL |
| `fecha_hora` | DateTime(tz) | NOT NULL, server default `now()` |
| `actor_id` | UUID (string) | FK → usuarios.id, NOT NULL |
| `impersonado_id` | UUID (string) | FK → usuarios.id, nullable |
| `materia_id` | UUID (string) | FK → materias.id, nullable |
| `accion` | String(50) | NOT NULL |
| `detalle` | JSONB | Nullable |
| `filas_afectadas` | Integer | Nullable |
| `ip` | String(45) | Nullable |
| `user_agent` | String(500) | Nullable |

#### Scenario: Create AuditLog entry
- **WHEN** a new `AuditLog` is created with valid fields
- **THEN** `id` SHALL be an auto-generated UUID
- **THEN** `fecha_hora` SHALL be set to the current timestamp
- **THEN** all provided fields SHALL be persisted

#### Scenario: AuditLog with impersonation
- **WHEN** an `AuditLog` is created with both `actor_id=A` and `impersonado_id=B`
- **THEN** the entry SHALL record both IDs
- **THEN** `impersonado_id` SHALL reference the user being impersonated

#### Scenario: AuditLog without optional fields
- **WHEN** an `AuditLog` is created with only required fields (`actor_id`, `accion`)
- **THEN** `materia_id`, `impersonado_id`, `detalle`, `filas_afectadas`, `ip`, `user_agent` SHALL be `NULL`

### Requirement: The system SHALL provide an audit service for logging actions

The system MUST provide an `AuditService` with a `log_action()` method that creates audit entries. The service SHALL be injectable via dependency injection.

#### Scenario: log_action creates an audit entry
- **WHEN** `audit_service.log_action(accion=CALIFICACIONES_IMPORTAR, actor_id=..., materia_id=..., detalle={...}, filas_afectadas=10, ip=..., user_agent=...)` is called
- **THEN** a new `AuditLog` record SHALL be created with all provided fields
- **THEN** the method SHALL return the created `AuditLog` entry

#### Scenario: log_action with impersonated user
- **WHEN** `audit_service.log_action(accion=..., actor_id=real_admin_id, impersonado_id=target_user_id)` is called
- **THEN** the created entry SHALL have `actor_id` equal to `real_admin_id`
- **THEN** the created entry SHALL have `impersonado_id` equal to `target_user_id`

### Requirement: The search endpoint SHALL support full-text query with filters

The system MUST provide `GET /api/admin/auditoria` with full-text search (`q` parameter) plus optional exact-match filters. All searches MUST be scoped to the caller's `tenant_id`. Results MUST be paginated.

#### Scenario: Search with full-text query
- **WHEN** a GET request is sent to `/api/admin/auditoria?q=importar` from a user with permission `auditoria:ver`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `items`, `total`, `limit`, `offset`
- **THEN** `items` SHALL contain only audit entries matching the full-text query within the caller's tenant
- **THEN** `items` SHALL be ordered by `fecha_hora DESC`

#### Scenario: Search with action filter
- **WHEN** a GET request is sent to `/api/admin/auditoria?accion=CALIFICACIONES_IMPORTAR`
- **THEN** only audit entries with `accion="CALIFICACIONES_IMPORTAR"` SHALL be returned

#### Scenario: Search with actor filter
- **WHEN** a GET request is sent to `/api/admin/auditoria?actor_id=<uuid>`
- **THEN** only audit entries with that `actor_id` SHALL be returned

#### Scenario: Search with materia filter
- **WHEN** a GET request is sent to `/api/admin/auditoria?materia_id=<uuid>`
- **THEN** only audit entries with that `materia_id` SHALL be returned

#### Scenario: Search with date range
- **WHEN** a GET request is sent to `/api/admin/auditoria?fecha_desde=2026-01-01&fecha_hasta=2026-06-01`
- **THEN** only entries with `fecha_hora` within that range SHALL be returned

#### Scenario: Search with multiple filters combined
- **WHEN** a GET request is sent to `/api/admin/auditoria?accion=CALIFICACIONES_IMPORTAR&actor_id=<uuid>&fecha_desde=2026-01-01&limit=10&offset=0`
- **THEN** all specified filters SHALL be applied conjunctively
- **THEN** pagination SHALL respect `limit` (default 50, max 200) and `offset`

#### Scenario: Search without auditoria:ver permission
- **WHEN** a GET request is sent to `/api/admin/auditoria` by a user without `auditoria:ver`
- **THEN** the response SHALL have status `403`

#### Scenario: Search with no results
- **WHEN** a GET request is sent to `/api/admin/auditoria?q=nonexistent_term`
- **THEN** the response SHALL have status `200`
- **THEN** `items` SHALL be an empty list
- **THEN** `total` SHALL be `0`

#### Scenario: Tenant isolation in search
- **WHEN** two users from different tenants each search their audit logs
- **THEN** each user SHALL see only entries belonging to their own `tenant_id`
- **THEN** no entries from other tenants SHALL appear in either result set

### Requirement: The system SHALL provide a docente interactions panel

The system MUST provide `GET /api/admin/auditoria/docentes/{id}/interacciones` that returns aggregated interaction metrics for a specific teacher (F9.1). This endpoint SHALL be scoped to the caller's tenant.

#### Scenario: Get docente interacciones with data
- **WHEN** a GET request is sent to `/api/admin/auditoria/docentes/{docente_id}/interacciones`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `docente_id`, `total_acciones`
- **THEN** the response body SHALL contain `por_accion` (object with action code → count)
- **THEN** the response body SHALL contain `por_materia` (array of objects with `materia_id`, `total`)
- **THEN** the response body SHALL contain `ultimas_acciones` (array, max 200 most recent)

#### Scenario: Get docente interacciones for docente with no activity
- **WHEN** a GET request is sent to `/api/admin/auditoria/docentes/{docente_id}/interacciones` for a docente with no audit entries
- **THEN** the response SHALL have status `200`
- **THEN** `total_acciones` SHALL be `0`
- **THEN** `por_accion` SHALL be an empty object
- **THEN** `ultimas_acciones` SHALL be an empty array

#### Scenario: Docente interacciones tenant-isolated
- **WHEN** a user from tenant A requests interacciones for a docente from tenant B
- **THEN** the response SHALL be empty (no cross-tenant data leakage)

### Requirement: The system SHALL provide search result export

The system MUST provide `GET /api/admin/auditoria/exportar` that returns search results in CSV or JSON format, using the same filter parameters as the search endpoint.

#### Scenario: Export search results as CSV
- **WHEN** a GET request is sent to `/api/admin/auditoria/exportar?accion=CALIFICACIONES_IMPORTAR&formato=csv`
- **THEN** the response SHALL have status `200`
- **THEN** `Content-Type` SHALL be `text/csv`
- **THEN** `Content-Disposition` SHALL include a filename like `auditoria-export-{timestamp}.csv`
- **THEN** the body SHALL contain CSV data with headers matching the audit log fields

#### Scenario: Export search results as JSON
- **WHEN** a GET request is sent to `/api/admin/auditoria/exportar?q=importar&formato=json`
- **THEN** the response SHALL have status `200`
- **THEN** `Content-Type` SHALL be `application/json`
- **THEN** the body SHALL be a JSON array of audit entries matching the query

#### Scenario: Export without permission
- **WHEN** a GET request is sent to `/api/admin/auditoria/exportar` by a user without `auditoria:ver`
- **THEN** the response SHALL have status `403`

### Requirement: PII fields SHALL NOT appear in audit log detalle

The system MUST ensure that no Personally Identifiable Information (email, DNI, CUIL, CBU, alias CBU) is ever stored in the `detalle` JSONB field of any audit log entry. The prohibition applies to any code that calls `log_action()`.

#### Scenario: PII not present in audit entries
- **WHEN** any existing `AuditLog` entry's `detalle` is inspected
- **THEN** it SHALL NOT contain a key named or resembling `email`, `dni`, `cuil`, `cbu`, `alias_cbu`

#### Scenario: Test verifies no PII patterns in log
- **WHEN** a test creates audit entries with various actions
- **THEN** the test SHALL assert that no entry's `detalle` contains string patterns matching email addresses or Argentine DNI/CUIL formats

### Requirement: The system SHALL have middleware/interceptor for automatic audit logging

The system MUST provide a mechanism (decorator, interceptor, or explicit service call pattern) for domain services to log actions. The pattern SHALL be documented and consistent across all services. For MVP, the explicit `audit_service.log_action()` call pattern is used — services explicitly call the audit service after completing significant operations.

#### Scenario: Service integrates audit logging
- **WHEN** a domain service completes a significant write operation (e.g., calificaciones import)
- **THEN** the service SHALL call `audit_service.log_action()` with the appropriate action code and context

### Requirement: The migration SHALL create the audit_log table with required indexes

Migration 013 SHALL create the `audit_log` table and all supporting indexes. The migration SHALL be reversible (downgrade drops the table and triggers).

#### Scenario: Migration creates audit_log table
- **WHEN** migration 013 is applied
- **THEN** the `audit_log` table SHALL exist with all defined columns
- **THEN** the append-only triggers SHALL exist
- **THEN** all B-tree indexes SHALL exist: `(tenant_id, fecha_hora DESC)`, `(tenant_id, accion)`, `(tenant_id, actor_id, fecha_hora DESC)`, `(tenant_id, materia_id, fecha_hora DESC)`, `(tenant_id, ip)`
- **THEN** the GIN index on `search_vector` SHALL exist

#### Scenario: Migration downgrade drops audit_log table
- **WHEN** migration 013 is rolled back
- **THEN** the `audit_log` table SHALL be dropped
- **THEN** triggers `trg_reject_audit_update` and `trg_reject_audit_delete` SHALL be removed
- **THEN** all associated indexes SHALL be removed
