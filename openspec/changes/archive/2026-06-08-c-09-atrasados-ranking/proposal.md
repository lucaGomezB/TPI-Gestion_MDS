## Why

Los datos de calificaciones (C-07) y padron de alumnos (C-06) ya estan en el sistema, pero actualmente no hay endpoints de consulta que exploten esos datos para detectar alumnos en riesgo academico ni para generar rankings de rendimiento. Los docentes necesitan visibilidad inmediata de quienes estan atrasados (actividades faltantes o por debajo del umbral) y un ranking de aprobadas para priorizar acompanamiento, sin tener que hacer cálculos manuales.

## What Changes

- **Nuevo router** `atrasados_ranking` con endpoints GET de consulta (solo lectura):
  - `GET /api/materias/{materia_id}/atrasados` — listar alumnos atrasados segun RN-06
  - `GET /api/materias/{materia_id}/ranking` — ranking de aprobadas descendente segun RN-09
  - `GET /api/materias/{materia_id}/reportes` — metricas clave consolidadas de la materia
  - Export de atrasados y ranking a formato descargable
- **Nuevo servicio** `AtrasadosRankingService` que usa el UoW pattern ya activo
- **Nuevo repositorio** `AtrasadosRankingRepository` con queries de lectura que cruzan `Calificacion` + `EntradaPadron` + `UmbralMateria`
- **Nuevos permisos**: `reportes:ver` (reportes rapidos), `calificaciones:exportar` (exportar datos)
- No se crean modelos nuevos — solo consultas sobre entidades existentes
- No se agregan endpoints de escritura ni mutacion de datos

## Capabilities

### New Capabilities
- `atrasados-ranking`: Deteccion de alumnos atrasados, ranking de aprobadas y reportes rapidos por materia, con filtros y exportacion. Solo endpoints GET sobre datos existentes de calificaciones y padron.

### Modified Capabilities
- `calificaciones`: Se agrega el permiso `calificaciones:exportar` a la matriz de permisos (PROFESOR, COORDINADOR, ADMIN). No hay cambios en requirements existentes, solo nuevo permiso.

## Impact

- **Router nuevo**: `backend/app/api/v1/routers/atrasados_ranking.py`
- **Servicio nuevo**: `backend/app/services/atrasados_ranking.py`
- **Repositorio nuevo**: `backend/app/repositories/atrasados_ranking.py`
- **Schemas nuevos**: `backend/app/schemas/atrasados_ranking.py`
- **Modificaciones menores**:
  - `backend/app/core/permissions.py`: agregar permisos `reportes:ver` y `calificaciones:exportar`
  - `backend/app/core/unit_of_work.py`: agregar property para el nuevo repositorio
  - `backend/app/api/v1/routers/__init__.py`: exportar nuevo router
  - `backend/app/main.py`: incluir nuevo router
- **Dependencias**: C-07 (calificaciones) y C-06 (padron) archivados — datos existentes disponibles
- **Sin migrations**: no hay nuevos modelos ni cambios de esquema
