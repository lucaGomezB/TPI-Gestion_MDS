## Why

El equipo docente y de coordinacion necesita un mecanismo interno de asignacion y seguimiento de tareas administrativas que hoy no existe. Sin el, la delegacion de trabajo depende de canales informales (WhatsApp, email) sin trazabilidad, estados ni posibilidad de dar seguimiento a traves del tiempo. Este modulo introduce un workflow ligero de tareas internas dentro de la misma plataforma, aprovechando la estructura de roles y materias ya existente.

## What Changes

- Nuevos modelos `Tarea` y `ComentarioTarea` en core-models (E12 del modelo de datos).
- Nuevo endpoint `GET /api/tareas` para que un docente vea sus tareas asignadas, filtradas por contexto academico.
- Nuevo endpoint `POST /api/tareas` para que un profesor o coordinador asigne una tarea a otro docente.
- Nuevo endpoint `PUT /api/tareas/{id}/estado` para que el asignado o un administrador cambie el estado de una tarea (Pendiente -> En progreso -> Resuelta).
- Nuevo endpoint `POST /api/tareas/{id}/comentarios` para agregar comentarios a una tarea como parte del workflow asincronico.
- Nuevo endpoint `GET /api/admin/tareas` para que COORDINADOR y ADMIN tengan una vista global con filtros (docente, materia, estado, busqueda libre).
- Nuevos permisos: `tareas:ver`, `tareas:asignar`, `tareas:admin`.
- Migracion Alembic para las tablas `tareas` y `comentarios_tarea`.

## Capabilities

### New Capabilities
- `tareas-internas`: Gestion de tareas internas entre docentes y coordinacion, incluyendo asignacion, cambio de estado y comentarios con filtros y administracion global.

### Modified Capabilities
- `core-models`: Agregar entidades E12 (Tarea, ComentarioTarea) y el enum `EstadoTarea` al modelo de datos del nucleo.

## Impact

- **Backend**: Nuevo router `routers/tareas.py`, nuevo service `services/tareas.py`, nuevo repository `repositories/tareas.py`. Modificacion minima a `core-models` (nuevos modelos SQLAlchemy y schemas Pydantic).
- **Base de datos**: Nueva migracion Alembic con tablas `tareas` y `comentarios_tarea`, ambas con `tenant_id` para multi-tenancy.
- **Auth**: Nuevo permiso `tareas:*` en la matriz de permisos existente. Chequeo de permiso en cada endpoint via `require_permission`.
- **Dependencias**: Requiere C-04 (materias), C-05 (roles y asignaciones docentes), C-11 (comunicaciones para notificacion opcional), C-14 (encuentros/guardias como referencia de patron de repositorio).
