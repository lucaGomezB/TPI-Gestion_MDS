## Context

The system has tenants and usuarios (C-01), core model mixins and the Usuario identity model with encrypted PII (C-02), and a complete JWT+RBAC auth system with 7 roles (C-03). The RBAC permissions matrix already includes `estructura_academica:gestionar` for ADMIN. However, there are no academic entities to manage — no carreras, cohortes, or materias.

The KB defines the entities in [04_modelo_de_datos.md](../../knowledge-base/04_modelo_de_datos.md) (E1-Carrera, E2-Cohorte, E3-Materia, E16-ProgramaMateria) and the functional capabilities in Épica 5 (F5.1-F5.4) of [06_funcionalidades.md](../../knowledge-base/06_funcionalidades.md).

**Current state (C-03):** Migration 002 is the latest. The `app` module has models for `Tenant`, `Usuario`, `Rol`, `UsuarioRol`, `RefreshToken`, `PasswordResetToken`. No academic models exist.
**Governance level:** ALTO — academic structure is the foundation for all downstream features (equipos docentes, ingesta, liquidaciones).

---

## Goals / Non-Goals

**Goals:**
- Create `Carrera`, `Cohorte`, `Materia`, `ProgramaMateria` SQLAlchemy models following the existing mixin patterns
- Implement tenant-scoped CRUD via REST endpoints under `/api/admin/`
- Enforce `(tenant_id, codigo)` uniqueness for Carrera and Materia
- Enforce `(tenant_id, carrera_id, nombre)` uniqueness for Cohorte
- Support estado transitions (Activa ↔ Inactiva) for Carrera, Cohorte, Materia
- Support temporal validity (`vig_desde`/`vig_hasta`) for Cohorte
- Support PDF upload with storage reference for ProgramaMateria
- Migration 003 creating all 4 tables with proper FKs, indexes, and unique constraints
- Tests covering CRUD, uniqueness violations, multi-tenant isolation, estado transitions

**Non-Goals:**
- **UI/Pagination/filtering** — API returns flat lists. Frontend comes later
- **Bulk operations** — create/update one entity at a time
- **Soft delete for these entities** — Estado field provides Activa/Inactiva. Hard delete is not permitted (audit trail via future audit log); for now, estado=Inactiva is the deactivation mechanism. No `deleted_at` column (these are reference data, not transactional records)
- **File storage service** — In MVP, `referencia_archivo` is a path/URL string. The actual file storage service (S3/MinIO) will be integrated later
- **Asignacion model (E5)** — This C-04 creates the entities that Asignacion references. The Asignacion model itself comes in a future change (C-05+)
- **VersionPadron, Calificacion** — future changes
- **Carrera-Cohorte-Materia assignment** (which matters belong to which carrera+cohorte) — this is modeled via E5 Asignacion and E16 ProgramaMateria in future changes. For now, the catalog is flat

---

## Decisions

### D-01: Model structure — inherit existing mixins consistently

All four models follow the established pattern:

| Mixin | Carrera | Cohorte | Materia | ProgramaMateria |
|-------|---------|---------|---------|-----------------|
| `AppModel` | ✅ UUID id | ✅ UUID id | ✅ UUID id | ✅ UUID id |
| `TimestampMixin` | ✅ created_at, updated_at | ✅ created_at, updated_at | ✅ created_at, updated_at | — uses `cargado_at` instead |
| `AuditMixin` | ✅ estado, deleted_at | ✅ estado, deleted_at | ✅ estado, deleted_at | ❌ (informational, no soft-delete needed) |
| `TenantMixin` | ✅ tenant_id (NOT NULL) | ✅ tenant_id (NOT NULL) | ✅ tenant_id (NOT NULL) | ✅ tenant_id (NOT NULL) |

ProgramaMateria is an informational document registry — it does NOT need soft-delete. Instead it has `cargado_at` as the creation timestamp. Deletion of a ProgramaMateria record is a hard delete (the storage reference becomes orphaned, acceptable for MVP).

### D-02: Estado as `String(20)` matching `EstadoRegistro` enum

The KB defines `estado` as `Activa | Inactiva` for Carrera, Cohorte, Materia. The existing `EstadoRegistro` enum (`Activo`/`Inactivo`) from `models/mixins.py` is used, but these academic entities use the Spanish feminine form `Activa`/`Inactiva` to match the KB. A new `EstadoAcademico` enum with values `Activa`/`Inactiva` is created.

**Alternative considered:** Reuse `EstadoRegistro` directly. Rejected because the feminine form matches the domain language (una carrera activa, una cohorte inactiva). The base `AuditMixin` is still used but `estado` column is overridden with `EstadoAcademico` defaulting to `Activa`.

### D-03: Unique constraints — composite, enforced at DB + service level

| Table | Unique Constraint | Rationale |
|-------|-------------------|-----------|
| `carreras` | `(tenant_id, codigo)` | Each tenant has unique program codes |
| `cohortes` | `(tenant_id, carrera_id, nombre)` | Cohort name must be unique within a carrera of a tenant |
| `materias` | `(tenant_id, codigo)` | Each tenant has a unique subject catalog |

Constraints are enforced at two levels:
1. **Database level** — `UniqueConstraint` in the model
2. **Service level** — The service checks for existing records before insert to return a user-friendly `409 Conflict` instead of a raw DB integrity error

**Alternative considered:** DB-only enforcement (catch IntegrityError). Rejected because the FastAPI exception handler for integrity errors is not domain-aware — it returns a generic 500 or 400. Service-level checks allow specific error messages and align with Clean Architecture.

### D-04: Cohorte temporal validity via `vig_desde`/`vig_hasta`

As defined in [E2-Cohorte](../../knowledge-base/04_modelo_de_datos.md#e2--cohorte):
- `vig_desde`: start date of the cohort's validity (NOT NULL)
- `vig_hasta`: end date (NULL = still open/active cohort)
- `estado`: derived semantic — `Activa` means the cohort is accepting activity, `Inactiva` means it is closed regardless of dates

The validity dates are business information (when the cohort runs) while `estado` controls system behavior (can new data be associated). This separation follows the KB convention in §Convenciones del modelo.

### D-05: Cohorte `anio` as integer year

The `anio` field captures the admission year as a numeric value (e.g., `2025`, `2026`). This is a denormalized convenience field extracted from `vig_desde` for quick filtering and display. It is NOT derived — it must be provided explicitly by the user.

### D-06: ProgramaMateria — storage reference as string, no file handling in MVP

- `referencia_archivo` is a `String(500)` storing an opaque reference (URL, path, or storage key)
- The `POST /api/admin/programas-materia/upload` endpoint accepts a `titulo` + `materia_id` + `carrera_id` + `cohorte_id` + file upload (multipart/form-data)
- In MVP, the uploaded file is saved to a local directory and the path is stored as `referencia_archivo`
- Future: migrate to S3/MinIO and store the object key instead

**Alternative considered:** Store file as base64 in DB. Rejected — bloats the database, no streaming support, no CDN integration.

### D-07: Endpoint structure — flat `/api/admin/` prefix

All endpoints live under `/api/admin/` prefix, not nested under `/api/v1/`. The existing router registration in `main.py` will be updated to include this new module.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/admin/carreras` | POST | Create carrera |
| `/api/admin/carreras` | GET | List all carreras (tenant-scoped) |
| `/api/admin/carreras/{id}` | GET | Get single carrera |
| `/api/admin/carreras/{id}` | PUT | Update carrera (estado, nombre) |
| `/api/admin/cohortes` | POST | Create cohorte |
| `/api/admin/cohortes` | GET | List cohortes (filterable by carrera_id via query param) |
| `/api/admin/cohortes/{id}` | GET | Get single cohorte |
| `/api/admin/cohortes/{id}` | PUT | Update cohorte |
| `/api/admin/materias` | POST | Create materia |
| `/api/admin/materias` | GET | List all materias (tenant-scoped) |
| `/api/admin/materias/{id}` | GET | Get single materia |
| `/api/admin/materias/{id}` | PUT | Update materia (estado, nombre) |
| `/api/admin/programas-materia` | GET | List programas_materia (filterable by materia_id, carrera_id, cohorte_id) |
| `/api/admin/programas-materia/upload` | POST | Upload programa PDF |
| `/api/admin/programas-materia/{id}` | DELETE | Remove programa record |

No `DELETE` endpoints for Carrera/Cohorte/Materia — only estado transition to `Inactiva` (soft deactivation).

### D-08: Permission guard — `estructura_academica:gestionar`

All endpoints are protected by `require_permission("estructura_academica:gestionar")`. Per the RBAC matrix in [user-auth spec](../../openspec/specs/user-auth/spec.md), only ADMIN has this permission. This is intentional — academic structure is tenant-level configuration, not user-level.

### D-09: Alembic migration 003

New file at `alembic/versions/XXXX_add_academic_structure.py`. Migration depends on revision 002 (auth schema). The upgrade creates 4 tables with all FKs, indexes, and unique constraints.

```sql
CREATE TABLE carreras (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activa',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, codigo)
);

CREATE TABLE cohortes (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    carrera_id UUID NOT NULL REFERENCES carreras(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    anio INTEGER NOT NULL,
    vig_desde DATE NOT NULL,
    vig_hasta DATE,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activa',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, carrera_id, nombre)
);

CREATE TABLE materias (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    codigo VARCHAR(20) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Activa',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, codigo)
);

CREATE TABLE programas_materia (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    materia_id UUID NOT NULL REFERENCES materias(id) ON DELETE CASCADE,
    carrera_id UUID NOT NULL REFERENCES carreras(id) ON DELETE CASCADE,
    cohorte_id UUID NOT NULL REFERENCES cohortes(id) ON DELETE CASCADE,
    titulo VARCHAR(255) NOT NULL,
    referencia_archivo VARCHAR(500) NOT NULL,
    cargado_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ix_programas_materia_materia_id ON programas_materia(materia_id);
CREATE INDEX ix_programas_materia_carrera_id ON programas_materia(carrera_id);
CREATE INDEX ix_programas_materia_cohorte_id ON programas_materia(cohorte_id);
```

### D-10: Repository pattern — one repository per entity

Following the established Clean Architecture:
- `CarreraRepository` — CRUD + find_by_codigo
- `CohorteRepository` — CRUD + find_by_nombre_in_carrera
- `MateriaRepository` — CRUD + find_by_codigo
- `ProgramaMateriaRepository` — CRUD + list_by_filters

Each repository inherits from `BaseRepository` and filters by `tenant_id` by default. All queries scope to the tenant resolved from JWT.

### D-11: Pydantic schemas with `extra='forbid'`

Follow the project convention:
- `CarreraCreate`, `CarreraUpdate`, `CarreraResponse`
- `CohorteCreate`, `CohorteUpdate`, `CohorteResponse`
- `MateriaCreate`, `MateriaUpdate`, `MateriaResponse`
- `ProgramaMateriaResponse`, `ProgramaMateriaUploadResponse`
- All with `model_config = ConfigDict(extra='forbid')`
- `CarreraCreate` and `MateriaCreate` validate `codigo` format (uppercase alphanumeric with underscores, 1-20 chars)
- `CohorteCreate` validates `anio` is a 4-digit year and `vig_desde <= vig_hasta` (if vig_hasta provided)

---

## Risks / Trade-offs

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Unique constraint violation returns 500 instead of 409 | Medium | Service layer checks existing records before insert/update, returns `409 Conflict` with clear message |
| File upload without real storage service | Low | Local path storage is acceptable for MVP. Documented as tech debt |
| Carrera/Cohorte/Materia referenced by future entities cannot be deactivated | Low | Estado check: if a carrera has active cohortes, reject deactivation. Service-level validation |
| Migration 003 fails if migration 002 not applied | Low | `depends_on=('002_...',)` in Alembic revision. Alembic enforces dependency ordering |
| Tenant isolation bypass via direct FK joins | Medium | Repositories always scope by `tenant_id`. Mix of `tenant_id` and FK must be validated in service for cross-entity operations (e.g., creating a Cohorte ensures the referenced Carrera belongs to the same tenant) |

---

## Migration Plan

1. Create migration 003 with `depends_on='002_...'`
2. Upgrade runs: 4 CREATE TABLE statements + 3 indexes
3. Downgrade drops all 4 tables
4. Rollforward is safe (additive, no data loss)
