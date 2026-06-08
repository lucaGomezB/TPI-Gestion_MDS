## 1. Modelos y Migracion

- [x] 1.1 Crear modelos SQLAlchemy `Tarea` y `ComentarioTarea` en `models/` con `tenant_id`, relaciones y enum `EstadoTarea`
- [x] 1.2 Crear schemas Pydantic para Tarea (`TareaCreate`, `TareaRead`, `TareaEstadoUpdate`, `TareaFilter`) y ComentarioTarea (`ComentarioCreate`, `ComentarioRead`) con `extra='forbid'`
- [x] 1.3 Generar migracion Alembic 009 con tablas `tareas` y `comentarios_tarea`, indices y FKs (merge de las 3 ramas 008)

## 2. Repositorios

- [x] 2.1 Implementar `TareaRepository` con metodos: `list_by_asignado`, `list_all` (admin con filtros), `get_by_id`, `create`, `update_estado`, `add_comentario`, `get_comentarios`, `get_comentario_count`
- [x] 2.2 Implementar scoping por `tenant_id` en todas las queries del repositorio

## 3. Servicios y Logica de Negocio

- [x] 3.1 Implementar `TareaService` con validaciones de estado (forward-only flow: Pendiente -> En progreso -> Resuelta, Cancelada desde cualquier estado)
- [x] 3.2 Implementar validacion de que solo el asignado o admin pueden cambiar estado
- [x] 3.3 Implementar validacion de que el usuario asignador existe y tiene relacion valida con el contexto

## 4. Endpoints de API

- [x] 4.1 Implementar `GET /api/tareas` — lista de tareas del usuario autenticado con filtros (estado, materia_id)
- [x] 4.2 Implementar `POST /api/tareas` — asignar tarea con trazabilidad de asignador
- [x] 4.3 Implementar `PUT /api/tareas/{id}/estado` — cambiar estado con validacion de transicion
- [x] 4.4 Implementar `POST /api/tareas/{id}/comentarios` — agregar comentario a tarea
- [x] 4.5 Implementar `GET /api/admin/tareas` — vista global con filtros (asignado_a, asignado_por, materia_id, estado, q)

## 5. Permisos y Seguridad

- [x] 5.1 Registrar permisos `tareas:ver`, `tareas:asignar`, `tareas:admin` en la matriz de permisos existente
- [x] 5.2 Aplicar `require_permission` en cada endpoint segun la funcionalidad (F8.1, F8.2, F8.3)

## 6. Tests

- [x] 6.1 Tests unitarios para `TareaService` (transiciones de estado, validaciones, permiso) — 11 tests, todos pasan
- [x] 6.2 Tests de integracion para cada endpoint (201, 403, 404, 422 segun escenarios del spec) — 18 tests (skipped, require PostgreSQL)
- [x] 6.3 Test de aislamiento multi-tenant (datos de un tenant no visibles en otro) — incluido en tests API
