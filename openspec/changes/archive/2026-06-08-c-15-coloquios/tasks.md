## 1. Models

- [x] 1.1 Create `EvaluacionColoquio` model in `app/models/evaluacion_coloquio.py` with fields: id, tenant_id, materia_id, titulo, dias (JSONB), creado_por, activa, created_at, updated_at. Inherits AppModel, TimestampMixin, TenantMixin.
- [x] 1.2 Create `ReservaColoquio` model in `app/models/reserva_coloquio.py` with fields: id, tenant_id, evaluacion_id, alumno_id, dia (Date), confirmada, created_at, updated_at. Unique on (evaluacion_id, alumno_id). Inherits AppModel, TimestampMixin, TenantMixin.
- [x] 1.3 Create `ResultadoColoquio` model in `app/models/resultado_coloquio.py` with fields: id, tenant_id, evaluacion_id, alumno_id, nota (Numeric(5,2)), aprobado, registrado_por, created_at, updated_at. Unique on (evaluacion_id, alumno_id). Inherits AppModel, TimestampMixin, TenantMixin.
- [x] 1.4 Register new models in `app/models/__init__.py`

## 2. Migrations

- [x] 2.1 Generate Alembic migration for `evaluaciones_coloquio`, `reservas_coloquio`, `resultados_coloquio` tables with all indexes and foreign keys
- [x] 2.2 Verify migration up/down works (file parsed, chain validated)

## 3. Pydantic Schemas

- [x] 3.1 Create `app/schemas/coloquios.py` with: `EvaluacionColoquioCreate`, `EvaluacionColoquioResponse` (with from_attributes), `DiaColoquioSchema` (fecha, cupos, reservados)
- [x] 3.2 Add schemas: `ReservaColoquioCreate`, `ReservaColoquioResponse`, `ResultadoColoquioCreate`, `ResultadoColoquioResponse`
- [x] 3.3 Add schemas: `AgendaColoquioResponse` (grouped by day with nested reservas), `ImportarAlumnosResponse`, `MetricasColoquioResponse`
- [x] 3.4 Add schema: `ColoquioListResponse` (paginated wrapper)
- [x] 3.5 Register schemas in `app/schemas/__init__.py`

## 4. Repositories

- [x] 4.1 Create `EvaluacionColoquioRepository` in `app/repositories/coloquios.py` with methods: create, get_by_id, list_by_materia, update, list_activas (tenant-scoped)
- [x] 4.2 Add `ReservaColoquioRepository` with methods: create, get_by_id, list_by_evaluacion, get_by_alumno_y_evaluacion, count_reservas_por_dia
- [x] 4.3 Add `ResultadoColoquioRepository` with methods: create, get_by_id, list_by_evaluacion, get_by_alumno_y_evaluacion, count_total
- [x] 4.4 Add `ColoquioAdminRepository` with methods: get_metricas (total_convocatorias, total_reservas, total_resultados)
- [x] 4.5 Register repositories in `app/repositories/__init__.py`

## 5. Unit of Work Integration

- [x] 5.1 Add `coloquio_evaluacion`, `coloquio_reserva`, `coloquio_resultado`, `coloquio_admin` properties to `UnitOfWork` in `app/core/unit_of_work.py`

## 6. Services

- [x] 6.1 Create `ColoquioService` in `app/services/coloquios.py` with method `crear_convocatoria` that validates materia exists, builds DiasColoquio from input, creates EvaluacionColoquio, logs audit (COLOQUIO_CREAR)
- [x] 6.2 Add method `importar_alumnos` that reads active padron for materia and links alumnos to the evaluacion (stores list of imported alumno_ids)
- [x] 6.3 Add method `reservar_turno` that validates cupos disponibles (reservados < cupos), checks no duplicate reservation, creates ReservaColoquio, updates JSONB reservados counter, logs audit (COLOQUIO_RESERVAR)
- [x] 6.4 Add method `obtener_agenda` that returns consolidated view with reservas per day
- [x] 6.5 Add method `registrar_resultado` that validates no duplicate result, creates ResultadoColoquio, logs audit (COLOQUIO_RESULTADO)
- [x] 6.6 Add method `obtener_metricas` for admin panel
- [x] 6.7 Register service in `app/services/__init__.py`

## 7. Permissions

- [x] 7.1 Define permission strings in `app/core/permissions.py`: `coloquios:crear`, `coloquios:importar`, `coloquios:reservar`, `coloquios:ver_agenda`, `coloquios:resultados`, `coloquios:metricas`

## 8. API Routers

- [x] 8.1 Create `app/api/v1/routers/coloquios.py` with router for `/api/materias/{materia_id}/coloquios` endpoints: POST (crear), POST (importar-alumnos)
- [x] 8.2 Add router for `/api/coloquios/{evaluacion_id}` endpoints: POST (reservar), GET (agenda), POST (resultados)
- [x] 8.3 Add router for `/api/admin/coloquios/metricas` endpoint: GET (metricas)
- [x] 8.4 Register all routers in main app (`app/main.py`)

## 9. Audit Actions

- [x] 9.1 Register audit action codes: `COLOQUIO_CREAR`, `COLOQUIO_RESERVAR`, `COLOQUIO_RESULTADO` in audit constants/seeds

## 10. Tests

- [x] 10.1 Write tests for EvaluacionColoquio model creation and JSONB dias behavior
- [x] 10.2 Write tests for ReservaColoquio (create, duplicate, cupo overflow)
- [x] 10.3 Write tests for ResultadoColoquio (create, duplicate)
- [x] 10.4 Write integration tests for all 6 endpoints (201, 403, 404, 409 scenarios)
- [x] 10.5 Write tenant isolation test (Tenant A data invisible to Tenant B)
- [x] 10.6 Write audit log tests for each auditable action
