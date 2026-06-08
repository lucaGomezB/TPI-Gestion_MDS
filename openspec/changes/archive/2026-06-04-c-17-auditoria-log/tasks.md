## 1. Action Code Catalog

- [x] 1.1 Create `core/action_codes.py` with `AccionAuditoria` StrEnum containing: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`
- [x] 1.2 Add validation that `log_action()` rejects non-enum values with `ValueError`

## 2. AuditLog Model

- [x] 2.1 Create `models/audit_log.py` with `AuditLog` model: all fields per design D-10, inheriting `AppModel` + `TenantMixin` only (NOT `TimestampMixin` or `AuditMixin`)
- [x] 2.2 Add SQLAlchemy event listener that prevents ORM-level UPDATE on `AuditLog` instances
- [x] 2.3 Update `models/__init__.py` to export `AuditLog`

## 3. Migration 013 — Audit Log Schema

- [x] 3.1 Create Alembic migration `f7a8b9c0d1e2` (003_audit_log.py, depends_on `a1b2c3d4e5f6`) with `upgrade()`:
  - Create `audit_log` table with all columns
  - Add generated column `search_vector TSVECTOR`
  - Create B-tree indexes: `(tenant_id, fecha_hora DESC)`, `(tenant_id, accion)`, `(tenant_id, actor_id, fecha_hora DESC)`, `(tenant_id, materia_id, fecha_hora DESC)`, `(tenant_id, ip)`
  - Create GIN index on `search_vector`
  - Create append-only triggers `trg_reject_audit_update` and `trg_reject_audit_delete`
- [x] 3.2 Implement `downgrade()` — drop all indexes, triggers, function, and the `audit_log` table
- [ ] 3.3 Verify migration against test database (requires running PostgreSQL with `alembic upgrade head`)

## 4. Audit Repository

- [x] 4.1 Create `repositories/audit_repository.py` with `AuditRepository`:
  - `create(entry: AuditLog) -> AuditLog` — persist new entry
  - `search(tenant_id, q=None, accion=None, actor_id=None, materia_id=None, ip=None, fecha_desde=None, fecha_hasta=None, limit=50, offset=0) -> tuple[list[AuditLog], int]` — full-text search with filters, returns (items, total)
  - `get_docente_interacciones(tenant_id, docente_id) -> dict` — aggregated metrics per F9.1
  - `export_search(tenant_id, filters) -> list[dict]` — returns raw data for export (no pagination limit)
- [x] 4.2 Repository MUST NOT expose `update()` or `delete()` methods (append-only enforced at application layer)

## 5. Audit Service

- [x] 5.1 Create `services/audit_service.py` with `AuditService`:
  - `log_action(accion, actor_id, tenant_id, materia_id=None, impersonado_id=None, detalle=None, filas_afectadas=None, ip=None, user_agent=None) -> AuditLogResponse`
  - `search(tenant_id, q=None, accion=None, actor_id=None, materia_id=None, ip=None, fecha_desde=None, fecha_hasta=None, limit=50, offset=0) -> AuditLogSearchResponse`
  - `get_docente_interacciones(tenant_id, docente_id) -> DocenteInteraccionesResponse`
  - `export(tenant_id, filters, formato: str) -> StreamingResponse`
- [x] 5.2 Validate that `accion` is a valid `AccionAuditoria` member in `log_action()`, raise `ValueError` otherwise

## 6. Pydantic Schemas

- [x] 6.1 Create `schemas/audit.py` with all schemas, all with `model_config = ConfigDict(extra='forbid')`:
  - `AuditLogResponse` — response schema for a single audit entry
  - `AuditLogSearchParams` — query params for search (q, accion, actor_id, materia_id, ip, fecha_desde, fecha_hasta, limit, offset)
  - `AuditLogSearchResponse` — paginated response with items, total, limit, offset
  - `DocenteInteraccionesResponse` — docente_id, total_acciones, por_accion, por_materia, ultimas_acciones
  - `AuditExportParams` — same filters + formato (csv | json)

## 7. Admin Router — Search Endpoint

- [x] 7.1 Create `api/v1/routers/admin_auditoria.py` with:
  - `GET /api/admin/auditoria` — full-text search with filters, paginated, protected by `require_permission("auditoria:ver")`
  - `tenant_id` resolved from JWT (never from request params)
- [x] 7.2 Register `admin_auditoria` router in `api/v1/routers/__init__.py`

## 8. Admin Router — Export Endpoint

- [x] 8.1 Add `GET /api/admin/auditoria/exportar` to `admin_auditoria.py`:
  - Same filters as search + `formato` parameter (csv | json default csv)
  - Returns `StreamingResponse` with appropriate Content-Type and Content-Disposition headers
  - Protected by `require_permission("auditoria:ver")`

## 9. Admin Router — Docente Interacciones Endpoint

- [x] 9.1 Add `GET /api/admin/auditoria/docentes/{docente_id}/interacciones` to `admin_auditoria.py`:
  - Returns aggregated interaction metrics (F9.1)
  - Tenant-scoped: only entries for the caller's tenant
  - Protected by `require_permission("auditoria:ver")`

## 10. Audit Middleware/Interceptor Infrastructure

- [x] 10.1 Create `core/audit_context.py` with helper to extract request metadata (IP, user_agent) from FastAPI `Request` object
- [x] 10.2 Create `core/audit_decorator.py` with `@audit_log(accion: AccionAuditoria)` decorator for simple service methods (optional, applies to services that can auto-derive materia_id, detalle, filas_afectadas from the return value)

## 11. Tests

- [x] 11.1 Unit test for `AccionAuditoria` enum — all codes exist, values match names (7 parametrized + 4 additional = 11 assertions across 5 test methods)
- [x] 11.2 Unit test for `AuditRepository` append-only enforcement — verify no update/delete methods exist (6 test methods covering create, search, get_docente_interacciones, export_search, absence of update/delete)
- [x] 11.3 Unit test for invalid action code rejection — `log_action()` with invalid code raises `ValueError` (2 test methods: invalid string, invalid type)
- [x] 11.4 Integration test for audit log creation — repository.create() creates `AuditLog` entry with all fields (2 test methods: all fields, minimal fields)
- [x] 11.5 Integration test for append-only trigger — direct SQL UPDATE/DELETE on `audit_log` raises exception (2 test methods: UPDATE rejected, DELETE rejected)
- [x] 11.6 Integration test for full-text search — search by keyword returns matching entries (2 test methods: with results, no results)
- [x] 11.7 Integration test for filters — search with each filter type (7 test methods: accion, actor_id, materia_id, date range, IP, combined filters)
- [x] 11.8 Integration test for tenant isolation — two tenants have separate search results (1 test method)
- [x] 11.9 Integration test for impersonation — `impersonado_id` is correctly recorded (1 test method)
- [x] 11.10 Integration test for PII sanitization — verify no PII patterns in `detalle` (1 test method with regex patterns)
- [x] 11.11 Integration test for docente interacciones endpoint — returns aggregated metrics (2 test methods: with data, no activity)
- [x] 11.12 Integration test for export — JSON and CSV export structures (2 test methods)
- [x] 11.13 Integration test for permission enforcement — user without `auditoria:ver` gets 403 on all audit endpoints (1 test method verifying 403 for ALUMNO, 200 for COORDINADOR)

> **Note**: Integration tests (11.4–11.13) require Docker with PostgreSQL (testcontainers). Unit tests (11.1–11.3) pass without DB. All 19 unit tests pass. Integration tests skip gracefully if testcontainers/Docker is unavailable.
