## Why

Docentes y coordinadores necesitan cargar el listado de alumnos habilitados para una materia desde archivos .xlsx/.csv exportados del LMS. Sin un padron versionado, no hay forma de registrar que alumnos cursan cada materia ni de asociar calificaciones (C-07), atrasados (C-09) ni comunicaciones (C-11) a los estudiantes correctos.

## What Changes

- Nuevos modelos `VersionPadron` y `EntradaPadron` con versionado: cada import genera una nueva version que desactiva la anterior.
- `POST /api/materias/{id}/padron/importar` — import de .xlsx/.csv con deteccion de columnas (nombre, apellidos, email, comision, regional).
- `GET /api/materias/{id}/padron` — listar entradas activas de la materia.
- `GET /api/materias/{id}/padron/versiones` — historial de versiones cargadas.
- Email del alumno cifrado en reposo (AES-256-GCM) via `EncryptedString` existente.
- Migracion Alembic 005: tablas `versiones_padron`, `entradas_padron`.
- Auditoria: registro de accion `PADRON_CARGAR` en AuditLog.

## Capabilities

### New Capabilities
- `padron-alumnos`: versionado de alumnos por materia, con import destructivo (RN-05), consulta de entradas activas e historial de versiones.

### Modified Capabilities
- `core-models`: agregar modelos VersionPadron y EntradaPadron al catalogo de modelos del dominio.
- `pii-encryption`: el campo `email` de EntradaPadron usa el TypeDecorator `EncryptedString` existente (no requiere cambios en la capacidad).

## Impact

| Area | Impact | Description |
|------|--------|-------------|
| `models/padron.py` | New | Modelos VersionPadron y EntradaPadron |
| `repositories/padron.py` | New | Repositorio con scope tenant, filtro por materia |
| `services/padron.py` | New | Logica de import, versionado, validacion de columnas |
| `routers/padron.py` | New | Endpoints REST (import, list, versiones) |
| `schemas/padron.py` | New | Schemas Pydantic con `extra='forbid'` |
| `alembic/versions/005_*.py` | New | Migracion de tablas |
| `services/auditoria.py` | Modified | Agregar codigo `PADRON_CARGAR` |
