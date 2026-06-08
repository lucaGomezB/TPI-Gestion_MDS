## Why

The system has no audit trail. RN-23 mandates that every significant action must generate an immutable audit record with full attribution (actor, materia, IP, user agent, affected rows). RN-24 requires a closed catalog of standardized action codes. Without this, no write-capable domain feature (califications import, liquidations, communications) can be built with accountability. Additionally, F9.1 and F9.2 require searchable, filterable audit log views for ADMIN/COORDINADOR roles. This change establishes the append-only audit infrastructure before any write-heavy feature is implemented.

## What Changes

- Create `AuditLog` SQLAlchemy model — append-only, no UPDATE or DELETE operations allowed at any layer
- Encode append-only guarantee at every layer: repository (no update/delete methods), service (create-only), DB (no UPDATE/DELETE grants, or at minimum a trigger to reject updates), and model-level constraint
- Create migration 013: `audit_log` table with tenant-isolated indexes, full-text search support, and action code index
- Implement `AuditMiddleware` that automatically intercepts significant write actions and records audit entries (actor_id from JWT, IP from request, user_agent from headers)
- Implement action code catalog as a Python enum/str enum (`CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, etc.) with explicit mapping
- Endpoints:
  - `GET /api/admin/auditoria` — full-text search with filters (accion, usuario, materia, fecha, IP, actor_id)
  - `GET /api/admin/auditoria/docentes/{id}/interacciones` — interaction panel per docente (F9.1)
- Export search results as CSV/JSON
- PII protection: ensure encrypted fields (email, DNI, CUIL, CBU) are NEVER logged in `detalle` JSON
- Append-only enforced at DB level: reject UPDATE/DELETE via PostgreSQL trigger or schema-level privilege
- Standardized action codes:
  - `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, `ASIGNACION_MODIFICAR`, `LIQUIDACION_CERRAR`, `IMPERSONACION_INICIAR`, `IMPERSONACION_FINALIZAR`
  - Extensible catalog for future actions
- Tests: audit creation, full-text search, append-only violation rejection, impersonation context, PII sanitization in logs

## Capabilities

### New Capabilities
- `auditoria-log`: Audit log infrastructure — append-only model with full-text search, filterable query endpoints, teacher interaction panel (F9.1), action code catalog (RN-24), automatic middleware interception, search result export, and strict PII sanitization in log entries.

### Modified Capabilities
- `core-models`: AuditLog entity added to the domain model catalog (E-AUD per 04_modelo_de_datos.md)

## Impact

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/audit_log.py` | **New** | `AuditLog` model: id, tenant_id, fecha_hora, actor_id, impersonado_id, materia_id, accion, detalle (JSONB), filas_afectadas, ip, user_agent |
| `backend/app/models/__init__.py` | Modified | Export AuditLog model |
| `backend/app/repositories/audit_repository.py` | **New** | Create-only repository (no update, no delete). Search with full-text + filters |
| `backend/app/services/audit_service.py` | **New** | Audit service: log_action, search, get_docente_interacciones, export |
| `backend/app/schemas/audit.py` | **New** | Pydantic schemas for audit requests/responses, all with `extra='forbid'` |
| `backend/app/api/v1/routers/admin_auditoria.py` | **New** | Admin endpoints: GET search, GET docente interacciones, GET export |
| `backend/app/api/v1/routers/__init__.py` | Modified | Register admin_auditoria router |
| `backend/app/core/audit_middleware.py` | **New** | Middleware/interceptor that captures actions and dispatches to audit service |
| `backend/app/core/action_codes.py` | **New** | Enum of all standardized action codes (closed catalog, per RN-24) |
| `backend/alembic/versions/` | **New** | Migration 013: `audit_log` table with indexes for GIN full-text search, filtering, tenant isolation |
| `backend/requirements.txt` | Modified | Potentially add `csv` or `xlsx` for export (stdlib csv is sufficient for MVP) |
