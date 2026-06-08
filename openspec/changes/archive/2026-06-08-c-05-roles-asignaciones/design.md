## Context

The system has core identity models (C-02), RBAC authentication (C-03), and the academic structure entities — Carrera, Cohorte, Materia, ProgramaMateria (C-04, archived). The permissions matrix in `core/permissions.py` already includes `equipo_docente:asignar` for COORDINADOR and ADMIN roles. However, there is no model that links users to roles within an academic context (materia, carrera, cohorte, comisiones).

The KB defines Asignacion in [04_modelo_de_datos.md](../../knowledge-base/04_modelo_de_datos.md) (E5), the functional capabilities in [06_funcionalidades.md](../../knowledge-base/06_funcionalidades.md) (Epica 4 — Gestion de Equipos Docentes, F4.1-F4.7), and the business rules in [05_reglas_de_negocio.md](../../knowledge-base/05_reglas_de_negocio.md) (RN-10, RN-11, RN-12, RN-30).

**Current state (C-04):** Migration 003 is the latest. The `app` module has models for Carrera, Cohorte, Materia, ProgramaMateria. No Asignacion model exists.
**Governance level:** ALTO — this is the pivotal change that bridges user identity with academic context. All downstream features (padron, calificaciones, comunicaciones, liquidaciones) depend on this model.

---

## Goals / Non-Goals

**Goals:**
- Create `Asignacion` SQLAlchemy model linking Usuario x Rol x Materia x Cohorte x Carrera x Comisiones with temporal validity
- Implement `responsable_id` FK for supervisory hierarchy (quien supervisa al asignado)
- Create individual CRUD endpoints: POST/GET/PUT `/api/admin/asignaciones`
- Create bulk assignment endpoint: POST `/api/admin/asignaciones/masiva`
- Create clone endpoint: POST `/api/admin/asignaciones/clonar` (RN-12)
- Create bulk vigencia modification: PUT `/api/admin/asignaciones/vigencia`
- Create equipo export: GET `/api/admin/equipos/export`
- Vigencia fields with derived state (Vigente/Vencida) computed at query time (RN-10)
- Migration 004: table `asignaciones` with composite indexes
- Permission guards: `equipo_docente:asignar` for COORDINADOR and ADMIN
- Audit logging for all mutating operations
- Tests: individual CRUD, bulk assign, clone, vigencia update, export, multi-tenant isolation

**Non-Goals:**
- **UI/Frontend** — API-only change. Frontend comes in C-23 (frontend-equipos)
- **Pagination on list endpoints** — API returns flat lists for MVP
- **Soft delete for Asignacion** — The row is preserved for historical tracking. Deactivation is handled via `vig_hasta` (date-based). No estado column needed — Asignacion is a temporal record, not a stateful entity
- **Role catalog management** — Roles are defined in the existing Rol model from C-03; this change uses a string enum matching the existing role names
- **Integration with external systems (Moodle)** — This change only models assignments internally. Sync to Moodle comes in a future change
- **Reporting/dashboard** — Export is a flat CSV/JSON. Full reporting comes later
- **Comision validation** — Comisiones are stored as JSONB text list; no validation that a comision exists in the padron (that comes in C-06)

---

## Decisions

### D-01: Model structure — Asignacion as a temporal link entity

Unlike Carrera/Cohorte/Materia (which have `estado` with Activa/Inactiva), Asignacion is a **temporal record** whose state is derived from dates. The model follows this structure:

| Mixin | Asignacion |
|-------|------------|
| `AppModel` | UUID id |
| `TimestampMixin` | created_at, updated_at |
| `TenantMixin` | tenant_id (NOT NULL) |
| `AuditMixin` | **NOT used** — state is derived from vigencia dates, not estado field |

The model does NOT inherit `AuditMixin` because:
- There is no `estado` column (soft-delete is not applicable to temporal records)
- An expired assignment is preserved in the historical record (it is not "deleted" or "inactive")
- The derived state (Vigente/Vencida) is computed at query time, not stored

**Alternative considered:** Add an `estado` column with Vigente/Vencida. Rejected because it would require a background job or trigger to update as dates pass, adding complexity without value. Computation at query time is trivial (compare current date against vig_desde/vig_hasta).

**Alternative considered:** Use `AuditMixin` and set estado to Activo by default. Rejected because mixing date-based validity with a separate estado field creates ambiguity: which one determines if the assignment is active?

### D-02: Vigencia fields naming — `vig_desde`/`vig_hasta`

Following the KB convention from §Convenciones del modelo:
- `vig_desde`: start of validity (NOT NULL)
- `vig_hasta`: end of validity (NULL = indefinitely valid)
- Derived state: Vigente if current date is within `[vig_desde, vig_hasta)` or `[vig_desde, inf)` if vig_hasta is NULL
- `vig_hasta` excludes upper bound semantics: an assignment with `vig_hasta='2026-06-07'` is valid up to and including 2026-06-06

The KB uses `desde`/`hasta` in E5. Using `vig_desde`/`vig_hasta` instead of just `desde`/`hasta` for consistency with Cohorte's temporal fields (which use `vig_` prefix) and other models. This avoids ambiguity with other `desde` fields in future entities.

### D-03: Comisiones as JSONB `list[str]`

The `comisiones` field stores a list of comision names/identifiers as a PostgreSQL JSONB array:

```python
comisiones: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
```

**Alternative considered:** Normalize comisiones into a separate `AsignacionComision` table. Rejected because:
- Comisiones are simple string identifiers (e.g., "A", "B", "C1") with no additional attributes
- A join table would add complexity for bulk operations (clone, masiva)
- JSONB allows atomic updates and is queryable via Postgres JSON operators
- The list is typically small (1-5 items per assignment)

The default value is an empty list `[]`, meaning the assignment covers no specific comisiones (all comisiones for the materia/cohorte).

### D-04: Nullable academic context FKs

The model has nullable FKs for `materia_id`, `carrera_id`, `cohorte_id`:

- **All null**: The assignment is a tenant-level role (e.g., an ADMIN or FINANZAS user with system-wide scope)
- **Only tenant scope**: A COORDINADOR or NEXO might be assigned at tenant level without a specific materia
- **materia_id + carrera_id + cohorte_id**: The typical case — a PROFESOR or TUTOR assigned to a specific academic unit

The service layer validates that at least one academic context FK is provided when the role requires it (PROFESOR, TUTOR require materia_id; ADMIN, FINANZAS do not).

### D-05: Responsable_id FK for supervisory hierarchy

`responsable_id` is a self-referencing FK to `usuarios.id` (NOT to Asignacion). This models the reporting chain per RN-11:

- A PROFESOR assigned to a materia can have `responsable_id` pointing to a COORDINADOR Usuario
- Multiple assignments can share the same `responsable_id`
- The FK is nullable (a top-level coordinator or admin has no supervisor in this context)

**Alternative considered:** Make `responsable_id` an FK to `asignaciones.id` (the coordinator's specific assignment). Rejected because:
- It couples two assignments together — if the coordinator's assignment changes, all dependent assignments would need updating
- The KB defines it as FK to Usuario, not to Asignacion

### D-06: Derived vigencia state — computed at service level

The `estado_vigencia` field from the KB (E5) is **not stored**. Instead, the service layer computes it when returning responses:

```python
def _compute_vigencia(vig_desde: date, vig_hasta: date | None, today: date) -> str:
    if vig_hasta is not None and today > vig_hasta:
        return "Vencida"
    if today < vig_desde:
        return "Pendiente"  # Future validity, not yet active
    return "Vigente"
```

Three states:
- **Pendiente**: Current date is before `vig_desde` (assignment not yet active)
- **Vigente**: Current date is within `[vig_desde, vig_hasta]` or `[vig_desde, inf)` if `vig_hasta` is NULL
- **Vencida**: Current date is after `vig_hasta`

The response schema includes a computed `estado_vigencia` field derived at serialization time.

### D-07: Bulk assignment endpoint design

`POST /api/admin/asignaciones/masiva` accepts:

```json
{
  "usuario_ids": ["uuid1", "uuid2", ...],
  "rol": "PROFESOR",
  "materia_id": "uuid",
  "carrera_id": "uuid",
  "cohorte_id": "uuid",
  "comisiones": ["A", "B"],
  "responsable_id": "uuid",
  "vig_desde": "2026-03-01",
  "vig_hasta": "2026-12-31"
}
```

The service:
1. Validates all `usuario_ids` exist in the same tenant
2. Validates the academic context FKs exist and belong to the tenant
3. Creates one `Asignacion` per `usuario_id` with the common parameters
4. Returns a list of created assignments with their IDs
5. If any validation fails, the entire operation rolls back (transactional)

This supports RN-30 (autocompletado en asignacion masiva) — the search for usuarios is delegated to the UsuarioRepository with a `search_by_name` method that the frontend can query separately.

### D-08: Clone endpoint design

`POST /api/admin/asignaciones/clonar` accepts:

```json
{
  "origen_materia_id": "uuid",
  "origen_carrera_id": "uuid",
  "origen_cohorte_id": "uuid",
  "destino_materia_id": "uuid",
  "destino_carrera_id": "uuid",
  "destino_cohorte_id": "uuid"
}
```

The service (per RN-12):
1. Fetches all active (Vigente) assignments for the source (materia x carrera x cohorte)
2. Creates a copy of each with the destination academic context
3. Preserves: `usuario_id`, `rol`, `comisiones`, `responsable_id`
4. Sets `vig_desde` and `vig_hasta` to the destination cohorte's vigencia (or today if cohorte has none)
5. Returns count of cloned assignments

Validation: Destination must differ from source (no self-clone). All destination FKs must exist in the same tenant.

### D-09: Bulk vigencia modification

`PUT /api/admin/asignaciones/vigencia` accepts:

```json
{
  "materia_id": "uuid",
  "carrera_id": "uuid",
  "cohorte_id": "uuid",
  "vig_desde": "2026-03-01",
  "vig_hasta": "2026-12-31"
}
```

Updates all assignments matching the academic context filter. This is useful at the start of a new period: the coordinator extends all assignments by updating the vig_hasta date in one operation.

### D-10: Equipo export endpoint

`GET /api/admin/equipos/export?materia_id=X&carrera_id=Y&cohorte_id=Z`

Returns a CSV file with columns:
- docente_nombre, docente_apellidos, docente_email, rol, comisiones, responsable_nombre, vig_desde, vig_hasta, estado_vigencia

The export is generated server-side as a streaming CSV response with `Content-Disposition: attachment`.

### D-11: Permission guards — `equipo_docente:asignar`

All mutating endpoints (POST, PUT) are protected with `require_permission("equipo_docente:asignar")`. Per the RBAC matrix, this permission is held by COORDINADOR and ADMIN. Read-only endpoints (GET) are protected with `require_permission("equipo_docente:ver")` — COORDINADOR, ADMIN, and potentially the assigned user themselves.

A new permission `equipo_docente:ver` will be added to the permission matrix for read access (currently only `equipo_docente:asignar` exists). This enables the "Mis equipos" view in F4.2.

### D-12: Rol as enum string matching existing roles

The `rol` field in Asignacion uses the same string values as the existing roles from C-03 (`PROFESOR`, `TUTOR`, `COORDINADOR`, `NEXO`, `ADMIN`, `FINANZAS`). A new Pydantic enum (`RolDocente`) is created for schema validation, but the DB stores raw strings for consistency with the existing `usuario_roles` table pattern.

### D-13: Alembic migration 004

New file at `alembic/versions/XXXX_add_asignaciones.py`. Migration depends on revision 003 (academic structure schema).

```sql
CREATE TABLE asignaciones (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    rol VARCHAR(20) NOT NULL,
    materia_id UUID REFERENCES materias(id) ON DELETE SET NULL,
    carrera_id UUID REFERENCES carreras(id) ON DELETE SET NULL,
    cohorte_id UUID REFERENCES cohortes(id) ON DELETE SET NULL,
    comisiones JSONB NOT NULL DEFAULT '[]',
    responsable_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    vig_desde DATE NOT NULL,
    vig_hasta DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Composite indexes for query patterns
CREATE INDEX ix_asignaciones_tenant_rol ON asignaciones(tenant_id, rol);
CREATE INDEX ix_asignaciones_usuario_id ON asignaciones(usuario_id);
CREATE INDEX ix_asignaciones_materia_id ON asignaciones(materia_id);
CREATE INDEX ix_asignaciones_cohorte_id ON asignaciones(cohorte_id);
CREATE INDEX ix_asignaciones_responsable_id ON asignaciones(responsable_id);
CREATE INDEX ix_asignaciones_vigencia ON asignaciones(tenant_id, vig_desde, vig_hasta);
```

Indexes cover the main query patterns:
- Filter by tenant + rol (list all profesores)
- Filter by usuario (mis equipos view)
- Filter by materia (equipo docente of a subject)
- Filter by cohorte (equipo docente of a cohort)
- Filter by responsable (who reports to whom)
- Filter by tenant + vigencia range (current assignments)

### D-14: Repository pattern — single AsignacionRepository

Following the established Clean Architecture:
- `AsignacionRepository` — CRUD + find_by_filters, bulk_create, find_by_equipo, delete_by_filters
- Inherits from `BaseRepository`
- Custom methods for equipo-scoped queries (filter by materia + carrera + cohorte)

### D-15: Pydantic schemas with `extra='forbid'`

Following the project convention:
- `AsignacionCreate`, `AsignacionUpdate`, `AsignacionResponse` — individual CRUD
- `AsignacionMasivaRequest`, `AsignacionMasivaResponse` — bulk assignment
- `ClonarRequest`, `ClonarResponse` — clone operation
- `VigenciaRequest`, `VigenciaResponse` — bulk vigencia update
- `EquipoExportRow` — export row representation
- All with `model_config = ConfigDict(extra='forbid')`
- Role validation via `RolDocente` enum
- Date validation: `vig_desde` must be provided; `vig_hasta` must be >= `vig_desde` if provided

---

## Risks / Trade-offs

| Risk | Probability | Mitigation |
|------|-------------|------------|
| JSONB comisiones list grows unbounded | Low | Document that comisiones are simple identifiers. If they become complex, normalize to a join table in a future change |
| Date-based vigencia race condition | Low | Service computes state against `date.today()` at query time. No caching of derived state. UTC dates throughout |
| Clone copies too many or too few assignments | Medium | Clear filter criteria: only Vigente assignments from source scope. Destination must differ from source to prevent accidental overwrites |
| Foreign key errors during migracion 004 | Low | `ON DELETE SET NULL` for most FKs ensures referenced entity deletion doesn't cascade-destroy assignments. `usuario_id` and `tenant_id` use CASCADE |
| Missing `equipo_docente:ver` permission | Medium | Add to permission matrix in this change to enable read-only access for assigned users |
| Export performance with large teams | Low | For MVP, no pagination. If teams exceed 500+ assignments, add streaming/chunked response in a future change |
| Roles enum must stay in sync with C-03 roles | Low | Rol values are validated at the service layer against a hardcoded list. If C-03 adds new roles, this must be updated. Documented as maintenance contract |
| Tenant isolation breach via responsable_id | Medium | Service validates that responsable_id's Usuario belongs to the same tenant. Repository scopes all queries by tenant_id |

---

## Migration Plan

1. Create migration 004 with `depends_on='003_...'` (academic structure revision)
2. Upgrade runs: 1 CREATE TABLE + 6 indexes
3. Downgrade drops the `asignaciones` table
4. Rollforward is safe (additive, no data loss)
5. No data migration needed (new table, no existing data to transform)
