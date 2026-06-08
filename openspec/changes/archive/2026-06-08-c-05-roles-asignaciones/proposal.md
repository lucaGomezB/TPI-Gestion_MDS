## Why

The system has academic structure (Carrera, Cohorte, Materia from C-04) and user identity with RBAC (C-03), but there is no way to assign users to roles within an academic context. Before any domain features can operate (padron de alumnos, calificaciones, comunicaciones, liquidaciones), the system needs the assignment model that links a user to a specific role, materia, carrera, cohorte, and comisiones with temporal validity. Without this, there is no concept of "who teaches what" or "who supervises whom."

## What Changes

- Create `Asignacion` SQLAlchemy model: links Usuario x Rol x Materia x Cohorte x Carrera x Comisiones x Vigencia, with `responsable_id` FK for supervisory hierarchy
- Create `POST/GET/PUT /api/admin/asignaciones` — individual CRUD for assignments
- Create `POST /api/admin/asignaciones/masiva` — bulk assignment of multiple docentes to a single academic context
- Create `POST /api/admin/asignaciones/clonar` — clone all assignments from a source (materia x carrera x cohorte) to a destination (RN-12)
- Create `PUT /api/admin/asignaciones/vigencia` — bulk update validity dates for all assignments in a given equipo
- Create `GET /api/admin/equipos/export` — export equipo docente data as downloadable file
- Vigencia fields: `vig_desde`/`vig_hasta` with derived state Vigente/Vencida based on current date (RN-10)
- `responsable_id` FK for reporting hierarchy within the same assignment context (RN-11)
- Permission guards: `equipo_docente:asignar` for COORDINADOR and ADMIN
- Migration 004: table `asignaciones` with composite indexes for efficient querying by usuario, materia, cohorte, and vigencia
- Tests: CRUD individual, bulk assign, clone, vigencia update, export, multi-tenant isolation, permission enforcement

## Capabilities

### New Capabilities
- `team-management`: Full management of teaching team assignments — individual CRUD, bulk assignment of docentes to (materia x carrera x cohorte x rol), clone of equipo between cohortes (RN-12), bulk vigencia modification, and export of equipo docente data. Includes `responsable_id` hierarchy for supervisory chain.

### Modified Capabilities

<!-- No existing specs change their requirements — the new team-management capability is additive. -->

## Impact

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/asignacion.py` | **New** | `Asignacion` model: id, tenant_id, usuario_id (FK), rol (enum), materia_id (FK nullable), carrera_id (FK nullable), cohorte_id (FK nullable), comisiones (JSONB list), responsable_id (FK nullable), vig_desde, vig_hasta, created_at, updated_at |
| `backend/app/models/__init__.py` | Modified | Export Asignacion model |
| `backend/app/schemas/team_management.py` | **New** | Pydantic schemas: AsignacionCreate, AsignacionUpdate, AsignacionResponse, AsignacionMasivaRequest, ClonarRequest, VigenciaRequest with `extra='forbid'` |
| `backend/app/repositories/team_management.py` | **New** | AsignacionRepository with tenant-scoped queries, bulk operations, clone logic |
| `backend/app/services/team_management.py` | **New** | Service layer: CRUD logic, bulk assignment, clone validation, vigencia update, export generation |
| `backend/app/api/v1/routers/team_management.py` | **New** | Router with endpoints for asignaciones CRUD, masiva, clonar, vigencia, export equipos |
| `backend/app/api/v1/routers/__init__.py` | Modified | Register team management router |
| `backend/app/core/permissions.py` | Modified | Add `equipo_docente:asignar` permission to COORDINADOR and ADMIN roles |
| `backend/alembic/versions/` | **New** | Migration 004: asignaciones table with composite indexes |
| `backend/tests/` | **New** | Unit + integration tests for CRUD, bulk, clone, vigencia, export, multi-tenant isolation |
