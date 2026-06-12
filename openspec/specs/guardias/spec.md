## ADDED Requirements

### Requirement: The system SHALL provide the Guardia model for duty records

The system MUST provide a `Guardia` model that records a duty shift (guardia) attended by a tutor or profesor, linked to an Asignacion, Materia, Carrera, and Cohorte.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `asignacion_id` | UUID (string) | FK -> asignaciones.id, NOT NULL |
| `materia_id` | UUID (string) | FK -> materias.id, NOT NULL |
| `carrera_id` | UUID (string) | FK -> carreras.id, NOT NULL |
| `cohorte_id` | UUID (string) | FK -> cohortes.id, NOT NULL |
| `dia` | String(10) | NOT NULL, values: Lunes, Martes, Miercoles, Jueves, Viernes, Sabado, Domingo |
| `horario` | String(50) | NOT NULL, free text (e.g. "14:00-14:45") |
| `estado` | String(20) | NOT NULL, default 'Pendiente', values: Pendiente, Realizada, Cancelada |
| `comentarios` | Text | Nullable |
| `creada_at` | DateTime(tz) | server default now() |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Indexes:
- `ix_guardias_tenant_materia` on (tenant_id, materia_id)
- `ix_guardias_asignacion_id` on (asignacion_id)
- `ix_guardias_estado` on (estado)

#### Scenario: Register a guardia with all required fields
- **WHEN** a POST request is sent to `/api/materias/{id}/guardias` with valid `asignacion_id`, `carrera_id`, `cohorte_id`, `dia='Miercoles'`, `horario='14:00-14:45'`, `estado='Pendiente'`, `comentarios='Atencion general'`
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain `id`, `asignacion_id`, `materia_id`, `carrera_id`, `cohorte_id`, `dia`, `horario`, `estado='Pendiente'`, `comentarios`, `creada_at`
- **THEN** `tenant_id` SHALL match the authenticated user's tenant

#### Scenario: Register a guardia with minimal fields
- **WHEN** a POST request is sent to `/api/materias/{id}/guardias` with only `asignacion_id`, `carrera_id`, `cohorte_id`, `dia='Viernes'`, `horario='10:00-11:00'`
- **THEN** the response SHALL have status `201`
- **THEN** `estado` SHALL default to `'Pendiente'`
- **THEN** `comentarios` SHALL be null

#### Scenario: Register guardia without guardias:registrar permission
- **WHEN** a user without `guardias:registrar` permission sends a POST to `/api/materias/{id}/guardias`
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL provide filtered queries for guardias

The system MUST provide an endpoint to query guardias by materia, with optional filters.

#### Scenario: Query guardias by materia
- **WHEN** a GET request is sent to `/api/materias/{id}/guardias`
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain a paginated list of `Guardia` records for that materia
- **THEN** each record SHALL include all attributes specified in the Guardia model
- **THEN** the list SHALL be ordered by `creada_at` descending

#### Scenario: Query guardias filtered by estado
- **WHEN** a GET request is sent to `/api/materias/{id}/guardias?estado=Pendiente`
- **THEN** the response SHALL only include guardias with `estado='Pendiente'`

#### Scenario: Query guardias with date range filter
- **WHEN** a GET request is sent to `/api/materias/{id}/guardias?desde=2026-08-01&hasta=2026-08-31`
- **THEN** the response SHALL only include guardias with `creada_at` within the specified range

#### Scenario: Query guardias without guardias:ver_todas permission
- **WHEN** a user without `guardias:ver_todas` permission sends a GET to `/api/materias/{id}/guardias`
- **THEN** the response SHALL have status `403`

#### Scenario: Query guardias for non-existent materia
- **WHEN** a GET request is sent to `/api/materias/{non_existent_id}/guardias`
- **THEN** the response SHALL have status `404`

### Requirement: The system SHALL scope guardia queries by tenant_id

All guardia queries MUST filter by the authenticated user's tenant_id. No guardia data from one tenant SHALL be visible to users of another tenant.

#### Scenario: Guardias are isolated by tenant
- **WHEN** a user from Tenant A queries guardias
- **THEN** the response SHALL NOT include guardias from Tenant B, even if they share the same materia_id

---

## ADDED Frontend Requirements (C-25)

### Requirement: El sistema SHALL proveer listado de guardias por materia

El sistema DEBE proveer una pagina en `/materias/:id/guardias` que muestre las guardias registradas (GET /api/materias/{id}/guardias). La pagina SHALL incluir:

- Tabla con columnas: Dia, Horario, Estado, Comentarios, Fecha de creacion
- Filtros: por estado (select), por rango de fechas (desde/hasta)
- Boton "Nueva guardia" que redirige a `/materias/:id/guardias/nuevo`
- Paginacion

#### Scenario: Cargar lista de guardias de una materia

- **WHEN** el usuario navega a `/materias/:id/guardias`
- **THEN** se muestra un indicador de carga
- **THEN** al cargar, se muestra la tabla paginada de guardias ordenada por fecha de creacion descendente

#### Scenario: Filtrar guardias por estado

- **WHEN** el usuario selecciona un estado en el filtro
- **THEN** la tabla se actualiza mostrando solo guardias con ese estado

#### Scenario: Sin guardias registradas

- **WHEN** la materia no tiene guardias registradas
- **THEN** se muestra un EmptyState con mensaje "No hay guardias registradas para esta materia"
- **THEN** el EmptyState incluye un boton "Registrar primera guardia"

### Requirement: El sistema SHALL proveer una pagina para registrar una nueva guardia

El sistema DEBE proveer una pagina con formulario para registrar una guardia (POST /api/materias/{id}/guardias). El formulario SHALL incluir:

- `asignacion_id`: selector de asignacion/docente (obligatorio)
- `carrera_id`: selector de carrera (obligatorio)
- `cohorte_id`: selector de cohorte (obligatorio)
- `dia`: selector enum (Lunes..Domingo, obligatorio)
- `horario`: input texto (obligatorio, ej: "14:00-14:45")
- `comentarios`: textarea (opcional)

#### Scenario: Registrar guardia exitosamente

- **WHEN** el usuario completa todos los campos obligatorios y presiona "Guardar"
- **THEN** se envia POST /api/materias/{id}/guardias
- **THEN** al recibir respuesta 201, se redirige a la lista de guardias
- **THEN** la nueva guardia aparece en la lista con estado "Pendiente"

#### Scenario: Validacion de campos obligatorios en formulario de guardia

- **WHEN** el usuario presiona "Guardar" sin completar campos obligatorios
- **THEN** se muestran mensajes de error debajo de cada campo invalido
- **THEN** el formulario no se envia
