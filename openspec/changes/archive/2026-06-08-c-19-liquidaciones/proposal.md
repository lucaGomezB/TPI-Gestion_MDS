## Why

FINANZAS needs to calculate, close, and audit monthly teacher salary settlements (liquidaciones). Currently no system support exists -- settlements are manual spreadsheet work, error-prone and unauditable. This change introduces the computation layer that reads salary grid (C-18), assignments (C-05), and enrollment data (C-06) to produce per-teacher monthly statements with proper separation between salaried and invoice-based teachers.

## What Changes

- New `Liquidacion` model (E19) with fields: tenant_id, cohorte_id, periodo, usuario_id, rol, comisiones (JSONB), monto_base, monto_plus, total, es_nexo, excluido_por_factura, estado (Abierta|Cerrada), timestamps
- Settlement calculation engine implementing RN-34: Total = Base(role) + Sum(Plus(category,role) x comisiones)
- Open/close lifecycle per RN-22: close = immutable, no further edits
- KPI segregation per RN-38: "Total sin factura" vs "Total con factura" in period view
- API under `/api/admin/liquidaciones/` -- period view, detail, close, history

## Capabilities

### New Capabilities
- `liquidaciones`: salary settlement computation, period view with KPI separation (F10.6), open/close lifecycle (F10.2), and historical audit (F10.3). Covers E19 model, RN-21/RN-22/RN-34/RN-35/RN-36/RN-37/RN-38.

### Modified Capabilities
- None

## Impact

- **Backend**: new SQLAlchemy model `Liquidacion`, new repository `LiquidacionRepository`, new service `LiquidacionService` with calculation engine, new router `liquidaciones.py` under `/api/admin/liquidaciones/`
- **Permissions**: new seeds `liquidaciones:ver`, `liquidaciones:cerrar`, `liquidaciones:calcular` (FINANZAS role)
- **Audit**: close and calculation actions logged via existing AuditLog
- **Dependencies**: reads `SalarioBase`, `SalarioPlus` (grilla-salarial C-18), `Asignacion` (team-management C-05), `EntradaPadron`/`VersionPadron` (padron-alumnos C-06)
