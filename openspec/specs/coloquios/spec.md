## ADDED Requirements

### Requirement: The system SHALL provide an EvaluacionColoquio model for coloquio convocatorias

The system MUST provide an `EvaluacionColoquio` SQLAlchemy model representing a coloquio convocatoria (evaluation call) with configurable days and quotas per day. The model inherits from `AppModel`, `TimestampMixin`, and `TenantMixin`.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `materia_id` | UUID (string) | FK -> materias.id, NOT NULL |
| `titulo` | String(200) | NOT NULL |
| `dias` | JSONB | NOT NULL, default `[]`, array of `{"fecha": "YYYY-MM-DD", "cupos": int, "reservados": int}` |
| `creado_por` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `activa` | Boolean | NOT NULL, default `True` |

Indexes:
- `ix_eval_coloquio_tenant_materia` on (tenant_id, materia_id)

#### Scenario: Create an EvaluacionColoquio with days and quotas
- **WHEN** a POST request to `/api/materias/{materia_id}/coloquios` with `{"titulo": "Coloquio Final", "dias": [{"fecha": "2026-07-01", "cupos": 10}, {"fecha": "2026-07-02", "cupos": 8}]}` is sent by an authenticated COORDINADOR
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL include `id`, `materia_id`, `titulo`, `dias` (with each entry having `reservados=0`), `creado_por`, `activa=true`, `created_at`
- **THEN** `tenant_id` SHALL match the authenticated user's tenant

#### Scenario: Create EvaluacionColoquio without activa sets default true
- **WHEN** a POST request creates an EvaluacionColoquio without specifying `activa`
- **THEN** `activa` SHALL default to `True`

#### Scenario: Create EvaluacionColoquio without coloquios:crear permission
- **WHEN** a user without `coloquios:crear` permission sends a POST to `/api/materias/{id}/coloquios`
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL provide a ReservaColoquio model for student reservations

The system MUST provide a `ReservaColoquio` SQLAlchemy model representing a student's reservation of a coloquio turn on a specific day. The model inherits from `AppModel`, `TimestampMixin`, and `TenantMixin`.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `evaluacion_id` | UUID (string) | FK -> evaluaciones_coloquio.id, NOT NULL |
| `alumno_id` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `dia` | Date | NOT NULL |
| `confirmada` | Boolean | NOT NULL, default `False` |

Unique constraint on `(evaluacion_id, alumno_id)` -- un alumno solo puede tener una reserva por convocatoria.

Indexes:
- `ix_reserva_coloquio_evaluacion` on (evaluacion_id)
- `ix_reserva_coloquio_alumno` on (alumno_id)

#### Scenario: Student reserves a coloquio turn
- **WHEN** a POST request to `/api/coloquios/{evaluacion_id}/reservar` with `{"dia": "2026-07-01"}` is sent by an authenticated ALUMNO
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL include `id`, `evaluacion_id`, `alumno_id`, `dia`, `confirmada=false`, `created_at`
- **THEN** the corresponding day in the EvaluacionColoquio `dias` JSONB SHALL have `reservados` incremented by 1

#### Scenario: Reserve when no more cupos available
- **WHEN** a POST request to `/api/coloquios/{evaluacion_id}/reservar` is sent for a day where `reservados >= cupos`
- **THEN** the response SHALL have status `409`
- **THEN** the response detail SHALL indicate "No hay cupos disponibles para esa fecha"

#### Scenario: Reserve when student already has a reservation
- **WHEN** a POST request to `/api/coloquios/{evaluacion_id}/reservar` is sent by a student who already has a reservation for that evaluacion
- **THEN** the response SHALL have status `409`
- **THEN** the response detail SHALL indicate "El alumno ya tiene una reserva para esta convocatoria"

#### Scenario: Reserve without coloquios:reservar permission
- **WHEN** a user without `coloquios:reservar` permission posts a reservation
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL provide a ResultadoColoquio model for exam results

The system MUST provide a `ResultadoColoquio` SQLAlchemy model representing a student's grade/result for a coloquio. The model inherits from `AppModel`, `TimestampMixin`, and `TenantMixin`.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `evaluacion_id` | UUID (string) | FK -> evaluaciones_coloquio.id, NOT NULL |
| `alumno_id` | UUID (string) | FK -> usuarios.id, NOT NULL |
| `nota` | Numeric(5,2) | Nullable |
| `aprobado` | Boolean | NOT NULL |
| `registrado_por` | UUID (string) | FK -> usuarios.id, NOT NULL |

Unique constraint on `(evaluacion_id, alumno_id)` -- un resultado por alumno por evaluacion.

#### Scenario: Register a coloquio result
- **WHEN** a POST request to `/api/coloquios/{evaluacion_id}/resultados` with `{"alumno_id": "...", "nota": 8.5, "aprobado": true}` is sent by an authenticated PROFESOR or COORDINADOR
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL include `id`, `evaluacion_id`, `alumno_id`, `nota`, `aprobado`, `registrado_por`, `created_at`

#### Scenario: Register result for non-existent evaluacion
- **WHEN** a POST request to `/api/coloquios/{non_existent_id}/resultados` is sent
- **THEN** the response SHALL have status `404`

#### Scenario: Register duplicate result
- **WHEN** a POST request registers a result for an alumno that already has a result for that evaluacion
- **THEN** the response SHALL have status `409`
- **THEN** the response detail SHALL indicate "El alumno ya tiene un resultado registrado"

#### Scenario: Register result without coloquios:resultados permission
- **WHEN** a user without `coloquios:resultados` permission posts a result
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL provide an endpoint to import students into a coloquio convocatoria

The system MUST provide an endpoint to load or update the roster of students eligible for a specific coloquio convocatoria.

#### Scenario: Import students to a coloquio from materia padron
- **WHEN** a POST request to `/api/materias/{materia_id}/coloquios/importar-alumnos` with `{"evaluacion_id": "..."}` is sent by an authenticated COORDINADOR
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL include a list of alumnos imported (from the materia's active padron)
- **THEN** the response SHALL include a count of imported alumnos

#### Scenario: Import students without coloquios:importar permission
- **WHEN** a user without `coloquios:importar` permission sends the import request
- **THEN** the response SHALL have status `403`

#### Scenario: Import when materia has no active padron
- **WHEN** the materia has no active padron version
- **THEN** the response SHALL have status `400`
- **THEN** the response detail SHALL indicate "La materia no tiene un padron activo"

### Requirement: The system SHALL provide an agenda endpoint for consolidated reservations view

The system MUST provide an endpoint to view all reservations for a given coloquio convocatoria, grouped by day.

#### Scenario: Get agenda of a coloquio
- **WHEN** a GET request to `/api/coloquios/{evaluacion_id}/agenda` is sent by an authenticated PROFESOR or COORDINADOR
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain a list of days, each with:
  - `fecha`: the day date
  - `cupos`: total available slots
  - `reservados`: count of reservations made
  - `reservas`: list of reservations with `alumno_id`, `alumno_nombre`, `alumno_apellidos`, `confirmada`
- **THEN** the response SHALL be ordered by `fecha` ascending

#### Scenario: Get agenda for non-existent evaluacion
- **WHEN** a GET request to `/api/coloquios/{non_existent_id}/agenda` is sent
- **THEN** the response SHALL have status `404`

#### Scenario: Get agenda without coloquios:ver_agenda permission
- **WHEN** a user without `coloquios:ver_agenda` permission requests the agenda
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL provide an admin metrics endpoint for coloquio overview

The system MUST provide a global metrics endpoint for COORDINADOR/ADMIN to see the overview of all coloquios in the tenant.

#### Scenario: Get coloquio metrics
- **WHEN** a GET request to `/api/admin/coloquios/metricas` is sent by an authenticated COORDINADOR or ADMIN
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL include:
  - `total_convocatorias`: total coloquio evaluaciones (activas)
  - `total_alumnos_importados`: count of unique students imported across all coloquios
  - `total_reservas_activas`: count of active reservations
  - `total_resultados_registrados`: count of registered results
- **THEN** the response SHALL be scoped to the authenticated user's tenant

#### Scenario: Get metrics without coloquios:metricas permission
- **WHEN** a user without `coloquios:metricas` permission requests metrics
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL log all significant coloquio actions to the audit log

Every create, reserve, and result registration SHALL produce an audit log entry.

#### Scenario: Audit log on coloquio creation
- **WHEN** a coloquio convocatoria is created
- **THEN** an AuditLog entry SHALL be created with `accion='COLOQUIO_CREAR'`, `actor_id=<current_user>`, `materia_id=<materia_id>`, `filas_afectadas=1`

#### Scenario: Audit log on reservation
- **WHEN** a student reserves a coloquio turn
- **THEN** an AuditLog entry SHALL be created with `accion='COLOQUIO_RESERVAR'`, `actor_id=<current_user>`, `materia_id=<materia_id from evaluacion>`, `filas_afectadas=1`

#### Scenario: Audit log on result registration
- **WHEN** a coloquio result is registered
- **THEN** an AuditLog entry SHALL be created with `accion='COLOQUIO_RESULTADO'`, `actor_id=<current_user>`, `materia_id=<materia_id from evaluacion>`, `filas_afectadas=1`

### Requirement: All coloquio queries SHALL be scoped by tenant_id

All coloquio data queries MUST filter by the authenticated user's tenant_id. No coloquio data from one tenant SHALL be visible to users of another tenant.

#### Scenario: Coloquio data is isolated by tenant
- **WHEN** a user from Tenant A queries coloquios
- **THEN** the response SHALL NOT include coloquio data from Tenant B, even if they share the same materia_id

---

## ADDED Frontend Requirements (C-25)

### Requirement: El sistema SHALL proveer una pagina de listado de convocatorias de coloquio

El sistema DEBE proveer una pagina en `/coloquios` que muestre las convocatorias de coloquio activas. La pagina SHALL incluir:

- Tabla con columnas: Materia, Titulo, Instancia, Dias disponibles, Convocados, Reservas activas, Cupos libres, Acciones
- Filtro por materia
- Boton "Nueva convocatoria" que redirige a `/coloquios/nuevo`
- Paginacion

#### Scenario: Cargar listado de convocatorias

- **WHEN** el usuario navega a `/coloquios`
- **THEN** se muestra un indicador de carga
- **THEN** al cargar, se muestra la tabla con las convocatorias activas

#### Scenario: Sin convocatorias activas

- **WHEN** no hay convocatorias activas
- **THEN** se muestra un EmptyState con mensaje "No hay convocatorias de coloquio activas"
- **THEN** el EmptyState incluye un boton "Crear primera convocatoria"

### Requirement: El sistema SHALL proveer una pagina para crear una convocatoria de coloquio

El sistema DEBE proveer una pagina con formulario para crear una convocatoria de coloquio (POST /api/materias/{id}/coloquios). El formulario SHALL incluir:

- `materia_id`: selector/autocomplete de materia (obligatorio)
- `titulo`: texto (obligatorio, max 200 chars)
- `dias`: lista dinamica de dias con fecha y cupos. Cada entrada incluye:
  - `fecha`: date picker (obligatorio)
  - `cupos`: input number (obligatorio, >= 1)
- Boton "Agregar dia" para anadir filas a la lista de dias
- Boton "Eliminar" por fila de dia

#### Scenario: Crear convocatoria exitosamente

- **WHEN** el usuario completa materia, titulo y al menos un dia con cupos
- **THEN** se envia POST /api/materias/{id}/coloquios
- **THEN** al recibir respuesta 201, se redirige al listado de convocatorias

#### Scenario: Agregar y eliminar dias en el formulario

- **WHEN** el usuario presiona "Agregar dia"
- **THEN** una nueva fila con date picker y campo de cupos se anade al formulario
- **WHEN** el usuario presiona "Eliminar" en una fila
- **THEN** esa fila se elimina del formulario

#### Scenario: Validar al menos un dia

- **WHEN** el usuario presiona "Guardar" sin agregar ningun dia
- **THEN** se muestra un mensaje de error: "Debe agregar al menos un dia disponible"

### Requirement: El sistema SHALL proveer acciones sobre convocatorias individuales

Cada convocatoria en el listado SHALL tener acciones disponibles:

- "Ver agenda" -> `/coloquios/:id/agenda`
- "Resultados" -> `/coloquios/:id/resultados`
- (solo ADMIN) "Cerrar convocatoria" -> cambia `activa` a false

#### Scenario: Cerrar convocatoria

- **WHEN** el usuario ADMIN presiona "Cerrar convocatoria"
- **THEN** se muestra un dialogo de confirmacion
- **THEN** al confirmar, se envia la peticion para desactivar la convocatoria
- **THEN** la convocatoria desaparece del listado de activas

### Requirement: El sistema SHALL proveer una pagina de agenda de reservas de coloquio

El sistema DEBE proveer una pagina en `/coloquios/:id/agenda` que muestre la agenda consolidada de una convocatoria (GET /api/coloquios/{id}/agenda). La pagina SHALL incluir:

- Cabecera con datos de la convocatoria: materia, titulo, estado
- Lista de dias agrupados, cada dia muestra:
  - Fecha, cupos totales, reservados, cupos libres
  - Tabla de reservas: Alumno, Confirmada (si/no), Acciones
- Los dias se muestran ordenados por fecha ascendente

#### Scenario: Cargar agenda de convocatoria

- **WHEN** el usuario navega a `/coloquios/:id/agenda`
- **THEN** se muestra un indicador de carga
- **THEN** al cargar, se muestran los dias con sus reservas agrupadas

#### Scenario: Agenda sin reservas

- **WHEN** la convocatoria no tiene reservas
- **THEN** se muestra un EmptyState por dia indicando "Sin reservas para esta fecha"

#### Scenario: Convocatoria no encontrada

- **WHEN** el id de la convocatoria no existe (respuesta 404)
- **THEN** se muestra un ErrorDisplay con mensaje "Convocatoria no encontrada"

### Requirement: El sistema SHALL proveer una pagina de resultados de coloquio

El sistema DEBE proveer una pagina en `/coloquios/:id/resultados` para registrar y consultar resultados de coloquio (POST /api/coloquios/{id}/resultados). La pagina SHALL incluir:

- Cabecera con datos de la convocatoria
- Tabla de alumnos convocados con columnas: Alumno, Nota, Aprobado, Acciones
- Boton "Registrar resultado" por fila (si no tiene resultado)
- Formulario inline o modal para ingresar nota y estado de aprobacion
- Los resultados ya registrados se muestran como solo lectura

#### Scenario: Cargar pagina de resultados

- **WHEN** el usuario navega a `/coloquios/:id/resultados`
- **THEN** se muestra un indicador de carga
- **THEN** al cargar, se muestran los alumnos con sus resultados (si existen)

#### Scenario: Registrar resultado de alumno

- **WHEN** el usuario presiona "Registrar resultado" en una fila sin resultado
- **THEN** se abre un modal o formulario inline con campos: nota (number), aprobado (checkbox/toggle)
- **WHEN** el usuario completa y confirma
- **THEN** se envia POST /api/coloquios/{id}/resultados
- **THEN** al recibir respuesta 201, la fila se actualiza mostrando el resultado como solo lectura

#### Scenario: Error al registrar resultado duplicado

- **WHEN** el servidor responde 409 (resultado ya existe para ese alumno)
- **THEN** se muestra un mensaje de error informando que el alumno ya tiene resultado registrado
- **THEN** la pagina recarga los datos para reflejar el estado actual

### Requirement: El sistema SHALL proveer un panel de metricas globales de coloquios

El sistema DEBE proveer una pagina en `/admin/coloquios` que muestre las metricas globales de coloquios del tenant (GET /api/admin/coloquios/metricas). La pagina SHALL incluir:

- Tarjetas de resumen (KPIs) con:
  - Total de convocatorias activas
  - Total de alumnos importados
  - Total de reservas activas
  - Total de resultados registrados
- Lista de convocatorias activas con enlaces rapidos a agenda y resultados
- Acceso al listado completo de convocatorias

#### Scenario: Cargar panel de metricas

- **WHEN** el usuario COORDINADOR o ADMIN navega a `/admin/coloquios`
- **THEN** se muestra un indicador de carga
- **THEN** al cargar, se muestran las 4 tarjetas KPI con valores numericos
- **THEN** cada tarjeta incluye una etiqueta descriptiva y el valor

#### Scenario: Sin datos de coloquios

- **WHEN** no hay convocatorias ni datos de coloquios en el tenant
- **THEN** las tarjetas KPI muestran valor 0
- **THEN** se muestra un mensaje informativo "No hay datos de coloquios para mostrar"

#### Scenario: Error al cargar metricas

- **WHEN** el servidor responde con error
- **THEN** se muestra un ErrorDisplay con opcion de reintentar
