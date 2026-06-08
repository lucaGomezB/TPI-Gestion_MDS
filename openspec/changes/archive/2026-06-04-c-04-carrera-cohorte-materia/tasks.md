## 1. Model Layer

- [x] 1.1 Create `EstadoAcademico` enum in `models/mixins.py` with values `Activa`/`Inactiva` (feminine form for academic entities)
- [x] 1.2 Create `Carrera` model in `models/carrera.py`: id, tenant_id (NOT NULL FK), codigo (unique per tenant), nombre, estado (EstadoAcademico, default Activa), created_at, updated_at. Inherits AppModel + TimestampMixin + TenantMixin. Override tenant_id with explicit FK and nullable=False. Override estado with EstadoAcademico.
- [x] 1.3 Create `Cohorte` model in `models/cohorte.py`: id, tenant_id (NOT NULL FK), carrera_id (FK), nombre, anio (Integer), vig_desde (Date), vig_hasta (Date, nullable), estado (EstadoAcademico), created_at, updated_at. UniqueConstraint on (tenant_id, carrera_id, nombre).
- [x] 1.4 Create `Materia` model in `models/materia.py`: id, tenant_id (NOT NULL FK), codigo (unique per tenant), nombre, estado (EstadoAcademico), created_at, updated_at. UniqueConstraint on (tenant_id, codigo).
- [x] 1.5 Create `ProgramaMateria` model in `models/programa_materia.py`: id, tenant_id (NOT NULL FK), materia_id (FK), carrera_id (FK), cohorte_id (FK), titulo, referencia_archivo, cargado_at (server default now()). No AuditMixin — hard delete only.
- [x] 1.6 Update `models/__init__.py` to export all new models and the new enum

## 2. Migration 004 — Academic Structure Schema

- [x] 2.1 Generate Alembic migration (revision 004, depends_on revision 003) with 4 CREATE TABLE statements matching the design
- [x] 2.2 Add indexes: ix_programas_materia_materia_id, ix_programas_materia_carrera_id, ix_programas_materia_cohorte_id
- [x] 2.3 Implement `downgrade()` — DROP TABLE programas_materia, materias, cohortes, carreras
- [ ] 2.4 Run migration and verify against test database — **Requires PostgreSQL**

## 3. Pydantic Schemas

- [x] 3.1 Create `schemas/academic_structure.py` with all schemas (all with `extra='forbid'`):
- [x] 4.1 Create `repositories/academic_structure.py` with:
- [x] 4.2 Export all repositories from `repositories/__init__.py`
- [x] 5.1 Create `services/academic_structure.py` with:
- [x] 5.2 Export all services from `services/__init__.py`
- [x] 6.1 Create `api/v1/routers/academic_structure.py` with all endpoints (17 total):
- [x] 6.2 All endpoints protected with `require_permission("estructura_academica:gestionar")` + `get_current_user`
- [x] 6.3 Register `academic_structure` router in `api/v1/routers/__init__.py`
- [x] 6.4 Wire the new router into `main.py`

## 7. Tests — Unit

- [x] 7.1 Unit test for EstadoAcademico enum values
- [x] 7.2 Unit test for codigo uppercasing validation in CarreraCreate and MateriaCreate schemas
- [x] 7.3 Unit test for CohorteCreate date range validation (vig_desde <= vig_hasta)
- [x] 7.4 Unit test for CarreraService create with duplicate codigo
- [x] 7.5 Unit test for MateriaService create with duplicate codigo
- [x] 7.6 Unit test for CohorteService create with duplicate nombre in same carrera
- [x] 7.7 Unit test for CohorteService create with cross-tenant carrera_id
- [x] 7.8 Unit test for CarreraService deactivate with active cohortes

## 8. Tests — Integration

- [x] 8.1 Integration test for POST `/api/admin/carreras` — create and verify response — **Requires PostgreSQL**
- [x] 8.2 Integration test for POST `/api/admin/carreras` with duplicate codigo (409) — **Requires PostgreSQL**
- [x] 8.3 Integration test for GET `/api/admin/carreras` — list tenant-scoped — **Requires PostgreSQL**
- [x] 8.4 Integration test for GET `/api/admin/carreras/{id}` — different tenant returns 404 — **Requires PostgreSQL**
- [x] 8.5 Integration test for PUT `/api/admin/carreras/{id}` — update estado to Inactiva — **Requires PostgreSQL**
- [x] 8.6 Integration test for POST `/api/admin/cohortes` — create with vig_desde and vig_hasta — **Requires PostgreSQL**
- [x] 8.7 Integration test for POST `/api/admin/cohortes` with duplicate nombre (409) — **Requires PostgreSQL**
- [x] 8.8 Integration test for POST `/api/admin/materias` — create with uppercase codigo — **Requires PostgreSQL**
- [x] 8.9 Integration test for POST `/api/admin/materias` with duplicate codigo (409) — **Requires PostgreSQL**
- [x] 8.10 Integration test for POST `/api/admin/programas-materia/upload` — upload PDF — **Requires PostgreSQL**
- [x] 8.11 Integration test for DELETE `/api/admin/programas-materia/{id}` — **Requires PostgreSQL**
- [x] 8.12 Integration test for cross-tenant isolation — user A cannot access user B's entities — **Requires PostgreSQL**
- [x] 8.13 Integration test for non-admin user returns 403 on all endpoints — **Requires PostgreSQL**
- [x] 8.14 Integration test for unauthenticated request returns 401 on all endpoints — **Requires PostgreSQL**
