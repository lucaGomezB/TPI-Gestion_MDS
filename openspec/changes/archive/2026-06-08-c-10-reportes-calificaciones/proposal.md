## Why

C-09 ya implemento endpoints de atrasados, ranking y reportes rapidos (F2.2, F2.3, F2.4), pero faltan funcionalidades de reportes avanzados: calcular notas finales agrupadas por alumno (F2.5), exportar trabajos practicos sin corregir (F2.6), y los monitores de actividades transversales (F2.7, F2.8, F2.9). Coordinadores y administracion necesitan visibilidad del estado general del tenant; profesores necesitan exportar pendientes de correccion y calcular notas de cierre de periodo.

## What Changes

- **Nuevo endpoint** `GET /api/materias/{id}/notas-finales` — calcula nota final agrupada por alumno con ponderacion configurable (F2.5). Solo PROFESOR.
- **Nuevo endpoint** `GET /api/materias/{id}/export/atrasados` — exporta listado de TP sin corregir segun RN-07/RN-08 (solo actividades textuales). PROFESOR y COORDINADOR (F2.6).
- **Nuevo endpoint** `GET /api/admin/monitor/actividades` — monitor transversal del tenant con filtros (materia, regional, comision, estado actividad, busqueda). COORDINADOR y ADMIN (F2.7).
- **Nuevo endpoint** `GET /api/materias/{id}/seguimiento` — monitor de seguimiento por materia con filtros (alumno, comision, regional, actividad, minimo cumplido). TUTOR, PROFESOR (F2.8). COORDINADOR, ADMIN obtienen ademas rango de fechas (F2.9).
- **Sin nuevos modelos SQLAlchemy** — solo consultas sobre entidades existentes (Calificacion, EntradaPadron, Actividad, etc.)
- **Filtros**: rango de fechas, regional, comision, estado de actividad como query params
- **Export a CSV** para notas-finales y export/atrasados
- **Nuevos permisos**: `reportes:notas_finales`, `reportes:exportar_atrasados`, `reportes:monitor_general`, `reportes:seguimiento`

## Capabilities

### New Capabilities
- `reportes-notas-finales`: Calculo de nota final agrupada por alumno para una materia, con ponderacion de actividades y exportacion (F2.5).
- `reportes-export-atrasados`: Deteccion y exportacion de entregas finalizadas sin calificar, basado en cruce de reporte de finalizacion del LMS con calificaciones importadas (RN-07). Solo actividades de escala textual (RN-08). (F2.6)
- `reportes-monitor`: Monitor general de actividades del tenant (F2.7) y monitor de seguimiento por materia con filtros (F2.8, F2.9). Incluye rango de fechas para coordinacion/admin.

### Modified Capabilities
- `atrasados-ranking`: No hay cambios en requirements existentes. El endpoint `GET /api/materias/{id}/export/atrasados` para F2.6 usa logica diferente (RN-07/RN-08) a la deteccion de alumnos atrasados (RN-06) implementada en C-09, por lo que vive en la nueva capacidad `reportes-export-atrasados`.

## Impact

- **Routers nuevos**: `backend/app/api/v1/routers/reportes.py` (notas-finales, export-atrasados, seguimiento), `backend/app/api/v1/routers/admin_reportes.py` (monitor general, solo COORDINADOR/ADMIN)
- **Servicios nuevos**: `backend/app/services/reportes_notas.py`, `backend/app/services/reportes_export.py`, `backend/app/services/reportes_monitor.py`
- **Repositorios nuevos**: `backend/app/repositories/reportes_notas.py`, `backend/app/repositories/reportes_export.py`, `backend/app/repositories/reportes_monitor.py`
- **Schemas nuevos**: `backend/app/schemas/reportes.py`
- **Modificaciones menores**:
  - `backend/app/core/permissions.py`: agregar permisos `reportes:notas_finales`, `reportes:exportar_atrasados`, `reportes:monitor_general`, `reportes:seguimiento`
  - `backend/app/core/unit_of_work.py`: agregar properties para los nuevos repositorios
  - `backend/app/api/v1/routers/__init__.py`: exportar nuevos routers
  - `backend/app/main.py`: incluir nuevos routers
- **Dependencias**: C-09 archivado — atrasados-ranking disponible como base. Datos de C-06 (padron), C-07 (calificaciones) existentes.
- **Sin migrations**: no hay nuevos modelos ni cambios de esquema.
