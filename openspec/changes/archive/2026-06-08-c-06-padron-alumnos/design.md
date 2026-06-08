## Context

El padron de alumnos es la base sobre la que se construyen calificaciones (C-07), atrasados (C-09) y comunicaciones (C-11). El modelo de datos E6 ya esta definido en la KB: `VersionPadron` y `EntradaPadron` con versionado preservando historial. La RN-05 establece que la importacion es upsert destructivo: nueva version desactiva la anterior.

Ya existen en el codigo: modelos base con mixins (TimestampMixin, TenantMixin, AuditMixin), repositorio abstracto con filtro tenant, servicio de cifrado AES-256-GCM via `EncryptedString`, y estructura Clean Architecture (routers -> services -> repositories -> models).

## Goals / Non-Goals

**Goals:**
- Modelos SQLAlchemy para VersionPadron y EntradaPadron con herencia de mixins existentes.
- Endpoint POST para importar .xlsx/.csv con deteccion automatica de columnas.
- Endpoint GET para listar entradas activas del padron vigente.
- Endpoint GET para historial de versiones ordenado por fecha descendente.
- Email del alumno cifrado en reposo usando `EncryptedString` existente.
- Versionado: al crear nueva version, desactivar la anterior de la misma (materia, cohorte).
- Migracion Alembic 005.
- Tests: import exitoso, versionado, rollback en error, multi-tenant isolation, cifrado.

**Non-Goals:**
- Import desde Moodle directo (eso es C-08).
- Preview de datos antes de confirmar import (sera en futura iteracion).
- Export de padron (fuera de scope por ahora).

## Decisions

### D1: Capa de procesamiento de archivos separada en services/padron.py
- **Opcion A** (elegida): Servicio `PadronService` que recibe el archivo subido, lo parsea con openpyxl/csv, valida columnas y llama al repositorio.
- **Opcion B**: Logica de parseo en el router.
- **Por que**: Separar responsabilidades. El router solo recibe el archivo, lo delega al servicio. El servicio puede testearse sin HTTP.

### D2: Deteccion de columnas por heuristica simple
- Columnas requeridas: `nombre`, `apellido(s)` (o `apellidos`), `email`.
- Columnas opcionales: `comision`, `regional`.
- Se normalizan los headers: lower-case, strip. Si falta `nombre` o `email`, error 400 con detalle.
- No se hace fuzzy-matching en esta version. Si una columna no se reconoce, se ignora con warning.

### D3: Versionado atomico en transaccion SQL
- Al importar: inicio de transaccion, nueva VersionPadron con `activa=True`, desactivar version anterior (`activa=False`), insertar todas las EntradaPadron nuevas, commit.
- Si falla cualquier operacion intermedia (parseo, insercion), rollback total.
- Esto garantiza que el padron nunca quede en estado inconsistente.

### D4: `usuario_id` nullable en EntradaPadron
- Como especifica la KB E6: una entrada puede existir antes de que el alumno tenga cuenta.
- No se hace matching por email contra Usuario en esta iteracion. El match se hara en C-07 (calificaciones) cuando sea necesario.

### D5: Validacion de permisos coincidente con C-05
- PROFESOR puede importar/ver padron de materias donde tiene asignacion activa.
- COORDINADOR puede importar/ver padron de cualquier materia del tenant.
- Se reutiliza `require_permission` existente con permisos `padron:importar` y `padron:ver`.

### D6: Cifrado de email con EncryptedString
- El campo `email` de EntradaPadron usa `EncryptedString` del tipo existente en `models/types.py`.
- No requiere cambios en la capacidad pii-encryption, solo su uso.

### D7: Archivos de import se procesan en memoria
- Se usa `UploadFile` de FastAPI. El archivo se lee completo en memoria (los padrones tipicamente son < 5MB).
- Si en el futuro se necesitan archivos mas grandes, se puede pasar a streaming.

## Risks / Trade-offs

| Riesgo | Probabilidad | Mitigacion |
|--------|-------------|------------|
| Archivo mal formado (columnas faltantes) | Media | Validacion de columnas con error 400 descriptivo |
| Carga concurrente de padron para misma materia | Baja | La transaccion y constraint de una activa por (materia, cohorte) lo protege |
| Email no cifrado accidentalmente en log | Media | Revisar que logs no expongan campos del modelo directo; usar `EncryptedString` a nivel ORM |
| Archivos muy grandes (>10MB) | Baja | Lectura en memoria por ahora; futuro streaming si necesario |
