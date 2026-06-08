## 1. Models

- [x] 1.1 Create `backend/app/models/slot_encuentro.py` with `SlotEncuentro` model (tenant_id, asignacion_id, materia_id, titulo, hora, dia_semana, fecha_inicio, cant_semanas, fecha_unica, meet_url, vig_desde, vig_hasta)
- [x] 1.2 Create `backend/app/models/instancia_encuentro.py` with `InstanciaEncuentro` model (tenant_id, slot_id nullable, materia_id, fecha, hora, titulo, estado, meet_url, video_url, comentario)
- [x] 1.3 Create `backend/app/models/guardia.py` with `Guardia` model (tenant_id, asignacion_id, materia_id, carrera_id, cohorte_id, dia, horario, estado, comentarios, creada_at)
- [x] 1.4 Register all three models in `backend/app/models/__init__.py`

## 2. Repositories

- [x] 2.1 Create `SlotEncuentroRepository` with CRUD + list by materia + tenant-scoped queries
- [x] 2.2 Create `InstanciaEncuentroRepository` with CRUD + list by slot/materia + bulk create for slot generation + tenant-scoped queries
- [x] 2.3 Create `GuardiaRepository` with CRUD + list by materia with filters (estado, date range) + tenant-scoped queries
- [x] 2.4 Register all repositories in `backend/app/repositories/__init__.py`

## 3. Services

- [x] 3.1 Create `EncuentroService` with:
  - `crear_slot_recurrente()` — creates slot + generates N `InstanciaEncuentro`
  - `crear_encuentro_unico()` — creates InstanciaEncuentro without slot
  - `editar_instancia()` — updates individual instance fields (estado, meet_url, video_url, comentario)
  - `generar_embed()` — generates HTML/Markdown snippet for Moodle
- [x] 3.2 Create `GuardiaService` with:
  - `registrar_guardia()` — creates a new Guardia record
  - `listar_guardias()` — queries guardias with optional estado and date range filters
- [x] 3.3 Register both services in `backend/app/services/__init__.py`

## 4. API Routes

- [x] 4.1 Create `backend/app/api/v1/routers/encuentros.py` with:
  - `POST /api/materias/{id}/encuentros/slot` — crear slot recurrente (F6.1)
  - `POST /api/materias/{id}/encuentros/unico` — crear encuentro unico (F6.2)
  - `PUT /api/encuentros/{id}` — editar instancia individual (F6.3, RN-14)
  - `POST /api/materias/{id}/encuentros/embed` — generar snippet HTML/Markdown (F6.4)
  - `GET /api/admin/encuentros` — vista transversal (F6.5)
- [x] 4.2 Create `backend/app/api/v1/routers/guardias.py` with:
  - `POST /api/materias/{id}/guardias` — registro de guardia (F6.6)
  - `GET /api/materias/{id}/guardias` — consulta de guardias con filtros (F6.6)
- [x] 4.3 Register both routers in `backend/app/api/v1/routers/__init__.py` and `backend/app/main.py`

## 5. Pydantic Schemas

- [x] 5.1 Create `backend/app/schemas/encuentros.py` with request/response schemas for SlotEncuentro and InstanciaEncuentro (all with `extra='forbid'`)
- [x] 5.2 Create `backend/app/schemas/guardias.py` with request/response schemas for Guardia (all with `extra='forbid'`)

## 6. Permissions

- [x] 6.1 Add permission actions `encuentros:crear`, `encuentros:editar`, `encuentros:ver_todas`, `guardias:registrar`, `guardias:ver_todas` to `backend/app/core/permissions.py`
- [x] 6.2 Apply `require_permission` decorators to all new endpoints

## 7. Migration

- [x] 7.1 Generate Alembic migration 008 with tables: `slots_encuentro`, `instancias_encuentro`, `guardias`
- [ ] 7.2 Verify migration runs cleanly (upgrade + downgrade) — requires running PostgreSQL

## 8. Tests

- [x] 8.1 Write tests for slot recurrente creation (happy path, 422 on invalid dates, permission check)
- [x] 8.2 Write tests for encuentro unico creation (happy path, slot_id=null)
- [x] 8.3 Write tests for instancia edicion (estado change, video_url, comentario, 404, permission check)
- [x] 8.4 Write tests for embed generation (HTML format, Markdown format, empty list)
- [x] 8.5 Write tests for vista transversal (COORDINADOR access, ADMIN access, forbidden role, filter by materia/estado)
- [x] 8.6 Write tests for guardia registration (happy path, minimal fields, permission check)
- [x] 8.7 Write tests for guardia queries (by materia, filter by estado, date range, tenant isolation)
- [ ] 8.8 Verify test coverage meets >= 80% lines, >= 90% business rules — requires running coverage suite
