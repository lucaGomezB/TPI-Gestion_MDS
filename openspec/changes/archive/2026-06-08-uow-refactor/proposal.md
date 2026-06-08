## Why

The current architecture passes `(session: AsyncSession, tenant_id: str)` to every service constructor, which then instantiates its own repository internally. When an operation requires multiple repositories (e.g., importing data involves PadronRepository + AuditRepository), there is no coordination — each service manages its own transaction lifecycle. This leads to inconsistent state on partial failures, duplicated session/tenant plumbing across 16 services, and no clear pattern for atomic multi-repository operations.

A Unit of Work pattern centralizes transaction management, ensures commit-on-success / rollback-on-exception across all repositories participating in the same operation, and reduces constructor boilerplate from two parameters to one.

## What Changes

- **CREATE** `backend/app/core/unit_of_work.py` — `UnitOfWork` async context manager with lazy repository properties for all repository types
- **MODIFY** 13 services to accept `uow: UnitOfWork` instead of `(session, tenant_id)`:
  - CarreraService, CohorteService, MateriaService, ProgramaMateriaService
  - CalificacionesService, PadronService, CommunicationService, EncuentroService
  - GuardiaService, AvisoService, TareaService, TeamManagementService
  - ManualImportService, MoodleSyncService
- **MODIFY** 2 special services to accept `UnitOfWork` instead of direct repository injection:
  - **BREAKING**: AuthService — receives `UnitOfWork` instead of `AuthRepository`
  - **BREAKING**: AuditService — receives `UnitOfWork` instead of `AuditRepository`
- **MODIFY** 14 routers to wrap service calls in `async with UnitOfWork(db, tenant_id) as uow:` context
- **REFACTOR** PadronService to not call `async with self.session.begin()` — UoW owns the transaction
- **REFACTOR** Calificaciones router inline SQLAlchemy queries to use repositories via UoW
- No changes to `email_sender.py`, `template_engine.py`, or any test files

## Capabilities

### New Capabilities
- `unit-of-work`: Centralized database transaction management with lazy-loading repository access, async context manager lifecycle (commit/rollback/close), and automatic tenant scoping via injected tenant_id.

### Modified Capabilities
- `base-repository`: Repository instantiation moves from individual services to the UnitOfWork. Repository interface (session + tenant_id constructor) remains unchanged — only the caller changes.
- `core-models`: No requirement changes — models are unaffected by this refactor.
- `user-auth`: AuthService constructor changes from `AuthRepository` to `UnitOfWork`. Auth behavior and JWT flow unchanged.

## Impact

- **All 16 service files** in `backend/app/services/` — constructor signatures change
- **All 14 router files** in `backend/app/api/v1/routers/` — service instantiation wrapped in UoW context
- **New file**: `backend/app/core/unit_of_work.py`
- **Tests**: No test files modified (existing tests must still pass after refactor)
- **No schema changes**: Database, models, and API contracts remain identical
