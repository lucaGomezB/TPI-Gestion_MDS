## MODIFIED Requirements

### Requirement: The system SHALL provide a generic BaseRepository[T] with automatic tenant scoping

The system MUST provide a generic `BaseRepository[T]` class in `repositories/base.py`. This repository MUST:

- Accept a `session: AsyncSession` and an optional `tenant_id: str | None`
- Automatically scope all queries by `tenant_id` for models that have the attribute
- Provide the following CRUD operations:
  - `get(id: str) -> T | None` — Retrieve by primary key
  - `list(**filters) -> list[T]` — List with optional equality filters
  - `create(data: dict | BaseModel) -> T` — Create a new entity
  - `update(id: str, data: dict | BaseModel) -> T | None` — Partially update an entity
  - `soft_delete(id: str) -> None` — Mark as Inactive with deleted_at timestamp

**Update**: Repository instantiation now occurs exclusively through the `UnitOfWork` class. Individual services no longer create repository instances directly. Services access repositories via `self.uow.<repository_property>` instead of instantiating them in their `__init__` methods.

This change does NOT modify the repository interface — only the caller that instantiates the repository. The constructor signature `__init__(self, session: AsyncSession, tenant_id: str | None = None)` remains the same.

#### Scenario: Repository is instantiated via UnitOfWork

- **WHEN** a service accesses `self.uow.carreras`
- **THEN** the repository SHALL be instantiated with the session and tenant_id from the UoW
- **THEN** tenant scoping SHALL behave identically to direct instantiation
