## Context

Las calificaciones se construyen sobre el padron de alumnos (C-06): cada calificacion se asocia a una `EntradaPadron` (FK `entrada_padron_id`) para mantener trazabilidad entre alumnos, actividades y notas. Ya existen en el codigo: modelos base con mixins (TimestampMixin, TenantMixin, AuditMixin), repositorio abstracto con filtro tenant, servicio de cifrado AES-256-GCM via `EncryptedString` (aunque no se usa en calificaciones porque no almacenan PII directo), estructura Clean Architecture consolidada, y el servicio de importacion de padron con parseo de .xlsx/.csv sirve como referencia para el flujo de import.

El modelo de datos E7 (Calificacion) y E8 (UmbralMateria) ya estan definidos en la KB. Las RN-01 a RN-04 establecen las reglas de negocio clave.

Para el preview de actividades, el flujo es de dos fases:
1. `POST /importar?preview=true` — sube archivo, parsea, detecta actividades y devuelve vista previa SIN persistir.
2. `POST /importar?preview=false` (o sin preview) — recibe la misma carga mas `actividades_seleccionadas`, persiste atomicamente.

## Goals / Non-Goals

**Goals:**
- Modelos SQLAlchemy para `Calificacion` y `UmbralMateria` con herencia de mixins existentes.
- Endpoint POST para importar .xlsx/.csv con preview (2 fases: detectar actividades, luego confirmar con seleccion).
- Deteccion de columnas `(Real)` como nota numerica (RN-01).
- Mapeo de escala textual aprobatoria (RN-02) con valores por defecto: "Satisfactorio", "Supera lo esperado".
- Umbral configurable por (asignacion x materia): POST y GET (RN-03).
- Derivacion automatica de `aprobado` al persistir: si `nota_numerica`, compara con umbral; si solo `nota_textual`, evalua contra valores_aprobatorios.
- Endpoint DELETE para vaciar datos scope-isolated: solo datos del usuario ejecutor en esa materia (RN-04).
- Endpoint GET para listar calificaciones por materia.
- Migracion Alembic 009.
- Tests: import con preview, confirmacion, deteccion de columnas (Real), umbral, derivacion de aprobado, vaciado scope-isolated, multi-tenant isolation.

**Non-Goals:**
- Import desde Moodle directo (es C-08).
- Deteccion de atrasados (es C-09).
- Ranking de actividades (es C-10).
- Export de calificaciones (fuera de scope por ahora).
- Interfaz de usuario frontend (futura iteracion).

## Decisions

### D1: Preview como dos fases dentro del mismo endpoint
- **Opcion A** (elegida): Un unico endpoint `POST /importar` que acepta `?preview=true` (solo parsea y devuelve preview sin persistir) y `?preview=false` o sin parametro (persiste con actividades seleccionadas).
- **Opcion B**: Dos endpoints separados (`/preview` y `/confirmar`).
- **Por que**: Un solo endpoint reduce la superficie de API y simplifica el contrato. El parametro query `preview` cambia la semantica sin duplicar rutas. El preview devuelve actividades detectadas con indices; la confirmacion recibe indices de actividades a incluir.

### D2: Deteccion de columnas de nota numerica por sufijo `(Real)`
- Se normalizan headers: lowercase + strip. Si un header normalizado termina en `(real)`, se interpreta como nota numerica (RN-01).
- El nombre de la actividad se deriva del header sin el sufijo: `"TP 1 (Real)"` -> actividad `"TP 1"`, nota_numerica.
- Columnas que no terminan en `(Real)` se tratan como nota textual (ej: `"TP 1"` -> actividad `"TP 1"`, nota_textual).
- Si una misma actividad aparece como nota numerica y textual (ej: `"TP 1 (Real)"` y `"TP 1"`), se toma la numerica como prioritaria y la textual como respaldo (nota_textual solo si no hay nota_numerica).

### D3: Umbral configurable por (asignacion x materia), default 60%
- `UmbralMateria.asignacion_id` vincula la configuracion a la asignacion del docente (FK -> Asignacion).
- Si no existe un umbral configurado para la asignacion del usuario en la materia, se usa 60%.
- `valores_aprobatorios` es un JSONB `list<texto>` con valores por defecto: `["Satisfactorio", "Supera lo esperado"]`.

### D4: Derivacion de `aprobado` en servicio (no en DB)
- `aprobado` se calcula en el servicio al persistir cada calificacion, no es un computed column de la DB.
- Razones: depende del umbral configurado (que puede cambiar despues de la importacion), y de valores_aprobatorios que son configuracion de dominio.
- Si el umbral cambia posteriormente, las calificaciones existentes mantienen su valor de `aprobado` calculado al momento de importacion. El recalculo masivo se dejara para C-09 si es necesario.

### D5: Scope-isolated DELETE por (usuario_id x materia_id)
- RN-04: el DELETE de calificaciones solo afecta registros del usuario ejecutor.
- Se filtra por `usuario_id` obtenido del JWT (nunca del body/param).
- No afecta calificaciones cargadas por otros docentes en la misma materia.
- Esto requiere que `Calificacion` tenga un campo `cargado_por` (usuario_id) para filtrar correctamente.
- Para COORDINADOR: el DELETE aplica a todas las calificaciones de la materia (scope completo), no solo las propias.

### D6: Preview devuelve estructura de actividades detectadas
- Response de preview:
```json
{
  "actividades": [
    {"nombre": "TP 1", "tipo": "numerica", "columna": "TP 1 (Real)", "total_alumnos": 30},
    {"nombre": "TP 2", "tipo": "textual", "columna": "TP 2", "total_alumnos": 30}
  ],
  "total_alumnos": 30,
  "archivo": "calificaciones.xlsx"
}
```
- En la confirmacion (preview=false), el body incluye:
```json
{
  "actividades_seleccionadas": ["TP 1", "TP 2"]
}
```

### D7: Validacion de permisos coincidente con C-05/C-06
- PROFESOR puede importar/listar/vaciar/configurar umbral en materias donde tiene asignacion activa.
- COORDINADOR puede hacerlo en cualquier materia del tenant.
- Se reutiliza `require_permission` existente con permisos `calificaciones:importar`, `calificaciones:ver`, `calificaciones:vaciar`, `calificaciones:configurar-umbral`.

### D8: Parseo de archivos reutiliza patron de C-06
- Se reusa el mismo enfoque de C-06: `openpyxl` para .xlsx, `csv` stdlib para .csv, deteccion de columnas en servicio, procesamiento en memoria.
- A diferencia de padron, las columnas no son fijas: se detectan dinamicamente del archivo.

### D9: Calificacion sin `usuario_id` directo, usa `entrada_padron_id`
- El alumno se identifica via `entrada_padron_id` -> `EntradaPadron.usuario_id`.
- `Calificacion` no tiene `usuario_id` directo para evitar duplicacion con la FK a EntradaPadron.
- Para filtros por alumno, se join via EntradaPadron.

## Risks / Trade-offs

| Riesgo | Probabilidad | Mitigacion |
|--------|-------------|------------|
| Archivo mal formado (columnas no estandar) | Media | Deteccion robusta de columnas + error 400 descriptivo si no se detectan actividades |
| Umbral cambiado post-importacion | Media | `aprobado` se calcula al momento de import; recalculo masivo se manejara en C-09 |
| Vista previa pesada (muchas actividades x alumnos) | Baja | El preview solo devuelve metadatos de actividades, no los datos de cada alumno; el detalle se ve al consultar las calificaciones ya importadas |
| Actividad con mismo nombre en columna numerica y textual | Baja | D2 define prioridad: numerica > textual para el mismo nombre de actividad |
| Carga concurrente de calificaciones para misma materia | Baja | Transaccion atomica protege la integridad; cada import es independiente por usuario |
| Datos PII en calificaciones | Ninguno | Calificacion no almacena PII directo (solo FK a EntradaPadron que ya tiene cifrado) |
