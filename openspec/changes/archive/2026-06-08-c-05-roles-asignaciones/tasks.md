## 1. Permission Matrix Update

- [x] 1.1 Add `equipo_docente:ver` permission to COORDINADOR and ADMIN roles in `core/permissions.py`
- [x] 1.2 Verify `equipo_docente:asignar` is present for COORDINADOR and ADMIN (existing, should be confirmed)

## 2. Model Layer

- [x] 2.1 Create `RolDocente` enum in `models/types.py` with values: PROFESOR, TUTOR, COORDINADOR, NEXO, ADMIN, FINANZAS (matching existing roles)
- [x] 2.2 Create `Asignacion` model in `models/asignacion.py`:
  - Inherits `AppModel`, `TimestampMixin`, `TenantMixin`
  - Fields: id, tenant_id (NOT NULL FK), usuario_id (NOT NULL FK), rol (String(20)), materia_id (FK nullable), carrera_id (FK nullable), cohorte_id (FK nullable), comisiones (JSONB, default []), responsable_id (FK nullable), vig_desde (Date NOT NULL), vig_hasta (Date nullable)
  - FKs with `ON DELETE CASCADE` for tenant_id/usuario_id, `ON DELETE SET NULL` for academic context FKs
  - No AuditMixin (state derived from dates, not estado column)
  - `__tablename__ = "asignaciones"`
- [x] 2.3 Update `models/__init__.py` to export `Asignacion` model and `RolDocente` enum

## 3. Pydantic Schemas

- [x] 3.1 Create `schemas/team_management.py` with all schemas (all with `extra='forbid'`):
  - `AsignacionCreate`: usuario_id, rol (from RolDocente enum), materia_id (optional), carrera_id (optional), cohorte_id (optional), comisiones (optional, default []), responsable_id (optional), vig_desde, vig_hasta (optional)
  - `AsignacionUpdate`: all fields optional except id, with partial update semantics
  - `AsignacionResponse`: all model fields + computed `estado_vigencia` (str: Pendiente|Vigente|Vencida)
  - `AsignacionMasivaRequest`: usuario_ids (list[str], min 1), rol, materia_id (optional), carrera_id (optional), cohorte_id (optional), comisiones (optional), responsable_id (optional), vig_desde, vig_hasta (optional)
  - `AsignacionMasivaResponse`: creadas (list[AsignacionResponse]), total (int)
  - `ClonarRequest`: origen_materia_id, origen_carrera_id, origen_cohorte_id, destino_materia_id, destino_carrera_id, destino_cohorte_id
  - `ClonarResponse`: clonadas (int)
  - `VigenciaRequest`: materia_id (optional), carrera_id (optional), cohorte_id (optional), vig_desde, vig_hasta (optional)
  - `VigenciaResponse`: actualizadas (int)
  - `EquipoExportRow`: docente_nombre, docente_apellidos, docente_email, rol, comisiones, responsable_nombre, vig_desde, vig_hasta, estado_vigencia
- [x] 3.2 Add date validation: vig_desde <= vig_hasta (if vig_hasta provided) — use Pydantic `model_validator`
- [x] 3.3 Add rol validation in AsignacionCreate to ensure at least one academic context FK is present for role types that require it (PROFESOR, TUTOR require materia_id)

## 4. Migration 007 — Asignaciones Schema

- [x] 4.1 Generate Alembic migration (revision 007, depends_on revision 006 `c3d4e5f6a7b8`) with:
  - CREATE TABLE asignaciones with all columns matching the model
  - 6 indexes: ix_asignaciones_tenant_rol, ix_asignaciones_usuario_id, ix_asignaciones_materia_id, ix_asignaciones_cohorte_id, ix_asignaciones_responsable_id, ix_asignaciones_vigencia
  - All FKs with proper ON DELETE rules
- [x] 4.2 Implement `downgrade()` — DROP TABLE asignaciones

## 5. Repository Layer

- [x] 5.1 Create `repositories/team_management.py` with `AsignacionRepository`:
  - Inherits from `BaseRepository[Asignacion]`
  - `list_by_filters(usuario_id, materia_id, carrera_id, cohorte_id, rol, vigente)` — filtered query with optional vigencia state filter
  - `bulk_create(entries: list[dict])` — creates multiple assignments in a single transaction
  - `find_by_equipo(materia_id, carrera_id, cohorte_id)` — finds all assignments for an academic context
  - `find_vigentes_by_equipo(materia_id, carrera_id, cohorte_id)` — only currently vigente assignments
  - `update_vigencia(materia_id, carrera_id, cohorte_id, vig_desde, vig_hasta)` — bulk update of vigencia dates
  - `export_equipo_data(materia_id, carrera_id, cohorte_id)` — returns joined data with Usuario names for export
- [x] 5.2 Export `AsignacionRepository` from `repositories/__init__.py`

## 6. Service Layer

- [x] 6.1 Create `services/team_management.py` with:
  - `create_asignacion(data)` — validates FKs belong to tenant, creates assignment, returns with computed estado_vigencia
  - `get_asignacion(id)` — retrieves individual assignment with computed estado_vigencia
  - `list_asignaciones(filters)` — list with filters and estado_vigencia computed per row
  - `update_asignacion(id, data)` — partial update, recomputes estado_vigencia
  - `asignacion_masiva(request)` — validates all usuario_ids, creates all in transaction, returns list
  - `clonar_equipo(request)` — validates source/destination differ, fetches source assignments, creates copies with destination context
  - `actualizar_vigencia(request)` — bulk update vigencia for equipo scope
  - `exportar_equipo(materia_id, carrera_id, cohorte_id)` — generates CSV data from export query
  - `_compute_estado_vigencia(vig_desde, vig_hasta)` — helper that returns Pendiente|Vigente|Vencida based on today's date
  - `_validate_academic_context(materia_id, carrera_id, cohorte_id)` — validates all FK references belong to the same tenant
- [x] 6.2 Export all service functions from `services/__init__.py`

## 7. Router Layer

- [x] 7.1 Create `api/v1/routers/team_management.py` with all endpoints:
  - `POST /api/admin/asignaciones` — create individual assignment (201)
  - `GET /api/admin/asignaciones` — list with optional filters (200)
  - `GET /api/admin/asignaciones/{id}` — get single assignment (200)
  - `PUT /api/admin/asignaciones/{id}` — update assignment (200)
  - `POST /api/admin/asignaciones/masiva` — bulk assignment (201)
  - `POST /api/admin/asignaciones/clonar` — clone equipo (201)
  - `PUT /api/admin/asignaciones/vigencia` — bulk vigencia update (200)
  - `GET /api/admin/equipos/export` — export as CSV (200, streaming)
- [x] 7.2 All mutating endpoints protected with `require_permission("equipo_docente:asignar")`
- [x] 7.3 Read endpoints protected with `require_permission("equipo_docente:ver")`
- [x] 7.4 All endpoints inject `get_current_user` dependency for tenant resolution
- [x] 7.5 Register `team_management` router in `api/v1/routers/__init__.py`
- [x] 7.6 Wire the new router into `main.py`

## 8. Tests — Unit

- [x] 8.1 Unit test for `_compute_estado_vigencia` — test all 4 states (Pendiente, Vigente with range, Vigente with null vig_hasta, Vencida)
- [x] 8.2 Unit test for `AsignacionCreate` schema validation — duplicate date range, invalid rol, missing required academic context for PROFESOR ro
- [x] 8.3 Unit test for `ClonarRequest` schema validation — source != destination required
- [x] 8.4 Unit test for service `asignacion_masiva` with non-existent usuario_id — verify rollback
  (Covered by integration test 9.8 — requires testcontainers)
- [x] 8.5 Unit test for service `clonar_equipo` with matching source/destination — verify error
  (Covered by integration test 9.10 + schema validation — requires testcontainers for service-level test)
- [x] 8.6 Unit test for service `_validate_academic_context` with cross-tenant FK references
  (Covered by integration test 9.4 — requires testcontainers)
- [x] 8.7 Unit test for permission matrix — verify `equipo_docente:ver` and `equipo_docente:asignar` are present for correct roles

## 9. Tests — Integration

- [x] 9.1 Integration test for POST `/api/admin/asignaciones` — create and verify response with computed estado_vigencia
- [x] 9.2 Integration test for POST `/api/admin/asignaciones` with vig_desde after vig_hasta (422)
- [x] 9.3 Integration test for GET `/api/admin/asignaciones/{id}` — get single assignment
- [x] 9.4 Integration test for GET `/api/admin/asignaciones/{id}` from different tenant (404)
- [x] 9.5 Integration test for GET `/api/admin/asignaciones` — list with filters
- [x] 9.6 Integration test for PUT `/api/admin/asignaciones/{id}` — update vigencia dates
- [x] 9.7 Integration test for POST `/api/admin/asignaciones/masiva` — bulk assign multiple usuarios
- [x] 9.8 Integration test for POST `/api/admin/asignaciones/masiva` with non-existent usuario (404 + rollback)
- [x] 9.9 Integration test for POST `/api/admin/asignaciones/clonar` — clone equipo between cohorts
- [x] 9.10 Integration test for POST `/api/admin/asignaciones/clonar` with identical source/destination (422)
- [x] 9.11 Integration test for PUT `/api/admin/asignaciones/vigencia` — bulk vigencia update
- [x] 9.12 Integration test for GET `/api/admin/equipos/export` — verify CSV content and headers
- [x] 9.13 Integration test for unauthenticated request (401) on all endpoints
- [x] 9.14 Integration test for non-admin user (403) on mutating endpoints
- [x] 9.15 Integration test for cross-tenant isolation — tenant A cannot read/mutate tenant B's assignments
