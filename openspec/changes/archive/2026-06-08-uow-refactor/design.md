## Context

The activia-trace backend currently passes `(session: AsyncSession, tenant_id: str)` to every service constructor. Each service creates its own repository internally. This works for single-repository operations but fails to coordinate transactions when multiple repositories participate (e.g., PadronService reads/writes from PadronRepository + AuditRepository). Transaction management is scattered: `session.commit()` in routers, `session.flush()` inline in services, `async with session.begin()` in some services.

16 services, 14 routers, and ~20 repositories exist. Every new service duplicates the same plumbing.

## Goals / Non-Goals

**Goals:**
- Create a `UnitOfWork` class with lazy-loading repository properties
- Refactor all 16 services to accept `UnitOfWork` instead of `(session, tenant_id)`
- Refactor all 14 routers to use `async with UnitOfWork(db, tenant_id) as uow:`
- Ensure atomic commit/rollback: no partial writes on failure
- Reduce constructor boilerplate from 2 params to 1
- Zero changes to API contracts, DB schema, or models

**Non-Goals:**
- Changing repository constructors (they still accept `(session, tenant_id)`)
- Migrating tests to UoW (test files remain unchanged)
- Adding new business logic or capabilities
- Changing `email_sender.py` or `template_engine.py` (stateless)

## Decisions

### D-01: Single UnitOfWork class with lazy repository properties

```python
class UnitOfWork:
    def __init__(self, session: AsyncSession, tenant_id: str | None = None):
        self._session = session
        self._tenant_id = tenant_id
        self._repos: dict[str, BaseRepository] = {}

    def _get(self, key: str, factory: Callable) -> Any:
        if key not in self._repos:
            self._repos[key] = factory(self._session, self._tenant_id)
        return self._repos[key]

    @property
    def asignaciones(self) -> AsignacionRepository:
        return self._get("asignaciones", AsignacionRepository)

    # ... one property per repo
```

**Rationale**: Lazy instantiation means repos are only created when actually used. The `_get` cache ensures the same repo instance is reused within a single UoW scope (important for identity map consistency).

**Alternative considered**: Eager initialization in constructor. Rejected because many service methods only use 1-2 repos — eager init wastes resources and complicates testing.

**Alternative considered**: Abstract base `UoWService` with `self.uow` property. Rejected because it requires changing service inheritance, and some services like ManualImportService and AuthService have unique init patterns.

### D-02: UoW owns transaction lifecycle (no commit/rollback in services)

Services **never** call `session.commit()`, `session.rollback()`, or `session.close()`. The UoW context manager handles everything:

```python
async with UnitOfWork(db, tenant_id) as uow:
    service = XxxService(uow)
    result = await service.do_something()
    # uow.__aexit__ commits on success, rolls back on exception
```

**Rationale**: Centralizing transaction control eliminates the risk of a service committing prematurely or forgetting to commit.

**Special case: PadronService** currently uses `async with self.session.begin():` inside `import_roster`. This nested transaction (savepoint) must be removed — the UoW owns the outer transaction.

### D-03: AuthService and AuditService refactored fully

AuthService currently receives `repo: AuthRepository` directly. AuditService receives `repo: AuditRepository`. Both will switch to `uow: UnitOfWork` for consistency.

**Rationale**: Having two different service injection patterns increases cognitive load. The breaking change is acceptable at this stage of the project (pre-v1).

**Trade-off**: AuthService has many methods that call `self.repo.db` directly for low-level operations like `db.flush()` and `db.get()`. These must move to the AuthRepository via new methods, not bypass the UoW.

### D-04: Router changes follow the same pattern

All 14 routers change from:
```python
service = XxxService(db, _get_tenant_id(current_user))
return await service.create(body)
```
To:
```python
async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:
    service = XxxService(uow)
    return await service.create(body)
```

**Rationale**: Consistent, minimal diff, easy to review.

### D-05: Calificaciones router inline queries moved

The Calificaciones router currently has inline SQLAlchemy queries for compute endpoint. These must be moved into a CalificacionesRepository method so they go through UoW.

## Risks / Trade-offs

| Risk | Probability | Mitigation |
|------|-------------|------------|
| AuthService refactor breaks login/refresh flow | Medium | Add integration test for login and refresh before/after. The logic doesn't change — only repo access pattern. |
| PadronService nested transaction removed incorrectly | Low | The `async with self.session.begin()` is a savepoint. Removing it means the outer UoW handles commit. Test import_roster with and without errors. |
| Auditoria service used by other services via AuditService(repo) | Medium | AuditService is instantiated by CalificacionesService and PadronService as `AuditService(AuditRepository(self.session))`. After refactor, these will use `AuditService(self.uow)`. |
| Router diff is large (14 files, ~30 lines each) | Low | Changes are mechanical — search-and-replace with context manager wrapping. Easy to verify. |

## Migration Plan

1. Create `UnitOfWork` class in `core/unit_of_work.py` with ALL repository properties
2. Refactor AuthRepository: add `get_user_by_id()`, `flush()`, `find_usuario_by_id()` methods so AuthService doesn't call `self.repo.db` directly
3. Refactor services: change constructor from `(session, tenant_id)` to `(uow)`, replace `self.repo.x()` with `self.uow.x()`, remove `self.session` references
4. Refactor routers: wrap service calls in `async with UnitOfWork(...)` context
5. Remove `self.session.begin()` from PadronService
6. Run tests: all 535+ unit tests must pass with 0 changes to test files
