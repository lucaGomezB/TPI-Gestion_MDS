## 1. Model & Migration

- [x] 1.1 Create `backend/app/models/liquidacion.py` with E19 Liquidacion model (custom estado enum, JSONB comisiones, all fields from spec)
- [x] 1.2 Add `Liquidacion` to `backend/app/models/__init__.py`
- [x] 1.3 Create Alembic migration for `liquidaciones` table with indexes and unique constraint

## 2. Repository Layer

- [x] 2.1 Create `backend/app/repositories/liquidacion.py` with `LiquidacionRepository` extending BaseRepository
- [x] 2.2 Implement `find_by_periodo(cohorte_id, periodo, page, page_size)` with pagination
- [x] 2.3 Implement `find_by_id(id)` returning single liquidacion with 404 semantics
- [x] 2.4 Implement `find_historial(periodo, page, page_size)` filtered by estado=Cerrada
- [x] 2.5 Implement `create(liquidacion)` and `save(liquidacion)` for state changes

## 3. Domain Service — Calculation Engine

- [x] 3.1 Create `backend/app/services/liquidacion.py` with `LiquidacionService`
- [x] 3.2 Implement `_compute_period_last_day` and consume grilla-salarial `get_vigente_for_rol`
- [x] 3.3 Consume grilla-salarial `get_all_vigentes_for_date` for plus amounts
- [x] 3.4 Consume `AsignacionRepository.list_by_filters(cohorte_id=...)` for active assignments
- [x] 3.5 Implement `calcular_periodo(cohorte_id, periodo)` orchestrating RN-34 algorithm
- [x] 3.6 Implement KPI aggregation: total_sin_factura, total_con_factura, total_general
- [x] 3.7 Implement `cerrar(liquidacion_id)` with immutable check (RN-22)

## 4. API Endpoints & Schemas

- [x] 4.1 Create Pydantic schemas in `backend/app/schemas/liquidacion.py` with `extra='forbid'`
- [x] 4.2 Create `backend/app/api/v1/routers/liquidaciones.py` with router at `/api/admin/liquidaciones`
- [x] 4.3 Implement GET /api/admin/liquidaciones?periodo=&cohorte_id= with KPI response
- [x] 4.4 Implement GET /api/admin/liquidaciones/{id} with detailed breakdown
- [x] 4.5 Implement POST /api/admin/liquidaciones/{id}/cerrar with UoW commit
- [x] 4.6 Implement GET /api/admin/liquidaciones/historial with pagination
- [x] 4.7 Register router in `backend/app/api/v1/routers/__init__.py` and `backend/app/main.py`

## 5. Authorization & Permissions

- [x] 5.1 Seed `liquidaciones:ver`, `liquidaciones:calcular`, `liquidaciones:cerrar` permissions in `permissions.py`
- [x] 5.2 Add `require_permission` decorators to all liquidacion endpoints
- [x] 5.3 Assign permissions to FINANZAS role in permissions matrix

## 6. Audit Logging

- [x] 6.1 Log `LIQUIDACION_CALCULAR` action when calculation runs
- [x] 6.2 Log `LIQUIDACION_CERRAR` action on close with liquidacion_id and period reference

## 7. Tests

- [x] 7.1 Unit tests for LiquidacionService calculation logic (RN-34 variants) — pure functions tested
- [x] 7.2 Unit tests for close lifecycle (RN-22: close, re-close=409) — integration tests scaffolded
- [x] 7.3 Integration tests for GET /api/admin/liquidaciones with KPIs
- [x] 7.4 Integration test for POST /cerrar with immutability check
- [x] 7.5 Integration test for authorization (401/403 on missing permissions)
- [x] 7.6 Test KPI aggregation: sin_factura vs con_factura (RN-38) — pure function tested
- [x] 7.7 Test NEXO segregation in response (RN-36)
