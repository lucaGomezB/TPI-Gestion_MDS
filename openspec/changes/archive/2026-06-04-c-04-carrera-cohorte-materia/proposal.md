## Why

The system currently has multi-tenant foundation (C-01), core models (C-02), and authentication/RBAC (C-03) — but no academic structure yet. Before any domain features can operate (ingesta, equipos docentes, liquidaciones), the system needs the base academic entities that define what a tenant teaches and how courses are organized: carreras (programs), cohortes (cohorts), materias (subjects catalog), and programas_materia (subject syllabi documents).

## What Changes

- Create `Carrera`, `Cohorte`, `Materia`, and `ProgramaMateria` SQLAlchemy models with proper mixin hierarchy, unique constraints, and cascade rules
- Create `POST /api/admin/carreras`, `GET /api/admin/carreras`, `GET /api/admin/carreras/{id}`, `PUT /api/admin/carreras/{id}` — CRUD for academic programs
- Create `POST /api/admin/cohortes`, `GET /api/admin/cohortes`, `GET /api/admin/cohortes/{id}`, `PUT /api/admin/cohortes/{id}` — CRUD for cohorts within a carrera
- Create `POST /api/admin/materias`, `GET /api/admin/materias`, `GET /api/admin/materias/{id}`, `PUT /api/admin/materias/{id}` — CRUD for the tenant-wide subject catalog
- Create `GET /api/admin/programas-materia`, `POST /api/admin/programas-materia/upload`, `DELETE /api/admin/programas-materia/{id}` — upload and manage syllabi PDFs
- Migration 003: tables carreras, cohortes, materias, programas_materia with indexes, unique constraints, and FKs
- All endpoints protected via `require_permission("estructura_academica:gestionar")` (ADMIN only)
- Multi-tenant isolation: every query filters by `tenant_id` from JWT
- PII encryption for `referencia_archivo` in ProgramaMateria is NOT needed (it is a storage reference, not PII)
- Tests: CRUD operations, unique constraint violations, multi-tenant isolation, estado transitions

## Capabilities

### New Capabilities
- `academic-structure`: Tenant-scoped academic structure management — carreras (programs) with unique code, cohortes (cohorts) with temporal validity linked to a carrera, materias (subjects) as a unique tenant-wide catalog, and programas_materia (syllabi documents) linked to a materia+carrera+cohorte combination. CRUD endpoints protected by `estructura_academica:gestionar` permission.

### Modified Capabilities

<!-- No existing specs change their requirements — the new academic-structure capability is additive. -->

## Impact

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/carrera.py` | **New** | `Carrera` model: id, tenant_id, codigo (unique per tenant), nombre, estado, created_at, updated_at |
| `backend/app/models/cohorte.py` | **New** | `Cohorte` model: id, tenant_id, carrera_id (FK), nombre, anio, vig_desde, vig_hasta, estado, created_at, updated_at |
| `backend/app/models/materia.py` | **New** | `Materia` model: id, tenant_id, codigo (unique per tenant), nombre, estado, created_at, updated_at |
| `backend/app/models/programa_materia.py` | **New** | `ProgramaMateria` model: id, tenant_id, materia_id (FK), carrera_id (FK), cohorte_id (FK), titulo, referencia_archivo, cargado_at |
| `backend/app/models/__init__.py` | Modified | Export new models |
| `backend/app/schemas/academic_structure.py` | **New** | Pydantic schemas for all request/response DTOs |
| `backend/app/repositories/academic_structure.py` | **New** | Repositories: Carrera, Cohorte, Materia, ProgramaMateria with tenant-scoped queries |
| `backend/app/services/academic_structure.py` | **New** | Service layer: CRUD logic, uniqueness validation, estado transitions |
| `backend/app/api/v1/routers/academic_structure.py` | **New** | Router with endpoints for carreras, cohortes, materias, programas_materia |
| `backend/app/api/v1/routers/__init__.py` | Modified | Register academic structure router |
| `backend/alembic/versions/` | **New** | Migration 003: carreras, cohortes, materias, programas_materia tables |
| `backend/tests/` | **New** | Unit + integration tests for academic structure CRUD, uniqueness, isolation |
