## Context

Liquidaciones (salary settlements) is the module that calculates monthly teacher pay by combining salary grid data (C-18 grilla-salarial) with teaching assignments (C-05 team-management) and student enrollment (C-06 padron-alumnos). The C-18 grilla-salarial already provides the `SalarioBase` and `SalarioPlus` models, repo, and a `query_vigentes_by_date` service method consumed by this module. The C-05 assignments model provides `Asignacion` with role, cohorte, comisiones, and temporal validity. The C-06 enrollment provides `VersionPadron`/`EntradaPadron` for per-subject cohort composition.

The existing codebase uses Clean Architecture: Routers -> Services -> Repositories -> Models, with UoW for atomic operations and JSON-structured audit logging. All endpoints live under FastAPI with Pydantic v2 schemas (`extra='forbid'`).

## Goals / Non-Goals

**Goals:**
- Implement E19 Liquidacion model with fields: tenant_id, cohorte_id, periodo (YYYY-MM), usuario_id, rol, comisiones (JSONB), monto_base, monto_plus, total, es_nexo, excluido_por_factura, estado (Abierta|Cerrada), timestamps
- Implement RN-34 calculation engine: Total = Base(role vigente al mes) + Sum(Plus(category,role) x N_comisiones)
- Provide GET /api/admin/liquidaciones?periodo=YYYY-MM for period view with KPI segregation (F10.6, RN-38)
- Provide GET /api/admin/liquidaciones/{id} for individual detail with breakdown
- Provide POST /api/admin/liquidaciones/{id}/cerrar for immutability (F10.2, RN-22)
- Provide GET /api/admin/liquidaciones/historial for closed-settlement history (F10.3)
- KPI headers: "Total sin factura" (excluido_por_factura=false) and "Total con factura" (excluido_por_factura=true)
- NEXO rows shown separately per RN-36 but included in total

**Non-Goals:**
- No integration with external payment/banking systems (export-to-spreadsheet-style only)
- No invoice management module (E20 Factura is C-20, separate change)
- No editing existing settlements after close -- immutable by design
- No UI or frontend components (backend API only in this change)
- No automatic re-calculation on upstream data changes (re-calculation is a re-run of the endpoint)

## Decisions

| Decision | Choice | Rationale | Rejected alternatives |
|----------|--------|-----------|----------------------|
| D-01: Settlement model approach | One `Liquidacion` row per (cohorte, mes, docente) | Granularity at teacher level allows individual close, detail breakdown, and per-teacher history. Matches RN-37 (cohorte x mes). | Single row per cohorte-month (too coarse). |
| D-02: Calculation engine location | `LiquidacionService` with domain logic | Clean Architecture: service orchestrates reads from grilla/assignments repos, computes totals, writes via LiquidacionRepository. | Inline in router (violates separation). |
| D-03: State machine | Custom `estado` field (Abierta/Cerrada) | Liquidation estado does not map to AuditMixin's Activo/Inactivo. Simpler to use a dedicated state column. Close sets cerrada_at timestamp. | Reusing AuditMixin.estado (wrong semantics). |
| D-04: Period closing scope | Per (cohorte, mes) entire batch | POST /cerrar on a single liquidacion closes only that row. Bulk close (all docentes for a cohorte-month) is a future enhancement. | Bulk close (adds complexity now -- deferred). |
| D-05: Calculation is on-demand | Calculation runs when FINANZAS requests the period view, not pre-cached on data change | Simpler implementation. Data changes (new plus amounts, re-assignments) between runs produce different results -- FINANZAS controls when to calculate. | Trigger-based auto-recalculation (complex eventing, unpredictable for users). |
| D-06: KPI computation | In-memory aggregation from queried Liquidacion rows | Period view returns both row list and computed KPI sums. Single query, simple math. | Separate aggregation endpoint (extra round-trip). |
| D-07: Permission suffix | `liquidaciones:ver`, `liquidaciones:cerrar`, `liquidaciones:calcular` | Consistent with existing pattern (e.g., `liquidaciones:configurar-salarios` from C-18). | Different naming patterns (would break convention). |

## Risks / Trade-offs

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Performance: cohorte with 50+ teachers and 10+ comisiones each | Low | Calculation queries are bounded by cohorte assignments. Pagination from the start even if period view is small initially. |
| Inconsistent state: upstream data changes between preview and close | Low | RN-22: preview is for verification; close writes final snapshot. Upstream changes require re-preview. |
| Missing vigente salary for a role on given month | Medium | Calculation returns `None` for that teacher's monto_base; rendered as zero with notice. FN-34 requires defined base. |
| excluido_por_factura overlaps with C-20 (facturas) | Medium | This change marks the flag but does not manage facturas. C-20 will add the E20 management layer. The flag is read-only from C-19 perspective (set on user.facturador flag). |
