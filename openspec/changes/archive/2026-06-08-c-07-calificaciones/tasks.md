## 1. Modelos SQLAlchemy

- [x] 1.1 Crear `models/calificaciones.py` con `Calificacion` (AppModel, TimestampMixin, TenantMixin) y columnas: id, tenant_id, entrada_padron_id, materia_id, actividad, nota_numerica (Numeric 5,2 nullable), nota_textual (String 100 nullable), aprobado, origen (enum Importado|Manual), cargado_por, importado_at
- [x] 1.2 Crear `UmbralMateria` (AppModel, TimestampMixin, TenantMixin) con columnas: id, tenant_id, asignacion_id, materia_id, umbral_pct (Integer default 60, min 0 max 100), valores_aprobatorios (JSONB default ["Satisfactorio", "Supera lo esperado"])
- [x] 1.3 Agregar relaciones SQLAlchemy: Calificacion.entrada_padron (many-to-one -> EntradaPadron), Calificacion.materia (many-to-one -> Materia), UmbralMateria.asignacion (many-to-one -> Asignacion), UmbralMateria.materia (many-to-one -> Materia)
- [x] 1.4 Registrar ambos modelos en `models/__init__.py`

## 2. Migracion Alembic

- [x] 2.1 Generar migracion 009 (depende de 008): tabla `calificaciones` con FK a entradas_padron (CASCADE), materias (CASCADE), usuarios (cargado_por, SET NULL), indice compuesto (materia_id, actividad), indice por (materia_id, cargado_por) para scope-isolated DELETE
- [x] 2.2 Agregar tabla `umbrales_materia` con FK a asignaciones (CASCADE), materias (CASCADE), constraint unique (asignacion_id, materia_id), columna valores_aprobatorios como JSONB

## 3. Repositorio

- [x] 3.1 Crear `repositories/calificaciones.py` con `CalificacionesRepository(BaseRepository)` con scope tenant
- [x] 3.2 Implementar `get_active_version_for_materia(materia_id) -> VersionPadron | None` (busca padron activo para la materia para validar que existan entradas)
- [x] 3.3 Implementar `get_threshold(asignacion_id, materia_id) -> UmbralMateria | None`
- [x] 3.4 Implementar `upsert_threshold(data) -> UmbralMateria` (crea o actualiza umbral)
- [x] 3.5 Implementar `bulk_create_calificaciones(entries: list[dict]) -> int` (bulk insert de calificaciones)
- [x] 3.6 Implementar `get_calificaciones(materia_id, filters: dict) -> list[Calificacion]` con filtros opcionales por actividad y aprobado
- [x] 3.7 Implementar `delete_calificaciones_scope(materia_id, cargado_por: str | None)` — scope-isolated: si cargado_por es None (COORDINADOR), borra todas; si tiene valor (PROFESOR), solo las del usuario

## 4. Schemas Pydantic

- [x] 4.1 Crear `schemas/calificaciones.py` con: `CalificacionOut`, `CalificacionListOut`, `ImportResultOut`, `PreviewActividadOut`, `PreviewResultOut`, `UmbralMateriaOut`, `UmbralMateriaUpdateIn` (todos con `extra='forbid'`)
- [x] 4.2 Schema `CalificacionOut`: id, entrada_padron_id, materia_id, actividad, nota_numerica (nullable), nota_textual (nullable), aprobado, origen, importado_at
- [x] 4.3 Schema `PreviewActividadOut`: nombre (str), tipo ("numerica" | "textual"), columna (str), total_alumnos (int)
- [x] 4.4 Schema `PreviewResultOut`: actividades (list[PreviewActividadOut]), total_alumnos (int), archivo (str)
- [x] 4.5 Schema `ImportConfirmIn`: actividades_seleccionadas (list[str], min 1)
- [x] 4.6 Schema `UmbralMateriaUpdateIn`: umbral_pct (int, ge=0, le=100, optional), valores_aprobatorios (list[str], optional)
- [x] 4.7 Schema `UmbralMateriaOut`: id, asignacion_id, materia_id, umbral_pct, valores_aprobatorios

## 5. Servicio de Calificaciones

- [x] 5.1 Crear `services/calificaciones.py` con `CalificacionesService`
- [x] 5.2 Implementar metodos de parseo de archivos (reutilizando patron de C-06): `_parse_csv`, `_parse_xlsx`, `_detect_columnas_notas` con deteccion de sufijo `(Real)` para nota numerica (RN-01)
- [x] 5.3 Implementar `preview_import(materia_id, file, filename) -> PreviewResultOut`: parsea archivo, detecta actividades, NO persiste
- [x] 5.4 Implementar `confirm_import(materia_id, file, filename, actividades_seleccionadas, usuario_id) -> ImportResultOut`: parsea archivo, filtra por actividades seleccionadas, deriva aprobado segun umbral configurado (D4), persiste atomicamente
- [x] 5.5 Implementar `_derivar_aprobado(nota_numerica, nota_textual, umbral_pct, valores_aprobatorios) -> bool` (D4)
- [x] 5.6 Implementar `_obtener_umbral(asignacion_id, materia_id) -> tuple[int, list[str]]`: devuelve (umbral_pct, valores_aprobatorios), default (60, ["Satisfactorio", "Supera lo esperado"])
- [x] 5.7 Implementar `list_calificaciones(materia_id, filters) -> list[CalificacionOut]`
- [x] 5.8 Implementar `clear_calificaciones(materia_id, usuario_id, es_coordinador)` — scope-isolated segun RN-04
- [x] 5.9 Implementar `set_threshold(materia_id, asignacion_id, data) -> UmbralMateriaOut`
- [x] 5.10 Implementar `get_threshold(materia_id, asignacion_id) -> UmbralMateriaOut` (retorna default si no existe)
- [x] 5.11 Registrar auditoria en import exitoso: `CALIFICACIONES_IMPORTAR` con actor_id, materia_id, filas_afectadas

## 6. Router (endpoints REST)

- [x] 6.1 Crear `routers/calificaciones.py` con prefijo `/api/materias/{materia_id}/calificaciones`
- [x] 6.2 Implementar `POST /importar` con query param `preview=true/false`: recibe UploadFile, si preview=true llama a preview_import, si no llama a confirm_import con body `ImportConfirmIn`
- [x] 6.3 Implementar `GET /`: listar calificaciones con filtros opcionales (actividad, aprobado)
- [x] 6.4 Implementar `DELETE /` con query param `confirmar=true`: scope-isolated segun rol del usuario
- [x] 6.5 Implementar `POST /umbral`: crear o actualizar umbral
- [x] 6.6 Implementar `GET /umbral`: obtener umbral configurado (o default)
- [x] 6.7 Integrar dependencia de autenticacion JWT + `require_permission` con permisos `calificaciones:importar`, `calificaciones:ver`, `calificaciones:vaciar`, `calificaciones:configurar-umbral`
- [x] 6.8 Validar que PROFESOR solo acceda a materias donde tiene asignacion activa; COORDINADOR a cualquier materia
- [x] 6.9 Registrar router en `app/api/v1/routers/__init__.py`

## 7. Tests

- [x] 7.1 Tests unitarios de deteccion de columnas de nota: headers con `(Real)` -> detectados como numericos, headers sin `(Real)` -> textuales, case-insensitive
- [x] 7.2 Tests de preview: archivo valido devuelve actividades sin persistir — integracion
- [x] 7.3 Tests de import exitoso: crea calificaciones con aprobado derivado correctamente — integracion
- [x] 7.4 Tests de derivacion de aprobado: nota numerica >= umbral -> True, < umbral -> False, textual en valores_aprobatorios -> True, no incluido -> False — integracion
- [x] 7.5 Tests de umbral configurable: crear umbral, obtener umbral, obtener default si no configurado — integracion
- [x] 7.6 Tests de scope-isolated DELETE: PROFESOR solo borra sus propias calificaciones, COORDINADOR borra todas — integracion
- [x] 7.7 Tests de validacion: archivo vacio -> 400, formato no soportado -> 400, actividades_seleccionadas vacio -> 400, DELETE sin confirmar -> 400 — integracion
- [x] 7.8 Tests de multi-tenant isolation: tenant A no ve datos de tenant B — integracion
- [x] 7.9 Tests de permisos: PROFESOR sin asignacion -> 403, COORDINADOR -> acceso global — integracion
