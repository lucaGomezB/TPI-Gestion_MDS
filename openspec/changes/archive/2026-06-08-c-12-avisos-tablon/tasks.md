## 1. Modelos y migracion

- [x] 1.1 Crear modelo `Aviso` en `backend/app/models/aviso.py` con campos: id, tenant_id, alcance (enum), materia_id (nullable), cohorte_id (nullable), rol_destino (nullable enum), severidad (enum), titulo, cuerpo, inicio_en, fin_en, orden, activo, requiere_ack. Heredar de AppModel + TimestampMixin + TenantMixin. No usar AuditMixin (tiene campo activo propio).
- [x] 1.2 Crear modelo `AcknowledgmentAviso` en `backend/app/models/acknowledgment_aviso.py` con campos: id, aviso_id (FK Aviso), usuario_id (FK Usuario), leido_en. Heredar de AppModel + TenantMixin (sin AuditMixin ni TimestampMixin).
- [x] 1.3 Registrar ambos modelos en `backend/app/models/__init__.py`.
- [x] 1.4 Crear migracion Alembic 010 (revision f6a7b8c9d0e1) con tablas `avisos` y `acknowledgments_avisos`, foreign keys a tenants, materias, cohortes, usuarios, y composite indexes: (tenant_id, inicio_en, fin_en, activo), (aviso_id, usuario_id) unique.

## 2. Permisos y enrutamiento

- [x] 2.1 Agregar permisos `avisos:publicar`, `avisos:ver`, `avisos:ack` en `backend/app/core/permissions.py` y asignarlos a los roles segun matriz: `avisos:publicar` -> COORDINADOR, ADMIN; `avisos:ver` y `avisos:ack` -> todos los roles.
- [x] 2.2 Crear schemas Pydantic v2 en `backend/app/schemas/aviso.py`: `AvisoCreate`, `AvisoUpdate`, `AvisoResponse`, `AvisoListResponse`, `AckResponse`, con `model_config = ConfigDict(extra='forbid')` y validacion de alcance vs. contexto (materia_id/cohorte_id obligatorios segun alcance).

## 3. CRUD administracion de avisos

- [x] 3.1 Crear `backend/app/repositories/aviso.py` con `AvisoRepository` heredando `BaseRepository[Aviso]`. Agregar metodos: `list_with_filters(activo, alcance, severidad)` para filtros admin, `get_with_ack_count()` que devuelva aviso con total de acknowledgments.
- [x] 3.2 Crear `backend/app/repositories/acknowledgment_aviso.py` con `AcknowledgmentRepository` heredando `BaseRepository[AcknowledgmentAviso]`. Agregar metodos: `find_by_aviso_and_user(aviso_id, usuario_id)` para idempotencia, `count_by_aviso(aviso_id)` para contadores.
- [x] 3.3 Crear `backend/app/services/aviso.py` con `AvisoService` que implemente logica de negocio: CRUD, soft deactivate en DELETE, scope filtering dinamico (RN-18, RN-20), acknowledgement (RN-19).
- [x] 3.4 Crear router admin en `backend/app/api/v1/routers/avisos_admin.py` con endpoints: `POST /api/admin/avisos` (crear), `GET /api/admin/avisos` (listar con filtros), `GET /api/admin/avisos/{id}` (detalle con contadores), `PUT /api/admin/avisos/{id}` (actualizar), `DELETE /api/admin/avisos/{id}` (desactivar). Todos protegidos con `require_permission("avisos:publicar")`.

## 4. Visualizacion y acknowledgment para usuarios

- [x] 4.1 Crear router publico en `backend/app/api/v1/routers/avisos_publico.py` con: `GET /api/avisos` (avisos visibles para el usuario autenticado, filtrados por alcance, vigencia, rol, severidad, ordenados por orden ASC luego created_at DESC). Protegido con `require_permission("avisos:ver")`.
- [x] 4.2 Implementar en `GET /api/avisos` el filtro combinado RN-20: si alcance=PorMateria, filtrar por materias del usuario; si alcance=PorCohorte, filtrar por cohortes del usuario; si alcance=PorRol, filtrar por rol_destino; si alcance=Global, no filtrar. Siempre aplicar filtro de vigencia (inicio_en <= now() AND fin_en >= now()) y activo=true.
- [x] 4.3 Crear endpoint `POST /api/avisos/{id}/ack` en router publico: registra acknowledgment con idempotencia (si ya existe, retorna el existente). Protegido con `require_permission("avisos:ack")`. Validar que aviso sea visible para el usuario y tenga requiere_ack=true.
- [x] 4.4 Agregar ambos routers (avisos_admin, avisos_publico) al enrutador principal de la aplicacion.

## 5. Tests

- [x] 5.1 Tests unitarios de schemas: validacion de alcance-contexto (PorMateria requiere materia_id, etc.), validacion vigencia (inicio < fin), extra='forbid'. 21 tests, all passing.
- [x] 5.2 Tests de CRUD admin: crear aviso, listar con filtros, obtener detalle, actualizar, desactivar. Incluir casos de error (campos faltantes, permisos insuficientes). Written in `tests/api/test_avisos_api.py`.
- [x] 5.3 Tests de visualizacion: filtro por alcance Global, PorMateria, PorCohorte, PorRol; filtro por vigencia (fuera de rango no aparece); orden; severidad filter. Written in `tests/api/test_avisos_api.py`.
- [x] 5.4 Tests de acknowledgment: ack exitoso, idempotencia (doble POST), rechazo si requiere_ack=false, rechazo si aviso no visible, 404 si no existe. Written in `tests/api/test_avisos_api.py`.
- [x] 5.5 Tests de aislamiento multi-tenant: verificar que datos de tenant A no sean visibles desde tenant B en todos los endpoints. Written in `tests/api/test_avisos_api.py`.
