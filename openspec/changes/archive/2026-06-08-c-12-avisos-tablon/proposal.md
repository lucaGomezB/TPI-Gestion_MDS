## Why

Coordinadores y administradores necesitan un mecanismo centralizado para comunicar novedades institucionales a los distintos actores del sistema (docentes, tutores, alumnos) de forma segmentada y controlada. Sin un tablon de avisos, las comunicaciones importantes se mezclan con la mensajeria interna o se pierden. Se necesita un canal propio con alcance configurable, ventana de vigencia, severidad y opcion de acuse de recibo obligatorio.

## What Changes

- Nuevos modelos `Aviso` y `AcknowledgmentAviso` en SQLAlchemy con migracion Alembic (migracion 008).
- CRUD administrativo completo via `POST/GET/PUT/DELETE /api/admin/avisos` para COORDINADOR y ADMIN.
- Endpoint publico `GET /api/avisos` que devuelve los avisos visibles para el usuario autenticado, filtrados por alcance, vigencia, rol y severidad.
- Endpoint `POST /api/avisos/{id}/ack` para que el usuario confirme lectura de un aviso con `requiere_ack=true`.
- La segmentacion por audiencia sigue RN-20: combinacion de alcance (Global, PorMateria, PorCohorte, PorRol), contexto (materia_id, cohorte_id), rol_destino y severidad.
- La ventana de vigencia sigue RN-18: solo visible dentro del rango `inicio_en` a `fin_en`.
- Tests unitarios e integracion: CRUD, scope filtering, vigencia, multi-tenant.

## Capabilities

### New Capabilities
- `avisos-admin`: CRUD administrativo de avisos del sistema (alta, baja, modificacion, listado con filtros) para COORDINADOR y ADMIN.
- `avisos-visualizacion`: Visualizacion de avisos visibles para el usuario autenticado con filtrado por alcance, vigencia y rol destino.
- `avisos-acknowledgment`: Confirmacion de lectura (ack) para avisos que lo requieran, con registro de usuario y timestamp.

### Modified Capabilities
- Ninguna. Esta es una nueva funcionalidad independiente.

## Impact

- `backend/`: nuevo modulo `backend/app/avisos/` con router, service, repository, schemas y models.
- `backend/app/models/`: nuevos modelos `Aviso` y `AcknowledgmentAviso` (entidades E13 del modelo de datos).
- `backend/alembic/versions/`: nueva migracion 008 con tablas `avisos` y `acknowledgments_avisos`.
- `backend/app/core/security.py`: nuevo permiso `avisos:publicar` en la matriz RBAC.
- Tests: nuevo archivo de tests por endpoint y por logica de negocio (filtrado, vigencia, multi-tenant).
- No afecta modulos existentes. Depende de modelos base (Tenant, Usuario, Materia, Cohorte) ya implementados en changes previos.
