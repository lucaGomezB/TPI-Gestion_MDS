## Context

El sistema actual cuenta con los modelos base (Tenant, Usuario, Materia), el modulo de asignaciones docentes (C-05), y los modulos de comunicaciones (C-11), avisos (C-12), encuentros (C-14) y mensajeria (C-13). No existe un mecanismo interno de asignacion y seguimiento de tareas entre docentes y coordinacion.

El change C-16 agrega dos nuevas entidades: `Tarea` (E12 del modelo de datos) y `ComentarioTarea`. Ambas se integran con la estructura existente mediante FKs a `Usuario` (asignado_a, asignado_por) y `Materia` (nullable). El flujo de estados transita por: Pendiente -> En progreso -> Resuelta (con cancelacion posible desde cualquier estado).

## Goals / Non-Goals

**Goals:**
- Proveer endpoint `GET /api/tareas` para que un usuario vea sus tareas asignadas, filtradas por estado y materia.
- Proveer endpoint `POST /api/tareas` para asignar una tarea a otro docente, con trazabilidad del asignador.
- Proveer endpoint `PUT /api/tareas/{id}/estado` para cambiar el estado de una tarea siguiendo el flujo Pendiente -> En progreso -> Resuelta.
- Proveer endpoint `POST /api/tareas/{id}/comentarios` para agregar comentarios a una tarea como parte del workflow asincronico.
- Proveer endpoint `GET /api/admin/tareas` para que COORDINADOR y ADMIN tengan una vista global con filtros: docente asignado, asignador, materia, estado y busqueda libre.
- Migracion Alembic 011 con tablas `tareas` y `comentarios_tarea`.
- Nuevos permisos: `tareas:ver`, `tareas:asignar`, `tareas:admin`.

**Non-Goals:**
- Notificaciones automaticas sobre asignacion o cambio de estado — se manejara via C-11 (cola comunicaciones) en un change futuro.
- Archivos adjuntos en tareas o comentarios.
- Tareas recursivas o con subtareas.
- Flujo de aprobacion/rechazo de tareas (el modelo actual es informativo).
- Integracion con calendarios externos.

## Decisions

### Decision 1: Tarea como entidad con estado auditado (no solo log)

**Decision**: `Tarea` es una entidad persistente con ciclo de estados explícito (`Pendiente -> En progreso -> Resuelta`) y posibilidad de cancelacion desde cualquier estado. No es un log de auditoria ni un recordatorio ephemeral.

**Rationale**: El dominio exige trazabilidad: quien asigno, cuando, a quien, y el estado actual. Una tarea no es un evento sino un work item con ciclo de vida. Mantenerla como entidad permite filtrar, buscar y auditar.

**Alternativa considerada**: Modelar como un tipo de comunicacion (C-11) o aviso (C-12). Se descarto porque las tareas requieren seguimiento bidireccional (asignado puede responder con comentarios), a diferencia de las comunicaciones que son broadcasts unidireccionales.

### Decision 2: Estado solo avanza hacia adelante (no retroceso)

**Decision**: El estado de una tarea solo puede avanzar en la cadena: `Pendiente -> En progreso -> Resuelta`. La excepcion es `Cancelada`, que puede activarse desde cualquier estado. No se permite `Resuelta -> En progreso`.

**Rationale**: Evita cambios de estado ciclicos que dificultarian la auditoria. Si una tarea resuelta requiere atencion nuevamente, el asignador debe crear una nueva tarea. La cancelacion se permite desde cualquier estado porque puede haber necesidades operativas (tarea duplicada, contexto perdido).

**Alternativa considerada**: Estado libre (saltos arbitrarios). Se descarto porque podria generar inconsistencias (ej: Resuelta -> Pendiente sin justificacion).

### Decision 3: Comentarios como coleccion independiente (no denormalizados en Tarea)

**Decision**: `ComentarioTarea` es una entidad separada con FK a `Tarea`, con su propio `id`, `autor_id` y `creado_at`.

**Rationale**: Los comentarios son N por tarea, tienen su propia autoria y orden temporal. Denormalizarlos en un campo JSON de la tarea complicaria las queries de auditoria ("quien comento que"), el filtrado por autor y la proyeccion futura (adjuntos, edicion).

**Alternativa considerada**: Array JSONB en la tarea. Se descarto porque complica la auditoria individual de cada comentario y rompe el principio de que cada entidad tiene su tabla.

### Decision 4: materia_id nullable para tareas institucionales

**Decision**: `materia_id` en Tarea es nullable. Si es NULL, la tarea es de nivel institucional (no vinculada a una materia especifica).

**Rationale**: La coordinacion puede asignar tareas que no pertenecen a una materia en particular (ej: "Preparar informe general del cuatrimestre").

### Decision 5: Permisos RBAC alineados con funcionalidades existentes

**Decision**: Se agregan las siguientes acciones de permiso:
- `tareas:ver` — acceder a `GET /api/tareas` (TUTOR, PROFESOR, COORDINADOR)
- `tareas:asignar` — acceder a `POST /api/tareas` (PROFESOR, COORDINADOR)
- `tareas:admin` — acceder a `GET /api/admin/tareas` y cambiar cualquier estado (COORDINADOR, ADMIN)

**Rationale**: Sigue el patron existente de `modulo:accion` establecido en C-03. Los permisos reflejan directamente las funcionalidades F8.1, F8.2 y F8.3.

## Risks / Trade-offs

- **[Risk] Sin notificaciones automaticas**: Al asignar una tarea, el docente asignado no recibe notificacion automatica dentro del sistema. Queda fuera de scope de este change, pero debe considerarse en una iteracion futura integrada con C-11.
- **[Risk] Flujo de avance estricto**: Si un docente marca una tarea como `Resuelta` por error, no puede revertirla. El asignador debe crear una nueva tarea. Esto puede generar friccion operativa si ocurre frecuentemente. Mitigacion: COORDINADOR/ADMIN tienen permiso `tareas:admin` que podria habilitar un override en el futuro.
- **[Trade-off] Comentarios sin edicion ni borrado**: Los comentarios son inmutables (solo creacion y lectura). No se permite editar o borrar comentarios. Se acepta como trade-off para mantener la trazabilidad.
- **[Trade-off] contexto_id como UUID generico**: El campo `contexto_id` es un UUID nullable que permite referenciar cualquier entidad del dominio sin FK explicita. Esto es flexible pero no tiene integridad referencial a nivel DB. Se acepta como trade-off para no acoplar tareas a N tablas distintas.
