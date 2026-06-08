## Context

El sistema ya cuenta con datos de calificaciones (C-07) y padron de alumnos (C-06). El modelo `Calificacion` almacena notas numericas y textuales por alumno-actividad, con flag `aprobado` derivado al importar. `UmbralMateria` almacena umbrales de aprobacion por (asignacion x materia). `EntradaPadron` contiene los datos de cada alumno (nombre, apellidos, comision) vinculados a la version activa del padron.

Actualmente no hay endpoints de consulta que crucen estos datos para detectar atrasados ni generar rankings. Los docentes necesitan estas visualizaciones sin modelos nuevos ni endpoints de escritura.

El UoW pattern ya esta activo en todos los services. Los patrones de router (dependencies, permission check, materia access) estan consolidados en calificaciones router.

## Goals / Non-Goals

**Goals:**
- Endpoint GET `/api/materias/{materia_id}/atrasados` con filtros (comision, fecha, busqueda)
- Endpoint GET `/api/materias/{materia_id}/ranking` con filtros (comision, busqueda)
- Endpoint GET `/api/materias/{materia_id}/reportes` con metricas clave consolidadas
- Export a CSV descargable para atrasados y ranking
- Nuevo repositorio `AtrasadosRankingRepository` con queries JOIN optimizadas
- Nuevo servicio `AtrasadosRankingService` usando UoW
- Nuevos permisos: `reportes:ver`, `calificaciones:exportar`
- Respeto de RN-08: PROFESOR solo ve sus propios datos (cargados por el)
- Respeto de RN-06 y RN-09 en la logica de negocio
- Tests unitarios para la logica de deteccion y ranking

**Non-Goals:**
- Nuevos modelos SQLAlchemy o migraciones Alembic
- Endpoints de escritura (POST/PUT/DELETE)
- Interfaz de usuario frontend (iteracion futura)
- Recalculo masivo de `aprobado` existentes (D4 de C-07)
- Export a otros formatos (PDF, XLSX) — solo CSV inicial
- Paginacion (los volumenes esperados son < 500 alumnos por materia)

## Decisions

### D1: Nuevo repositorio dedicado con queries JOIN

- **Opcion A** (elegida): `AtrasadosRankingRepository` separado de `CalificacionesRepository`, con queries SQLAlchemy SELECT + JOIN dedicadas.
- **Opcion B**: Agregar metodos a `CalificacionesRepository` existente.
- **Por que**: Las queries de atrasados/ranking cruzan 3 tablas (Calificacion + EntradaPadron + VersionPadron) con agrupaciones y conteos. Mezclarlas con el CRUD de calificaciones incrementaria la complejidad del repositorio existente. Un repositorio separado mantiene la separacion de responsabilidades.

### D2: Determinacion de atrasados via LEFT JOIN + logica en service

- **RN-06**: Alumno atrasado = faltante en calificaciones O nota_numerica < umbral configurado.
- **Approach**: El repository devuelve todas las calificaciones del alumno en la materia (con LEFT JOIN desde EntradaPadron activa). El service determina "atrasado" aplicando:
  1. Si el alumno no tiene calificaciones en ninguna actividad del docente -> atrasado por faltante.
  2. Si tiene calificaciones, se evalua cada una contra el umbral. Si alguna nota_numerica < umbral, es atrasado.
  3. Se unifica: un alumno es atrasado si cumple CUALQUIER condicion.
- Esto permite que la logica de negocio (RN-06, RN-03, RN-02) viva en el service, no en SQL.

### D3: Ranking con COUNT + HAVING en repository

- **RN-09**: Ranking solo incluye alumnos con >= 1 actividad aprobada, ordenados por cantidad descendente.
- **Query**: SELECT entrada_padron_id, COUNT(*) FILTER (WHERE aprobado = true) as total_aprobadas, GROUP BY entrada_padron_id, HAVING total_aprobadas > 0, ORDER BY total_aprobadas DESC.
- La exportacion a CSV y la respuesta JSON comparten la misma query del repository.

### D4: Scope docente (RN-08) aplicado como filtro en repository

- PROFESOR: filtra Calificacion.cargado_por = usuario_id del JWT.
- COORDINADOR/ADMIN: sin filtro de cargado_por (ve todos los datos de la materia).
- El role check se hace en el router (reusa patron de calificaciones router).
- El repository recibe `cargado_por: str | None` como parametro opcional.

### D5: Export via query param `?exportar=csv`

- **Opcion A** (elegida): Los mismos endpoints GET aceptan `?exportar=csv` y devuelven `Content-Type: text/csv` con `Content-Disposition: attachment`.
- **Opcion B**: Endpoints separados `/atrasados/exportar` y `/ranking/exportar`.
- **Por que**: Reduce la superficie de API y evita duplicar logica de filtros. El export comparte exactamente los mismos filtros que la consulta JSON.

### D6: Reportes rapidos como endpoint separado

- `GET /api/materias/{materia_id}/reportes` devuelve metricas clave:
  - `total_alumnos`: cantidad de alumnos en padron activo
  - `total_con_calificaciones`: alumnos con al menos una calificacion cargada
  - `total_atrasados`: alumnos detectados como atrasados
  - `total_aprobadas`: total de calificaciones con aprobado = true
  - `actividades_detectadas`: lista de actividades distintas con conteos
- Es un endpoint liviano que agrega datos de las mismas queries.

### D7: Filtro por busqueda de alumno via ILIKE

- El query param `busqueda` busca coincidencia parcial (ILIKE) en `EntradaPadron.nombre` y `EntradaPadron.apellidos`.
- Se aplica como filtro adicional en el repository, no post-filtrado en service.

### D8: Reuso del patron de acceso a materia existente

- Se reusa `_check_materia_access`, `_is_coordinador`, `_get_tenant_id` del router de calificaciones (o se extraen a un modulo compartido).
- Esto evita duplicar la logica de verificacion de asignacion activa.

## Risks / Trade-offs

| Riesgo | Probabilidad | Mitigacion |
|--------|-------------|------------|
| Performance con muchas calificaciones (>10k registros) | Baja | Las queries usan JOIN con indices existentes (materia_id, entrada_padron_id). Sin paginacion porque el volumen por materia es bajo (< 500 alumnos x 10 actividades = 5k registros) |
| Umbral cambiado post-importacion | Media | `aprobado` se calculo al importar (D4 de C-07). La deteccion de atrasados usa el `aprobado` persistido, no recalcula. Si se necesita recalculo masivo, sera un change futuro |
| Definicion de "faltante" ambigua | Media | Se considera faltante a un alumno del padron activo que no tiene NINGUNA calificacion cargada por el usuario actual en la materia. No se evalua actividad por actividad porque el docente pudo no haber importado todas las actividades |
| Scope RN-08 malinterpretado | Baja | RN-08 dice "visibilidad solo del propio docente". Se implementa filtrando por `cargado_por` del JWT para PROFESOR. COORDINADOR/ADMIN ven todo |
| Export CSV con caracteres especiales | Baja | Se usa `csv.writer` con UTF-8 BOM para compatibilidad con Excel en Windows |
