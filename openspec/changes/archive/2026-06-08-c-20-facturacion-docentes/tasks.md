## 1. Modelo y Esquemas

- [x] 1.1 Crear modelo `Factura` (E20) en `backend/app/models/factura.py` con campos: id, tenant_id, usuario_id, periodo, detalle, referencia_archivo, tamano_kb, estado (Pendiente|Abonada), cargada_at, abonada_at. Seguir patron de Liquidacion (D-03: custom estado, sin AuditMixin).
- [x] 1.2 Crear enums `EstadoFactura` (Pendiente, Abonada) y schemas Pydantic en `backend/app/schemas/factura.py`: `FacturaCreate`, `FacturaResponse`, `FacturaDetailResponse`, `FacturaListResponse`. Todos con `extra='forbid'`.
- [x] 1.3 Crear migracion Alembic `alembic/versions/a3b4c5d6e7f8_014_create_facturas.py` para tabla `facturas` con columnas, FK a `usuarios.id`, indexes (tenant_id+periodo, usuario_id, tenant_id+estado).

## 2. Repositorio

- [x] 2.1 Crear `FacturaRepository` en `backend/app/repositories/factura.py` con metodos:
  - `create(data)` — crear factura
  - `find_by_id(id)` — single lookup scoped by tenant
  - `find_by_usuario(usuario_id, periodo, page, page_size)` — historial del propio docente
  - `find_all(estado, periodo, usuario_id, q, page, page_size)` — admin view con filtros combinacionales
  - `save(factura)` — persistir cambios (flush)
- [x] 2.2 Registrar repositorio en `backend/app/repositories/__init__.py`

## 3. Servicio

- [x] 3.1 Crear `FacturaService` en `backend/app/services/factura.py` con metodos:
  - `subir_factura(usuario_id, periodo, detalle, archivo_bytes, nombre_archivo)` — validar facturador=true, validar PDF, almacenar archivo, crear Factura
  - `get_historial(usuario_id, periodo, page, page_size)` — historial del docente
  - `get_admin_view(estado, periodo, usuario_id, q, page, page_size)` — admin view
  - `abonar(id, descargar=False)` — marcar como Abonada + opcional descarga PDF
  - `get_factura(id)` — single lookup for download endpoint
  - Validar estado: 409 si ya Abonada, 403 si no facturador, 400 si no PDF
- [x] 3.2 Registrar servicio en `backend/app/services/__init__.py`

## 4. Endpoints

- [x] 4.1 Crear router docente `backend/app/api/v1/routers/docente_facturas.py`:
  - `POST /api/docentes/facturas` — subir factura PDF (permiso `facturas:subir`, requiere facturador=true)
  - `GET /api/docentes/facturas` — historial propio (permiso `facturas:subir`)
- [x] 4.2 Crear router admin `backend/app/api/v1/routers/admin_facturas.py`:
  - `GET /api/admin/facturas` — gestion con filtros (permiso `facturas:gestionar`)
  - `GET /api/admin/facturas/{id}/descargar` — descargar PDF
  - `PUT /api/admin/facturas/{id}/abonar` — marcar abonada (permiso `facturas:gestionar`)
- [x] 4.3 Registrar ambos routers en `backend/app/api/v1/routers/__init__.py` y en `backend/app/api/v1/__init__.py`
- [x] 4.4 Agregar permisos `facturas:subir` y `facturas:gestionar` en el sistema de permisos (core/permissions)

## 5. Almacenamiento de Archivos

- [x] 5.1 Implementar mecanismo de almacenamiento de PDF (reutilizar patron de E16 - ProgramaMateria): directorio configurable `UPLOAD_DIR`, archivo con UUID como nombre, referencia opaca en `referencia_archivo`.
- [x] 5.2 Validacion de upload: Content-Type=application/pdf, tamano maximo configurable (default 10 MB).
- [x] 5.3 Endpoint de descarga (`GET /api/admin/facturas/{id}/descargar`): leer archivo del storage y devolver como FileResponse.

## 6. Tests

- [x] 6.1 Tests unitarios del modelo Factura (creacion, estados, validaciones) — 15 tests
- [x] 6.2 Tests del repositorio (CRUD, filtros, scope tenant) — 7 interface + 13 integration
- [x] 6.3 Tests del servicio (upload valido, upload no-facturante rechazado, abonar, conflictos) — 11 tests
- [x] 6.4 Tests de integracion de endpoints (autenticacion, permisos, flujo completo subir-listar-abonar) — 17 integration tests
