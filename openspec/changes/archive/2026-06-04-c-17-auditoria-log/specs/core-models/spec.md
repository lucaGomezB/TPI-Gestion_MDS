# Core Models — Delta

> **Delta spec for C-17 auditoria-log**: Adds the `AuditLog` model (E-AUD) to the domain model catalog. No existing requirements are modified or removed.

---

## ADDED Requirements

### Requirement: The system SHALL have an AuditLog model for immutable audit records

The system MUST provide an `AuditLog` SQLAlchemy model representing an immutable record of a significant action performed by a user in the system (E-AUD). The model inherits from `AppModel` and `TenantMixin` but SHALL NOT inherit `TimestampMixin` or `AuditMixin` (no updated_at, no soft delete — the record is append-only).

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated via uuid4 |
| `tenant_id` | UUID (string) | FK → tenants.id, NOT NULL |
| `fecha_hora` | DateTime(tz) | server default now(), NOT NULL |
| `actor_id` | UUID (string) | FK → usuarios.id, NOT NULL |
| `impersonado_id` | UUID (string) | FK → usuarios.id, nullable |
| `materia_id` | UUID (string) | FK → materias.id, nullable |
| `accion` | String(50) | NOT NULL |
| `detalle` | JSONB | Nullable, arbitrary additional context |
| `filas_afectadas` | Integer | Nullable |
| `ip` | String(45) | Nullable |
| `user_agent` | String(500) | Nullable |

The model SHALL be declared with `__tablename__ = "audit_log"`.

#### Scenario: Create AuditLog with minimal fields
- **WHEN** a new `AuditLog` is created with `actor_id` and `accion`
- **THEN** the `id` SHALL be an auto-generated UUID
- **THEN** `fecha_hora` SHALL default to the current timestamp
- **THEN** `impersonado_id`, `materia_id`, `detalle`, `filas_afectadas`, `ip`, `user_agent` SHALL be `NULL`

#### Scenario: AuditLog model inherits TenantMixin
- **WHEN** inspecting the `AuditLog` model class
- **THEN** `AuditLog` SHALL have a `tenant_id` column of type UUID referencing `tenants.id`
- **THEN** `AuditLog` SHALL NOT have a `deleted_at` column
- **THEN** `AuditLog` SHALL NOT have an `updated_at` column

#### Scenario: Append-only enforcement at model level
- **WHEN** any code attempts to call `UPDATE` on an `AuditLog` instance via SQLAlchemy
- **THEN** the operation SHALL be rejected before reaching the database
