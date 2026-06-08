## Why

Docentes y coordinadores necesitan importar las calificaciones de actividades evaluables desde los archivos .xlsx/.csv exportados del LMS para consolidar notas, detectar alumnos atrasados y generar reportes. Sin este modulo, las calificaciones existen solo en el LMS y no se pueden cruzar con el padron de alumnos (C-06) ni alimentar los modulos de analisis (C-09, C-10). El umbral de aprobacion debe ser configurable por docente y materia para reflejar las pautas pedagogicas de cada comision.

## What Changes

- Nuevos modelos `Calificacion` y `UmbralMateria` con herencia de mixins existentes (AppModel, TimestampMixin, TenantMixin).
- `POST /api/materias/{id}/calificaciones/importar` — importacion de .xlsx/.csv con deteccion de columnas de nota numerica (headers que terminan en `(Real)`, RN-01), mapeo de escala textual aprobatoria (RN-02) y vista previa de actividades detectadas antes de confirmar.
- `GET /api/materias/{id}/calificaciones` — listar calificaciones importadas para una materia.
- `DELETE /api/materias/{id}/calificaciones` — vaciar datos scope-isolated (RN-04): solo datos del usuario ejecutor en esa materia.
- `POST /api/materias/{id}/calificaciones/umbral` — configurar umbral de aprobacion por (asignacion x materia), default 60% (RN-03).
- `GET /api/materias/{id}/calificaciones/umbral` — obtener umbral configurado.
- Derivacion del campo `aprobado`: si existe `nota_numerica`, compara con umbral configurado; si solo existe `nota_textual`, evalua contra `valores_aprobatorios` configurados.
- Migracion Alembic 009: tablas `calificaciones` y `umbrales_materia`.
- Auditoria: registro de accion `CALIFICACIONES_IMPORTAR` en AuditLog.

## Capabilities

### New Capabilities
- `calificaciones`: importacion de calificaciones con deteccion de actividades, preview antes de confirmar, umbral configurable por asignacion x materia, listado y vaciado scope-isolated.

### Modified Capabilities
- `padron-alumnos`: las `EntradaPadron` existentes ahora reciben calificaciones asociadas a traves de la FK `entrada_padron_id` en `Calificacion` (no requiere cambios en la spec existente, solo uso de las entradas activas).
- `core-models`: agregar modelos `Calificacion` y `UmbralMateria` al catalogo de modelos del dominio.

## Impact

| Area | Impact | Description |
|------|--------|-------------|
| `models/calificaciones.py` | New | Modelos Calificacion y UmbralMateria |
| `repositories/calificaciones.py` | New | Repositorio con scope tenant, filtro por materia y usuario |
| `services/calificaciones.py` | New | Logica de import con preview, umbral, derivacion de aprobado, vaciado scope-isolated |
| `routers/calificaciones.py` | New | Endpoints REST (import con preview, list, delete, umbral CR) |
| `schemas/calificaciones.py` | New | Schemas Pydantic con `extra='forbid'` |
| `alembic/versions/009_*.py` | New | Migracion de tablas calificaciones y umbrales_materia |
| `services/auditoria.py` | Modified | Agregar codigo `CALIFICACIONES_IMPORTAR` |
| `app/__init__.py` / `app/api/v1/routers/__init__.py` | Modified | Registrar nuevo router y modelos |
