## Context

El sistema ya cuenta con datos de calificaciones (C-07), padron de alumnos (C-06), y endpoints de atrasados/ranking/reportes (C-09). Los modelos `Calificacion` y `EntradaPadron` son la base de datos disponible. No existe aun un modelo separado de "reporte de finalizacion del LMS" (F1.2 esta fuera del camino critico actual).

Actualmente no hay endpoints para calcular notas finales agrupadas, exportar TP sin corregir, ni monitores de seguimiento transversal. Docentes y coordinadores necesitan estas capacidades para cierre de periodo y gestion de correcciones.

El UoW pattern esta activo en todos los services. Los patrones de router (dependencies, permission check, materia access) estan consolidados en calificaciones router y atrasados ranking router.

## Goals / Non-Goals

**Goals:**
- Endpoint `GET /api/materias/{id}/notas-finales` — calculo de nota final agrupada por alumno (F2.5), con export CSV
- Endpoint `GET /api/materias/{id}/export/atrasados` — exportacion de TP sin corregir segun RN-07/RN-08, solo actividades textuales (F2.6)
- Endpoint `GET /api/admin/monitor/actividades` — monitor transversal del tenant (F2.7), solo COORDINADOR/ADMIN
- Endpoint `GET /api/materias/{id}/seguimiento` — monitor de seguimiento por materia con filtros (F2.8, F2.9)
- Filtros: rango de fechas, regional, comision, estado de actividad, busqueda por alumno
- Export CSV descargable para notas-finales y export-atrasados
- Nuevos repositorios `ReportesNotasRepository`, `ReportesExportRepository`, `ReportesMonitorRepository` con queries JOIN
- Nuevos servicios `ReportesNotasService`, `ReportesExportService`, `ReportesMonitorService` usando UoW
- Nuevos permisos: `reportes:notas_finales`, `reportes:exportar_atrasados`, `reportes:monitor_general`, `reportes:seguimiento`
- Tests unitarios para logica de calculo de nota final y deteccion de no corregidos
- Respeto de RN-08: solo actividades textuales en export atrasados

**Non-Goals:**
- Nuevos modelos SQLAlchemy o migraciones Alembic
- Endpoints de escritura (POST/PUT/DELETE)
- Interfaz de usuario frontend (iteracion futura)
- Importacion de reporte de finalizacion del LMS (F1.2, change futuro)
- Export a otros formatos (PDF, XLSX) — solo CSV inicial
- Paginacion (volumenes esperados < 500 alumnos por materia, < 50 materias por tenant)
- Notas finales con ponderacion por actividad configurable desde API (se usa ponderacion uniforme inicial)

## Decisions

### D1: Notas finales — calculo en service con datos agregados del repository

- **Opcion A** (elegida): El repository devuelve todas las calificaciones agrupadas por alumno con sus notas. El service calcula la nota final (promedio simple de notas numericas sobre actividades textuales aprobadas) y determina el estado final (aprobado/reprobado).
- **Opcion B**: Calculo completamente en SQL con window functions.
- **Por que**: La logica de ponderacion y calculo de nota final puede volverse configurable (distintos pesos por actividad). Mantenerla en el service permite cambiar la formula sin modificar SQL. Ademas, se pueden incluir validaciones y reglas de redondeo que serian engorrosas en SQL puro.

### D2: Export atrasados (RN-07/RN-08) — deteccion basada en datos disponibles de Calificacion

- **RN-07** requiere cruce con reporte de finalizacion del LMS para identificar "entregado sin calificar". Dado que F1.2 (importacion de reporte de finalizacion) no esta en el camino critico y no hay modelo dedicado, la implementacion inicial usa una heuristica basada en datos de Calificacion.
- **Heuristica**: Se identifican como "posibles TP sin corregir" aquellos alumnos que:
  1. Estan en el padron activo de la materia.
  2. Tienen al menos una actividad textual registrada en el sistema (actividades donde existe al menos un Calificacion con `nota_textual IS NOT NULL`).
  3. No tienen un Calificacion con nota textual asignada para esa actividad.
- **RN-08**: Solo actividades de escala textual. Se filtra por actividades que tienen al menos un registro con `nota_textual IS NOT NULL`.
- **Flag de dependencia**: Cuando F1.2 se implemente, este endpoint debera actualizarse para usar el reporte de finalizacion real en lugar de la heuristica. Se deja la estructura preparada para recibir esa fuente.

### D3: Monitor general — query transversal con JOINs pesados en repository

- **Opcion A** (elegida): Unico repository con queries que cruzan Calificacion + EntradaPadron + VersionPadron + Materia, con filtros aplicados como clausulas WHERE en SQL.
- **Opcion B**: Materializar una vista o cache de datos agregados.
- **Por que**: Los volumenes son manejables (< 50 materias, < 500 alumnos por materia). No se justifica una vista materializada hasta que haya evidencia de problema de performance. El tenant_id del JWT acota la query al tenant actual.
- El endpoint vive en router separado (`admin_reportes`) con decorador que exige rol COORDINADOR o ADMIN.

### D4: Seguimiento — endpoint unico con comportamiento diferencial por rol

- **Opcion A** (elegida): Un unico endpoint `GET /api/materias/{id}/seguimiento` que detecta el rol del usuario autenticado y aplica filtros diferentes:
  - TUTOR/PROFESOR: filtra por `cargado_por` del JWT. Sin rango de fechas. Filtros: alumno, comision, regional, actividad, minimo_actividades_cumplidas.
  - COORDINADOR/ADMIN: sin filtro de `cargado_por` (ve todos los docentes). Filtros adicionales: `fecha_desde`, `fecha_hasta`.
- **Opcion B**: Endpoints separados `/seguimiento` y `/seguimiento/admin`.
- **Por que**: La logica es casi identica. La unica diferencia es el scope de datos y un par de filtros extra. Un unico endpoint reduce duplicacion de codigo y superficie de API. El router verifica permisos al inicio y pasa el contexto al service.

### D5: Export CSV via query param `?exportar=csv`

- **Opcion A** (elegida): Los endpoints `notas-finales` y `export/atrasados` aceptan `?exportar=csv` y devuelven `Content-Type: text/csv` con `Content-Disposition: attachment`, reusando el patron establecido en C-09.
- **Opcion B**: Endpoints separados para export.
- **Por que**: Reduce la superficie de API. El export comparte exactamente los mismos filtros que la consulta JSON. El monitor y seguimiento no soportan export (son interactivos).

### D6: Filtros via query params con schemas Pydantic

- Todos los filtros se reciben como query params tipados con Pydantic (via `Depends()`).
- Los schemas de filtros usan `extra='forbid'`.
- Fecha invalida o mal formateada → `422` por validacion automatica de Pydantic.
- Parametros desconocidos → `422` por `extra='forbid'`.

### D7: Repositorios separados por capacidad

- **Opcion A** (elegida): Tres repositorios separados: `ReportesNotasRepository`, `ReportesExportRepository`, `ReportesMonitorRepository`.
- **Opcion B**: Un repositorio unificado `ReportesRepository`.
- **Por que**: Cada repositorio tiene queries fundamentalmente diferentes (agregacion de notas, cruce de actividades textuales, JOINs transversales). Separarlos mantiene cohesion y legibilidad. El UoW pattern soporta multiples repositorios sin penalidad.

### D8: Filtro regional disponible en EntradaPadron

- `EntradaPadron.regional` es un campo nullable. Los filtros por regional se aplican como WHERE en el repository.
- Solo `EntradaPadron.comision` y `EntradaPadron.regional` estan disponibles como filtros de segmentacion.
- El filtro "estado de actividad" se resuelve como: `tiene_calificacion` (boolean) o `aprobado` (boolean) segun corresponda.

## Risks / Trade-offs

| Riesgo | Probabilidad | Mitigacion |
|--------|-------------|------------|
| Export atrasados heuristico (sin F1.2) puede dar falsos positivos | Media | Documentar en el endpoint que la deteccion es preliminar. Cuando F1.2 este implementado, migrar a cruce con datos reales de finalizacion |
| Performance del monitor general con muchas materias | Baja | Queries acotadas por tenant_id. Indices existentes en materia_id, entrada_padron_id. Si se detecta lentitud, agregar paginacion y/o cache |
| Nota final con ponderacion uniforme no cubre todos los casos de uso | Media | El calculo esta en el service, facilitando cambiar la formula. La ponderacion configurable queda como mejora futura |
| Filtro "minimo actividades cumplidas" en seguimiento puede ser costoso | Baja | Se implementa como HAVING COUNT() >= N en la query. Los volumenes por materia son bajos |
| Scope de TUTOR mal definido (no tiene `cargado_por` en Calificaciones) | Media | TUTOR no carga calificaciones (solo visualiza). El scope del TUTOR se resuelve por asignaciones a la materia, no por `cargado_por`. Se filtra por alumnos en comisiones donde el TUTOR esta asignado |
| Separacion de routers puede causar duplicacion de helpers de materia access | Baja | Extraer `_check_materia_access`, `_is_coordinador`, `_get_tenant_id` a un modulo compartido si se reusan en 3+ routers |
