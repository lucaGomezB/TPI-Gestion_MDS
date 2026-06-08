## 1. Modelos SQLAlchemy

- [x] 1.1 Crear `models/padron.py` con `VersionPadron` (AppModel, TimestampMixin, TenantMixin) y columnas: id, tenant_id, materia_id, cohorte_id, cargado_por, cargado_at, activa
- [x] 1.2 Crear `EntradaPadron` (AppModel, TimestampMixin, TenantMixin) con columnas: id, version_id, tenant_id, usuario_id (nullable), nombre, apellidos, email (EncryptedString), comision, regional
- [x] 1.3 Agregar relaciones SQLAlchemy: VersionPadron.entradas (one-to-many), EntradaPadron.version (many-to-one), VersionPadron.materia (M:N indirecto via FK)
- [x] 1.4 Registrar ambos modelos en `models/__init__.py`

## 2. Migracion Alembic

- [x] 2.1 Generar migracion 008 (depende de 007): tabla `versiones_padron` con FK a materias, cohortes, usuarios + indice compuesto (materia_id, cohorte_id, activa)
- [x] 2.2 Agregar tabla `entradas_padron` con FK a versiones_padron (CASCADE), FK a usuarios (nullable), columna email cifrada (TEXT)
- [ ] 2.3 Ejecutar migracion en base de test y verificar tablas (requiere PostgreSQL + Docker)

## 3. Repositorio

- [x] 3.1 Crear `repositories/padron.py` con `PadronRepository(BaseRepository)` con scope tenant
- [x] 3.2 Implementar `get_active_version(materia_id, cohorte_id) -> VersionPadron | None`
- [x] 3.3 Implementar `get_entries(version_id) -> list[EntradaPadron]`
- [x] 3.4 Implementar `deactivate_version(version_id)` (set activa=False)
- [x] 3.5 Implementar `create_version(data) -> VersionPadron` (crea nueva version activa)
- [x] 3.6 Implementar `create_entries(version_id, entries_data) -> int` (bulk insert de entradas)
- [x] 3.7 Implementar `get_version_history(materia_id) -> list[VersionPadron]` con total_entradas count
- [x] 3.8 Implementar `get_active_entries(materia_id) -> list[EntradaPadron]` via active version

## 4. Schemas Pydantic

- [x] 4.1 Crear `schemas/padron.py` con: `VersionPadronOut`, `EntradaPadronOut`, `VersionHistoryOut`, `ImportResultOut`, `PadronListOut` (todos con `extra='forbid'`)
- [x] 4.2 Validacion de nombres de columnas esperadas en request de import (en `_detect_columns`)

## 5. Servicio de Padron

- [x] 5.1 Crear `services/padron.py` con `PadronService`
- [x] 5.2 Implementar `import_roster(materia_id, cohorte_id, file, usuario_id)`: parseo de .xlsx (openpyxl) y .csv (csv stdlib), deteccion de columnas, validacion, versionado atomico
- [x] 5.3 Implementar deteccion de columnas: normalizar headers a lowercase+strip, requerir `nombre` y `email`, ignorar columnas no reconocidas con log warning
- [x] 5.4 Implementar validaciones pre-import: archivo vacio, columnas faltantes, formato no soportado
- [x] 5.5 Implementar transaccion atomica: crear version -> desactivar anterior -> bulk insert entradas -> commit
- [x] 5.6 Implementar `get_active_entries(materia_id)` para listar padron activo
- [x] 5.7 Implementar `get_version_history(materia_id)` para historial con total_entradas
- [x] 5.8 Registrar auditoria en import exitoso: `PADRON_CARGAR` con actor_id, materia_id, filas_afectadas

## 6. Router (endpoints REST)

- [x] 6.1 Crear `routers/padron.py` con prefijo `/api/materias/{materia_id}/padron`
- [x] 6.2 Implementar `POST /importar`: recibe UploadFile, llama a service, devuelve resultado
- [x] 6.3 Implementar `GET /`: listar entradas activas del padron
- [x] 6.4 Implementar `GET /versiones`: historial de versiones
- [x] 6.5 Integrar dependencia de autenticacion JWT + `require_permission("padron:importar")` y `require_permission("padron:ver")`
- [x] 6.6 Validar que PROFESOR solo acceda a materias donde tiene asignacion activa; COORDINADOR a cualquier materia

## 7. Tests

- [x] 7.1 Tests unitarios de deteccion de columnas: headers correctos, faltantes, con espacios, case-insensitive
- [x] 7.2 Tests de import exitoso con .xlsx (crea version, desactiva version anterior, crea entradas) — integracion
- [x] 7.3 Tests de import exitoso con .csv (delimitador coma y punto y coma) — integracion
- [x] 7.4 Tests de validacion: archivo vacio -> 400, columnas faltantes -> 400, formato no soportado -> 400 — integracion
- [x] 7.5 Tests de versionado: nueva version desactiva la anterior, historial preserva todas — integracion
- [x] 7.6 Tests de rollback en error: si falla la insercion intermedia, no queda version huerfana — integracion
- [x] 7.7 Tests de multi-tenant isolation: tenant A no ve datos de tenant B — integracion
- [x] 7.8 Tests de permisos: PROFESOR sin asignacion -> 403, COORDINADOR -> acceso global — integracion
- [x] 7.9 Tests de cifrado: email en EntradaPadron cifrado en DB, legible en atributo del modelo — integracion
