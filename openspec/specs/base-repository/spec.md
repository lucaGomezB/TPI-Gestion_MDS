# Base Repository

> **Purpose**: Define the generic `BaseRepository[T]` pattern with automatic tenant scoping, soft-delete filtering, and standard CRUD operations. All domain-specific repositories build upon this base.

---

## Requirements

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

#### Scenario: Get by ID with tenant scope
- **WHEN** `repo.get("some-id")` is called with `tenant_id="tenant-a"`
- **THEN** the generated query MUST include `WHERE model.id = 'some-id' AND model.tenant_id = 'tenant-a'`

#### Scenario: List returns only tenant-scoped records
- **WHEN** `repo.list()` is called with `tenant_id="tenant-a"`
- **THEN** the query MUST include `WHERE model.tenant_id = 'tenant-a' AND model.estado != 'Inactivo'`
- **THEN** records from other tenants MUST NOT be included

#### Scenario: Create sets tenant_id automatically
- **WHEN** `repo.create({"nombre": "test"})` is called with `tenant_id="tenant-a"`
- **THEN** the created record MUST have `tenant_id = 'tenant-a'`

#### Scenario: Soft delete sets estado and deleted_at
- **WHEN** `repo.soft_delete("some-id")` is called
- **THEN** the record's `estado` MUST be `'Inactivo'`
- **THEN** the record's `deleted_at` MUST be set to a non-null timestamp
- **THEN** the record SHALL NOT appear in subsequent `list()` calls

#### Scenario: Update only modifies specified fields
- **WHEN** `repo.update("some-id", {"nombre": "New Name"})` is called
- **THEN** only the `nombre` column SHALL be updated
- **THEN** the `updated_at` column SHALL be refreshed automatically (via onupdate)
- **THEN** other columns SHALL retain their original values

#### Scenario: TenantRepository for Tenant model (no tenant_id)
- **WHEN** a special `TenantRepository` subclass is used for the `Tenant` model (which has no `tenant_id`)
- **THEN** the repository SHALL skip tenant scoping
- **THEN** `list()` SHALL return all tenants without filtering
