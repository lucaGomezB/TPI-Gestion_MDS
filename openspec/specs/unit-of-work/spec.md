# Unit of Work

> **Purpose**: Define the `UnitOfWork` class for coordinated transaction management across multiple repositories. All services consume repositories through a shared UoW instance that owns the transaction lifecycle.

---

## Requirements

### Requirement: The system SHALL provide a UnitOfWork class for coordinated transaction management

The system MUST provide a `UnitOfWork` class in `core/unit_of_work.py` that wraps an `AsyncSession` and `tenant_id`, managing the transaction lifecycle and exposing all repository types as lazy-loading properties.

- The class MUST implement `__aenter__` and `__aexit__` async context manager protocol
- On `__aenter__`: return `self`
- On `__aexit__` with no exception: commit the session
- On `__aexit__` with exception: rollback the session
- On `__aexit__` always: close the session
- Constructor signature: `__init__(self, session: AsyncSession, tenant_id: str | None = None)`
- Each repository property MUST instantiate the repository on first access with `self._session` and `self._tenant_id`
- The class MUST expose properties for ALL repository types: AsignacionRepository, AuditRepository, AuthRepository, AvisoRepository, AcknowledgmentAvisoRepository, CalificacionesRepository, CarreraRepository, CohorteRepository, ComunicacionRepository, GuardiaRepository, ImportRepository, InstanciaEncuentroRepository, LoteRepository, MateriaRepository, MoodleSyncRepository, PadronRepository, ProgramaMateriaRepository, SlotEncuentroRepository, SyncLogRepository, TareaRepository

#### Scenario: Commit on success

- **WHEN** the `with` block completes without an exception
- **THEN** `await session.commit()` MUST be called
- **THEN** `await session.close()` MUST be called

#### Scenario: Rollback on exception

- **WHEN** the `with` block raises an exception
- **THEN** `await session.rollback()` MUST be called
- **THEN** `await session.close()` MUST be called
- **THEN** the exception MUST be re-raised

#### Scenario: Repository properties are lazy

- **WHEN** a `UnitOfWork` is instantiated but no repository property is accessed
- **THEN** no repository constructor SHALL be called
- **THEN** the first access to a property SHALL instantiate that repository

#### Scenario: Tenant_id propagates to repositories

- **WHEN** `UnitOfWork(db, tenant_id="tenant-a")` is created and a repository property is accessed
- **THEN** the repository MUST be instantiated with `tenant_id="tenant-a"`

#### Scenario: Multiple repositories share the same session

- **WHEN** two different repository properties are accessed on the same `UnitOfWork` instance
- **THEN** both repositories MUST reference the same `AsyncSession` instance

### Requirement: Services SHALL accept UnitOfWork instead of (session, tenant_id)

Every service in `app/services/` MUST change its constructor to accept a single `uow: UnitOfWork` parameter instead of `session: AsyncSession, tenant_id: str`.

- All method-level `self.session`, `self.tenant_id`, and `self.repo` references MUST be replaced with `self.uow.<repository_property>`
- The public method signatures (name, parameters excluding constructor, return types) SHALL NOT change
- Services SHALL NOT call `session.commit()`, `session.rollback()`, or `session.close()` directly

#### Scenario: Service uses repository from UoW

- **WHEN** a service method accesses `self.uow.carreras`
- **THEN** it MUST receive a `CarreraRepository` instance with the UoW's session and tenant_id
- **THEN** the repository SHALL be fully functional for CRUD operations

#### Scenario: PadronService does not manage its own transaction

- **WHEN** PadronService performs an import operation
- **THEN** it SHALL NOT call `self.session.begin()`
- **THEN** internal savepoints SHALL use `self.uow.session.begin_nested()`

### Requirement: Routers SHALL wrap service calls in UnitOfWork context

Every router endpoint that instantiates a service MUST wrap the call in:

```python
async with UnitOfWork(db, tenant_id) as uow:
    service = XxxService(uow)
    return await service.method(...)
```

#### Scenario: Router creates UoW with tenant_id

- **WHEN** a router endpoint handler creates a service
- **THEN** it MUST use `async with UnitOfWork(db, _get_tenant_id(current_user)) as uow:`
- **THEN** the service MUST be instantiated with `uow`
- **THEN** the service method call MUST be inside the `with` block
