## Context

C-12 implements the system notice board (tablon de avisos) as defined in F3.5, entities E13, and business rules RN-18/RN-19/RN-20. This is a new capability built on top of C-11 (communication queue). The module follows the existing Clean Architecture pattern: Router -> Service -> Repository -> Model -> DB, with tenant scoping via `BaseRepository`, JWT auth via `get_current_user`, and RBAC via `require_permission`.

All models use `AppModel` (UUID PK), and mixins from `app/models/mixins.py`. The `Aviso` model does NOT require `AuditMixin` (avisos have an explicit `activo` boolean field for active/inactive state and can be hard-deleted by admins). The `AcknowledgmentAviso` model is purely a log table with no soft-delete.

## Goals / Non-Goals

**Goals:**
- Implement the `Aviso` and `AcknowledgmentAviso` SQLAlchemy models with migration 008.
- CRUD administrative endpoints at `/api/admin/avisos` for COORDINADOR and ADMIN.
- Public read endpoint `GET /api/avisos` returning avisos visible to the authenticated user, filtered by scope, vigencia, role, and severity (RN-20).
- Ack endpoint `POST /api/avisos/{id}/ack` for users to confirm reading (RN-19).
- Scope filtering: Global, PorMateria, PorCohorte, PorRol, with nullable context fields.
- Vigencia filtering: only avisos where now() is between `inicio_en` and `fin_en` (RN-18).
- Full test coverage: CRUD, scope filtering, vigencia, multi-tenant isolation.

**Non-Goals:**
- Notifications or push delivery when a new aviso is published (out of scope).
- Frontend UI for the avisos tablon (separate concern, will be handled in a future frontend change).
- Rich text rendering or sanitization for `cuerpo` (field is stored as text; rendering is frontend concern).
- Automated expiry cleanup of avisos (finished avisos remain in DB for audit).

## Decisions

### D-01: `Aviso` model uses `activo` flag instead of `AuditMixin`
- **Decision**: The `Aviso` model uses an explicit `activo: bool` column instead of inheriting `AuditMixin` (estado enum + soft delete).
- **Rationale**: Avisos have a natural lifecycle driven by vigencia (`inicio_en`/`fin_en`), not by soft-delete. Admins may want to temporarily deactivate an aviso without losing its vigencia configuration. The `activo` flag is simpler and more domain-appropriate than the generic `AuditMixin`. If hard-delete is needed, the admin endpoint allows it directly.
- **Alternatives considered**: `AuditMixin` with a dedicated status field. Rejected because the domain concepts of "active" and "within vigencia range" are orthogonal — an aviso can be active but outside its vigencia window, or inactive but within it.

### D-02: Scope filtering in repository layer with dynamic WHERE clauses
- **Decision**: The filtering logic for visible avisos (alcance, materia_id, cohorte_id, rol_destino, severidad) is implemented as composable query methods in the repository, invoked by the service.
- **Rationale**: Keeps the service layer focused on business logic (what to filter) and the repository focused on data access (how to filter). The `BaseRepository._stmt()` pattern is extended to add visibility scope.
- **Alternatives considered**: Filtering in service layer via Python list comprehensions after loading all avisos. Rejected because it would load unnecessary data and break at scale.

### D-03: Separate router for admin vs. user-facing endpoints
- **Decision**: Admin CRUD lives under `/api/admin/avisos` with `avisos:publicar` permission. User-facing read and ack live under `/api/avisos` with `avisos:ver` and `avisos:ack` permissions.
- **Rationale**: Clear separation of concerns. Admin endpoints require elevated permissions; user endpoints are accessible to any authenticated user. This follows the existing pattern (e.g., `/api/admin/comunicaciones/{id}/aprobar` in C-11).
- **Alternatives considered**: Single router with permission checks in each handler. Rejected because it couples admin and user concerns in the same file.

### D-04: Acknowledgment is an append-only log
- **Decision**: `AcknowledgmentAviso` records are inserted once and never modified or deleted. The service checks for existing ack before recording a duplicate (idempotency for safe retries).
- **Rationale**: RN-19 requires an audit trail of who confirmed reading. Immutability ensures the record is trustworthy. Idempotency prevents duplicate records from client retries.
- **Alternatives considered**: Updating a `leido_en` timestamp on the aviso-user relationship. Rejected because it loses the audit trail (you cannot see when each confirmation happened).

### D-05: Vigencia filtering uses `AND inicio_en <= now() AND fin_en >= now()`
- **Decision**: The vigencia check is `inicio_en <= now() AND fin_en >= now()`. Both fields are `DateTime(timezone=True)`.
- **Rationale**: This is the standard range check for temporal validity. Using timezone-aware timestamps ensures correct behavior across daylight saving time changes.
- **Alternatives considered**: Using `BETWEEN` operator. Equivalent behavior; the explicit AND form is more readable and easier to extend (e.g., adding a `publicado_en` field later).

## Risks / Trade-offs

- **[Performance] No index on `inicio_en`/`fin_en`** could cause slow queries if the avisos table grows large (hundreds of thousands of rows). Mitigation: add a composite index `(tenant_id, inicio_en, fin_en, activo)` in the migration.
- **[Scope creep] Rich text in `cuerpo`** may require sanitization if HTML is stored. Mitigation: store as plain text for now; rich text rendering can be added in a future change without schema changes.
- **[Multi-tenant] Cross-tenant data leak** if `tenant_id` is not properly scoped. Mitigation: all queries go through `BaseRepository` with `tenant_id` set from JWT, which auto-applies `WHERE tenant_id = ...`. This is the same pattern used across all existing modules.
- **[Idempotency] Duplicate ack records** from concurrent requests. Mitigation: the repository checks for existing ack before inserting. A unique constraint on `(aviso_id, usuario_id)` in the migration provides a DB-level safety net.

## Migration Plan

1. Create migration 008 with tables `avisos` and `acknowledgments_avisos`.
2. Add permission `avisos:publicar` to COORDINADOR and ADMIN roles in `core/permissions.py`.
3. Add permissions `avisos:ver` and `avisos:ack` to all roles (see matrix in `03_actores_y_roles.md`).
4. Register the new `avisos` router in `api/v1/__init__.py`.
5. No rollback complexity: tables are additive, no existing data is modified.

## Open Questions

- Should `cuerpo` support Markdown or plain text only? Decision deferred to apply phase; schema accepts text, format interpretation is frontend concern.
- What is the default sort order for `GET /api/avisos`? Proposal: by `orden` ASC, then `created_at` DESC (highest priority first, newest first for ties). This can be adjusted.
