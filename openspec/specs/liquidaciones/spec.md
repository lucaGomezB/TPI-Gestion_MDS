## ADDED Requirements

### Requirement: The system SHALL provide the Liquidacion model for salary settlements

The system MUST provide a `Liquidacion` model (E19) representing a single teacher's salary settlement for a given (cohorte, mes) pair. The model SHALL persist the snapshot of settlement data at the time of calculation, not reference live upstream data.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `cohorte_id` | UUID (string) | FK -> cohortes.id, NOT NULL |
| `periodo` | String(7) | NOT NULL, format YYYY-MM |
| `usuario_id` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `rol` | String(20) | NOT NULL, values: PROFESOR, TUTOR, COORDINADOR, NEXO |
| `comisiones` | JSONB | NOT NULL, default `[]`, list of commission identifiers used in calculation |
| `monto_base` | Numeric(12,2) | NOT NULL, base salary amount vigente for the period |
| `monto_plus` | Numeric(12,2) | NOT NULL, sum of all applicable plus amounts |
| `total` | Numeric(12,2) | NOT NULL, computed as monto_base + monto_plus |
| `es_nexo` | Boolean | NOT NULL, default false, indicates NEXO-role settlement |
| `excluido_por_factura` | Boolean | NOT NULL, default false, derived from usuario.facturador |
| `estado` | String(10) | NOT NULL, default 'Abierta', values: Abierta, Cerrada |
| `created_at` | DateTime(tz) | server default now() |
| `cerrada_at` | DateTime(tz) | nullable, set when estado transitions to Cerrada |

Indexes:
- `ix_liquidaciones_periodo` on (tenant_id, periodo)
- `ix_liquidaciones_cohorte_periodo` on (tenant_id, cohorte_id, periodo)
- `ix_liquidaciones_usuario_id` on (usuario_id)
- `ix_liquidaciones_estado` on (tenant_id, estado)

UniqueConstraint:
- `uq_liquidacion_cohorte_usuario_periodo` on (tenant_id, cohorte_id, usuario_id, periodo) -- one settlement per teacher per cohorte-month

#### Scenario: Create liquidacion with all required fields
- **WHEN** the system creates a Liquidacion for a given teacher in a period
- **THEN** the model SHALL store tenant_id, cohorte_id, periodo, usuario_id, rol, comisiones, monto_base, monto_plus, total, es_nexo, excluido_por_factura
- **THEN** estado SHALL default to 'Abierta'
- **THEN** created_at SHALL be set to current timestamp
- **THEN** cerrada_at SHALL be null

#### Scenario: Total is computed as base + sum of plus
- **WHEN** a Liquidacion is created with monto_base=150000.00 and monto_plus=25000.00
- **THEN** total SHALL equal 175000.00

#### Scenario: Reject duplicate settlement for same cohorte+usuario+periodo
- **WHEN** creating a second Liquidacion for the same (tenant_id, cohorte_id, usuario_id, periodo)
- **THEN** the system SHALL raise an integrity error (duplicate key violation)

### Requirement: The system SHALL allow FINANZAS to calculate liquidaciones for a given period

The system MUST provide a calculation endpoint (internal service + triggered via period view) that computes liquidaciones for all teachers assigned to a given cohorte for a period (YYYY-MM). The calculation SHALL read vigente SalarioBase and SalarioPlus from grilla-salarial, and active Asignacion records from team-management.

Algorithm per RN-34:
1. For each teacher with active Asignacion in the cohorte for the period:
   a. Determine vigente SalarioBase for the teacher's rol on the last day of the period month
   b. For each comision, determine applicable SalarioPlus based on (grupo_materia, rol)
   c. Sum all applicable plus amounts across all comisiones
   d. Set excluido_por_factura = true if usuario.facturador is true
   e. Set es_nexo = true if the Asignacion's rol is NEXO

#### Scenario: Calculate liquidacion for a PROFESOR with one comision
- **WHEN** the system calculates liquidacion for a teacher with rol=PROFESOR, one comision in grupo="PROG", vigente SalarioBase=150000, vigente SalarioPlus=5000
- **THEN** the system SHALL create a Liquidacion with monto_base=150000.00, monto_plus=5000.00, total=155000.00
- **THEN** es_nexo SHALL be false

#### Scenario: Calculate liquidacion with multiple comisiones same grupo
- **WHEN** a teacher has 3 active comisiones all in grupo="PROG", SalarioPlus=5000
- **THEN** monto_plus SHALL be 15000.00 (3 x 5000) and total SHALL reflect the sum

#### Scenario: Calculate liquidacion for NEXO role
- **WHEN** a teacher's active Asignacion has rol=NEXO
- **THEN** the created Liquidacion SHALL have es_nexo=true

#### Scenario: Calculate liquidacion for facturante teacher
- **WHEN** the teacher has facturador=true on their Usuario record
- **THEN** the created Liquidacion SHALL have excluido_por_factura=true

#### Scenario: Calculate liquidacion when no vigente SalarioBase exists
- **WHEN** no SalarioBase exists vigente for the teacher's rol on the period's last day
- **THEN** the system SHALL skip that teacher with a logged warning (no liquidacion created)

### Requirement: The system SHALL expose GET /api/admin/liquidaciones for period view with KPIs

The system MUST provide an endpoint returning all liquidaciones for a given period, with KPI headers that segregate totals by excluido_por_factura flag (RN-38). NEXO rows SHALL be visually separable per RN-36.

Query parameters:
- `periodo` (required, format YYYY-MM) -- filter by settlement period
- `cohorte_id` (optional, UUID) -- filter by cohorte
- `page`, `page_size` (optional, pagination defaults)

Response structure:
```json
{
  "items": [{ Liquidacion detail }],
  "kpis": {
    "total_sin_factura": 1230000.00,
    "total_con_factura": 450000.00,
    "total_general": 1680000.00
  },
  "total": 25,
  "page": 1,
  "page_size": 50
}
```

#### Scenario: Get period view with KPIs
- **WHEN** FINANZAS user sends GET /api/admin/liquidaciones?periodo=2026-06
- **THEN** the system SHALL return 200 with all liquidaciones for that period
- **THEN** response SHALL include `kpis` with total_sin_factura, total_con_factura, total_general
- **THEN** total_sin_factura SHALL sum total where excluido_por_factura=false
- **THEN** total_con_factura SHALL sum total where excluido_por_factura=true
- **THEN** total_general SHALL be total_sin_factura + total_con_factura

#### Scenario: Filter by cohorte
- **WHEN** GET /api/admin/liquidaciones?periodo=2026-06&cohorte_id=uuid-123
- **THEN** the system SHALL return only liquidaciones for that cohorte

#### Scenario: Empty period returns empty list
- **WHEN** no liquidaciones exist for the requested period
- **THEN** the system SHALL return 200 with empty items array and kpis all set to zero

### Requirement: The system SHALL expose GET /api/admin/liquidaciones/{id} for individual detail

#### Scenario: Get liquidacion detail
- **WHEN** FINANZAS user sends GET /api/admin/liquidaciones/{id}
- **THEN** the system SHALL return 200 with the full Liquidacion data including desglose fields (monto_base breakdown, monto_plus breakdown by grupo)
- **THEN** if id does not exist, SHALL return 404

### Requirement: The system SHALL expose POST /api/admin/liquidaciones/{id}/cerrar to finalize a settlement

Closing a liquidacion (RN-22):
- Sets estado = 'Cerrada'
- Sets cerrada_at = current timestamp
- No further modifications allowed
- Returns 409 if already closed

#### Scenario: Close an open liquidacion
- **WHEN** FINANZAS user sends POST /api/admin/liquidaciones/{id}/cerrar for an Abierta liquidacion
- **THEN** the system SHALL set estado='Cerrada' and cerrada_at to current timestamp
- **THEN** SHALL return 200 with the updated liquidacion

#### Scenario: Close already closed liquidacion returns 409
- **WHEN** POST /api/admin/liquidaciones/{id}/cerrar is sent for a Cerrada liquidacion
- **THEN** the system SHALL return 409 Conflict with error message indicating already closed

#### Scenario: Reject close without FINANZAS permission
- **WHEN** a non-FINANZAS user sends POST /api/admin/liquidaciones/{id}/cerrar
- **THEN** the system SHALL return 403

### Requirement: The system SHALL expose GET /api/admin/liquidaciones/historial for closed settlements

Returns all liquidaciones with estado=Cerrada, ordered by cerrada_at descending. Supports pagination.

#### Scenario: Get closed settlement history
- **WHEN** FINANZAS user sends GET /api/admin/liquidaciones/historial
- **THEN** the system SHALL return 200 with paginated list of Cerrada liquidaciones ordered by cerrada_at desc
- **THEN** items SHALL only include liquidaciones with estado='Cerrada'

#### Scenario: Filter historial by periodo
- **WHEN** GET /api/admin/liquidaciones/historial?periodo=2026-06
- **THEN** the system SHALL filter to only show Cerrada liquidaciones for that period

### Requirement: The system SHALL enforce authorization for all liquidacion endpoints

Based on permission schema from AGENTS.md:
- `liquidaciones:ver` -- GET endpoints (period view, detail, historial)
- `liquidaciones:calcular` -- CALCULATE (triggered on period view generation)
- `liquidaciones:cerrar` -- POST /cerrar

#### Scenario: Reject unauthenticated requests
- **WHEN** an unauthenticated request is sent to any /api/admin/liquidaciones/* endpoint
- **THEN** the system SHALL return 401

#### Scenario: Reject request without required permission
- **WHEN** an authenticated user without liquidaciones:ver requests GET /api/admin/liquidaciones
- **THEN** the system SHALL return 403

#### Scenario: Accept request with correct permission
- **WHEN** a FINANZAS user with liquidaciones:ver sends GET /api/admin/liquidaciones
- **THEN** the system SHALL return 200
