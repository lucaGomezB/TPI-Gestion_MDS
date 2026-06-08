## 1. Permissions and Audit Codes

- [x] 1.1 Add `reportes:notas_finales`, `reportes:exportar_atrasados`, `reportes:monitor_general`, `reportes:seguimiento` to RBAC matrix in `permissions.py` with correct role assignments
- [x] 1.2 Add audit action codes `NOTAS_FINALES_CONSULTAR`, `EXPORT_ATRASADOS_CONSULTAR`, `MONITOR_GENERAL_CONSULTAR`, `SEGUIMIENTO_CONSULTAR` to `action_codes.py`
- [x] 1.3 Register new repositories (`ReportesNotasRepository`, `ReportesExportRepository`, `ReportesMonitorRepository`) and routers in `unit_of_work.py`, `routers/__init__.py`, and `main.py`

## 2. Notas Finales — Repository Layer

- [x] 2.1 Create `ReportesNotasRepository` in `repositories/reportes_notas.py` with tenant-scoped queries
- [x] 2.2 Implement `get_calificaciones_agrupadas()` — all Calificacion records grouped by entrada_padron_id for a materia, with optional cargado_por scope filter
- [x] 2.3 Add filter support: comision, busqueda (ILIKE) as optional parameters

## 3. Notas Finales — Schema and Service Layer

- [x] 3.1 Create Pydantic schemas in `schemas/reportes.py` with `extra='forbid'`:
  - `NotaFinalEntryOut`: entrada_padron_id, nombre, apellidos, comision, total_actividades, nota_final, estado
  - `NotasFinalesResponse`: items, total, total_alumnos, promedio_general
- [x] 3.2 Create `ReportesNotasService` in `services/reportes_notas.py` — implements calcular_nota_final() logic: promedio simple de notas numericas, determina estado (aprobado/reprobado) segun umbral
- [x] 3.3 Implement `export_csv()` — builds CSV string from notas-finales data with UTF-8 BOM

## 4. Notas Finales — Router Layer

- [x] 4.1 Create `routers/reportes.py` with APIRouter — shared router for notas-finales, export-atrasados, and seguimiento
- [x] 4.2 Implement `GET /api/materias/{materia_id}/notas-finales` with filters (comision, busqueda) and `?exportar=csv`
- [x] 4.3 Wire permission `reportes:notas_finales` and audit logging for endpoint
- [x] 4.4 Reuse `_check_materia_access`, `_is_coordinador`, `_get_tenant_id` patterns from existing routers

## 5. Export Atrasados — Repository Layer

- [x] 5.1 Create `ReportesExportRepository` in `repositories/reportes_export.py` with tenant-scoped queries
- [x] 5.2 Implement `get_actividades_textuales()` — distinct actividades that have at least one Calificacion with nota_textual IS NOT NULL for a materia
- [x] 5.3 Implement `get_alumnos_sin_calificacion_textual()` — alumnos in active padron without Calificacion for specific textual actividades
- [x] 5.4 Add filter support: comision, fecha_desde, fecha_hasta as optional parameters

## 6. Export Atrasados — Schema, Service, and Router

- [x] 6.1 Create Pydantic schemas in `schemas/reportes.py` (extend existing):
  - `ExportAtrasadoEntryOut`: nombre, apellidos, comision, actividad, estado
  - `ExportAtrasadosResponse`: items, total
- [x] 6.2 Create `ReportesExportService` in `services/reportes_export.py` — implements detectar_sin_corregir() heuristic: cruza padron activo con actividades textuales, identifica alumnos sin calificacion textual (RN-07 heuristic, RN-08 filter)
- [x] 6.3 Implement `export_csv()` — builds CSV string for export-atrasados data
- [x] 6.4 Implement `GET /api/materias/{materia_id}/export/atrasados` with filters (comision, fecha_desde, fecha_hasta) and `?exportar=csv`
- [x] 6.5 Wire permission `reportes:exportar_atrasados` and audit logging

## 7. Monitor General — Repository Layer

- [x] 7.1 Create `ReportesMonitorRepository` in `repositories/reportes_monitor.py` with tenant-wide queries
- [x] 7.2 Implement `get_monitor_general()` — cross-subject query: JOIN Calificacion + EntradaPadron + VersionPadron + Materia, grouped by (materia, alumno)
- [x] 7.3 Add filter support: materia_id, regional, comision, estado_actividad, busqueda, fecha_desde, fecha_hasta as optional parameters
- [x] 7.4 Implement `get_metricas_generales()` — top-level agregated metrics (total_alumnos, total_materias, total_actividades, total_aprobadas)

## 8. Monitor General — Schema, Service, and Router

- [x] 8.1 Create Pydantic schemas in `schemas/reportes.py` (extend existing):
  - `MonitorEntryOut`: entrada_padron_id, nombre, apellidos, comision, regional, materia_nombre, materia_id, total_actividades, total_aprobadas, total_pendientes, ultima_actividad
  - `MonitorGeneralResponse`: items, total, total_alumnos, total_materias, total_actividades, total_aprobadas
- [x] 8.2 Create `ReportesMonitorService` in `services/reportes_monitor.py` — delegates to repository, formats response
- [x] 8.3 Create `routers/admin_reportes.py` with APIRouter for admin-only endpoints
- [x] 8.4 Implement `GET /api/admin/monitor/actividades` with all filters
- [x] 8.5 Wire permission `reportes:monitor_general` (COORDINADOR, ADMIN only) and audit logging

## 9. Seguimiento — Repository, Service, and Router

- [x] 9.1 Extend `ReportesMonitorRepository` with `get_seguimiento()` — per-subject query: Calificacion + EntradaPadron for a materia, with role-aware scope
- [x] 9.2 Implement role-aware scope: TUTOR/PROFESOR filters by cargado_por or comision assignment; COORDINADOR/ADMIN sees all
- [x] 9.3 Add seguimiento-specific filters: alumno, comision, regional, actividad, minimo_actividades_cumplidas (HAVING COUNT), fecha_desde, fecha_hasta (only for COORDINADOR/ADMIN)
- [x] 9.4 Create Pydantic schemas (extend existing):
  - `SeguimientoEntryOut`: entrada_padron_id, nombre, apellidos, comision, actividades (list), total_actividades, total_aprobadas, porcentaje_cumplimiento
  - `SeguimientoResponse`: items, total, total_alumnos, promedio_cumplimiento
- [x] 9.5 Extend `ReportesMonitorService` with `get_seguimiento()` — delegates to repository, computes porcentaje_cumplimiento, applies role-aware logic
- [x] 9.6 Implement `GET /api/materias/{materia_id}/seguimiento` in `routers/reportes.py` with role-aware filters
- [x] 9.7 Wire permission `reportes:seguimiento` (TUTOR, PROFESOR, COORDINADOR, ADMIN) and audit logging

## 10. Testing

- [x] 10.1 Unit tests for `ReportesNotasService.calcular_nota_final()`: promedio simple, mixed grade types, empty data, scope isolation
- [x] 10.2 Unit tests for `ReportesExportService.detectar_sin_corregir()`: textual activities detected, numeric excluded (RN-08), all graded, no textual activities, filtered by comision
- [x] 10.3 Unit tests for `ReportesMonitorService.get_monitor_general()`: cross-subject aggregation, filters (materia, regional, comision, busqueda, estado_actividad)
- [x] 10.4 Unit tests for `ReportesMonitorService.get_seguimiento()`: role-aware scope (TUTOR, PROFESOR, COORDINADOR), filter by minimo_actividades_cumplidas, date range for COORDINADOR only
- [x] 10.5 Unit tests for CSV export: correct format, headers, UTF-8 BOM, empty data for both notas-finales and export-atrasados
- [ ] 10.6 Integration tests: 200 success, 403 permissions, CSV response headers, filter combinations for each endpoint
