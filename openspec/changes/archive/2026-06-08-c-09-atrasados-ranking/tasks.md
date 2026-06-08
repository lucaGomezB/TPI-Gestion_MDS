## 1. Permissions and Audit Codes

- [x] 1.1 Add `reportes:ver` and `calificaciones:exportar` to RBAC matrix in `permissions.py` (PROFESOR, COORDINADOR, ADMIN)
- [x] 1.2 Add audit action codes `ATRASADOS_CONSULTAR` and `RANKING_CONSULTAR` to `action_codes.py`
- [x] 1.3 Register new router and repository in `unit_of_work.py` and `main.py`

## 2. Repository Layer

- [x] 2.1 Create `AtrasadosRankingRepository` in `repositories/atrasados_ranking.py` with tenant-scoped queries
- [x] 2.2 Implement `get_alumnos_con_calificaciones()` — LEFT JOIN EntradaPadron (activa) + Calificacion, with optional `cargado_por` scope filter
- [x] 2.3 Implement `get_ranking()` — GROUP BY entrada_padron_id, COUNT(aprobado=true), HAVING > 0, with filters (comision, busqueda)
- [x] 2.4 Implement `get_metricas()` — consolidated metrics query (total alumnos, atrasados, aprobadas, distinct actividades)
- [x] 2.5 Add filter support: comision, busqueda (ILIKE), fecha_desde, fecha_hasta as optional parameters

## 3. Schema Layer

- [x] 3.1 Create `schemas/atrasados_ranking.py` with Pydantic models (extra='forbid'):
  - `AlumnoAtrasadoOut`: nombre, apellidos, email, comision, razon, nota_minima, umbral, total_actividades
  - `AtrasadosListResponse`: items, total, metrics (total_alumnos, total_atrasados)
  - `RankingEntryOut`: nombre, apellidos, comision, total_aprobadas, total_actividades, porcentaje_aprobacion
  - `RankingListResponse`: items, total
  - `ReportesOut`: total_alumnos, alumnos_con_calificaciones, total_atrasados, total_aprobadas, total_calificaciones, actividades, porcentaje_atrasados

## 4. Service Layer

- [x] 4.1 Create `services/atrasados_ranking.py` with `AtrasadosRankingService`
- [x] 4.2 Implement `list_atrasados()` — gets data from repo, applies RN-06 logic (determine faltante vs nota_baja), returns response
- [x] 4.3 Implement `get_ranking()` — gets data from repo, applies RN-09 logic, returns response with porcentaje_aprobacion
- [x] 4.4 Implement `get_reportes()` — gets metrics from repo, computes derived fields (porcentaje_atrasados)
- [x] 4.5 Implement `export_csv()` — shared method that builds CSV string from atrasados or ranking data

## 5. Router Layer

- [x] 5.1 Create `routers/atrasados_ranking.py` with APIRouter
- [x] 5.2 Implement `GET /api/materias/{materia_id}/atrasados` with filters (comision, busqueda, fecha_desde, fecha_hasta) and `?exportar=csv`
- [x] 5.3 Implement `GET /api/materias/{materia_id}/ranking` with filters (comision, busqueda) and `?exportar=csv`
- [x] 5.4 Implement `GET /api/materias/{materia_id}/reportes` with consolidated metrics
- [x] 5.5 Reuse `_check_materia_access`, `_is_coordinador`, `_get_tenant_id` patterns from calificaciones router (or extract shared helpers)
- [x] 5.6 Wire permissions: `atrasados:ver` for atrasados, `atrasados:ver` for ranking, `reportes:ver` for reportes, `calificaciones:exportar` for export
- [x] 5.7 Add audit logging to each endpoint

## 6. Wiring and Integration

- [x] 6.1 Register `AtrasadosRankingRepository` in `unit_of_work.py` as `atrasados_ranking` property
- [x] 6.2 Export `atrasados_ranking_router` from `api/v1/routers/__init__.py`
- [x] 6.3 Include router in `main.py`

## 7. Testing

- [x] 7.1 Unit tests for `list_atrasados()`: faltantes, nota_baja, mixed, empty padron, scope isolation
- [x] 7.2 Unit tests for `get_ranking()`: ordered by count, excludes 0 approved, filtered by comision/busqueda, scope isolation
- [x] 7.3 Unit tests for `get_reportes()`: full data, empty, scope isolation
- [x] 7.4 Unit tests for `export_csv()`: correct format, headers, UTF-8 BOM, empty data
- [x] 7.5 Integration tests for endpoints: 200, 403, filters, export
