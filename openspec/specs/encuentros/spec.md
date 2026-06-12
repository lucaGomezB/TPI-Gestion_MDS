## ADDED Requirements

### Requirement: The system SHALL provide the SlotEncuentro model for recurring meeting templates

The system MUST provide a `SlotEncuentro` model that defines a recurring meeting template linked to an Asignacion and a Materia. The model supports two mutually exclusive modes: recurring (day_of_week + hour + start_date + num_weeks) and single date (fecha_unica).

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `asignacion_id` | UUID (string) | FK -> asignaciones.id, NOT NULL |
| `materia_id` | UUID (string) | FK -> materias.id, NOT NULL |
| `titulo` | String(255) | NOT NULL |
| `hora` | Time | NOT NULL |
| `dia_semana` | String(10) | NOT NULL, values: Lunes, Martes, Miercoles, Jueves, Viernes, Sabado, Domingo |
| `fecha_inicio` | Date | NOT NULL for recurring mode |
| `cant_semanas` | Integer | NOT NULL default 0, 0 = single date |
| `fecha_unica` | Date | Nullable, used only when cant_semanas=0 |
| `meet_url` | String(500) | Nullable |
| `vig_desde` | Date | NOT NULL |
| `vig_hasta` | Date | Nullable |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Indexes:
- `ix_slots_encuentro_tenant_materia` on (tenant_id, materia_id)
- `ix_slots_encuentro_asignacion_id` on (asignacion_id)

#### Scenario: Create recurring slot generates N instances
- **WHEN** a POST request is sent to `/api/materias/{id}/encuentros/slot` with valid `titulo='Clase Semanal'`, `hora='18:00'`, `dia_semana='Martes'`, `fecha_inicio='2026-08-01'`, `cant_semanas=4`, `meet_url='https://meet.example.com/abc'`
- **THEN** the response SHALL have status `201`
- **THEN** the response body SHALL contain `id`, `titulo`, `hora`, `dia_semana`, `fecha_inicio`, `cant_semanas=4`
- **THEN** the system SHALL create exactly 4 `InstanciaEncuentro` records linked to this slot, one per week starting from `fecha_inicio`

#### Scenario: Create slot with cant_semanas=0 creates single instance
- **WHEN** a POST request is sent to `/api/materias/{id}/encuentros/slot` with `cant_semanas=0` and `fecha_unica='2026-08-15'`
- **THEN** the response SHALL have status `201`
- **THEN** the system SHALL create exactly 1 `InstanciaEncuentro` record with `fecha='2026-08-15'`

#### Scenario: Create single encounter (non-recurring, no slot)
- **WHEN** a POST request is sent to `/api/materias/{id}/encuentros/unico` with valid `fecha='2026-08-20'`, `hora='10:00'`, `titulo='Clase Extra'`, `meet_url='https://meet.example.com/extra'`
- **THEN** the response SHALL have status `201`
- **THEN** the response SHALL contain `id`, `fecha`, `hora`, `titulo`, `estado='Programado'`, `meet_url`
- **THEN** the created `InstanciaEncuentro` SHALL have `slot_id=null`

#### Scenario: Create slot with invalid date range (vig_desde after vig_hasta)
- **WHEN** a POST request is sent with `vig_desde='2026-12-31'` and `vig_hasta='2026-03-01'`
- **THEN** the response SHALL have status `422`

#### Scenario: Create slot without materias:crear permission
- **WHEN** a user without `encuentros:crear` permission sends a POST to `/api/materias/{id}/encuentros/slot`
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL provide the InstanciaEncuentro model for individual meetings

The system MUST provide an `InstanciaEncuentro` model representing a concrete meeting instance, optionally linked to a SlotEncuentro (`slot_id` nullable). Each instance has its own independent state per RN-14.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `slot_id` | UUID (string) | FK -> slots_encuentro.id, nullable |
| `materia_id` | UUID (string) | FK -> materias.id, NOT NULL |
| `fecha` | Date | NOT NULL |
| `hora` | Time | NOT NULL |
| `titulo` | String(255) | NOT NULL |
| `estado` | String(20) | NOT NULL, default 'Programado', values: Programado, Realizado, Cancelado |
| `meet_url` | String(500) | Nullable |
| `video_url` | String(500) | Nullable |
| `comentario` | Text | Nullable |
| `created_at` | DateTime(tz) | server default now() |
| `updated_at` | DateTime(tz) | server default now(), onupdate now() |

Indexes:
- `ix_instancias_encuentro_slot_id` on (slot_id)
- `ix_instancias_encuentro_materia_fecha` on (materia_id, fecha)

#### Scenario: Edit instance estado independently
- **WHEN** a PUT request is sent to `/api/encuentros/{id}` with `estado='Realizado'`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `estado='Realizado'`
- **THEN** other instances from the same slot SHALL remain unchanged

#### Scenario: Edit instance with video_url and comentario
- **WHEN** a PUT request is sent to `/api/encuentros/{id}` with `video_url='https://drive.example.com/grabacion'` and `comentario='Se vio toda la clase'`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `video_url` and `comentario`

#### Scenario: Edit non-existent instance returns 404
- **WHEN** a PUT request is sent to `/api/encuentros/{id}` with a non-existent UUID
- **THEN** the response SHALL have status `404`

#### Scenario: Edit instance without encuentros:editar permission
- **WHEN** a user without `encuentros:editar` permission sends a PUT to `/api/encuentros/{id}`
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL generate an embeddable HTML/Markdown snippet for Moodle

The system MUST provide an endpoint that returns a formatted HTML or Markdown snippet containing the scheduled meetings for a materia, ready to be embedded in Moodle.

#### Scenario: Generate HTML snippet with all scheduled instances
- **WHEN** a POST request is sent to `/api/materias/{id}/encuentros/embed` with `formato='html'`
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain a `snippet` field with valid HTML content
- **THEN** the HTML SHALL include a table with column headers: Fecha, Hora, Titulo, Enlace
- **THEN** the HTML SHALL only include instances with `estado='Programado'`

#### Scenario: Generate Markdown snippet
- **WHEN** a POST request is sent to `/api/materias/{id}/encuentros/embed` with `formato='markdown'`
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain a `snippet` field with valid Markdown content

#### Scenario: Generate snippet with no scheduled instances
- **WHEN** a POST request is sent for a materia with no `Programado` instances
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain a `snippet` field with a message indicating no encuentros are scheduled

#### Scenario: Generate snippet without encuentros:crear permission
- **WHEN** a user without `encuentros:crear` permission requests an embed
- **THEN** the response SHALL have status `403`

### Requirement: The system SHALL provide a transversal view of all encuentros for COORDINADOR and ADMIN

The system MUST provide an endpoint that returns all encuentros (instances) across the entire tenant, regardless of which profesor created them.

#### Scenario: View all encuentros as COORDINADOR
- **WHEN** a GET request is sent to `/api/admin/encuentros` by a user with COORDINADOR role
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain a paginated list of `InstanciaEncuentro` records across all materias of the tenant
- **THEN** each record SHALL include `id`, `titulo`, `fecha`, `hora`, `estado`, `materia_id`, `materia_nombre`, `meet_url`, `video_url`, `comentario`

#### Scenario: View all encuentros as ADMIN
- **WHEN** a GET request is sent to `/api/admin/encuentros` by a user with ADMIN role
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain records across all materias

#### Scenario: View encuentros without encuentros:ver_todas permission
- **WHEN** a user without `encuentros:ver_todas` permission requests `/api/admin/encuentros`
- **THEN** the response SHALL have status `403`

#### Scenario: Filter encuentros by materia_id and estado
- **WHEN** a GET request is sent to `/api/admin/encuentros?materia_id={uuid}&estado=Programado`
- **THEN** the response SHALL only include instances matching the given materia_id and estado

---

## ADDED Frontend Requirements (C-25)

### Requirement: El sistema SHALL proveer una pagina para crear slot recurrente de encuentro

El sistema DEBE proveer una pagina con formulario validado para crear un slot de encuentro recurrente (POST /api/materias/{id}/encuentros/slot). El formulario SHALL incluir los siguientes campos:

- `materia_id`: selector/autocomplete de materia (obligatorio)
- `titulo`: texto (obligatorio, max 255 chars)
- `dia_semana`: selector enum (Lunes..Domingo, obligatorio)
- `hora`: input time (obligatorio)
- `fecha_inicio`: date picker (obligatorio)
- `cant_semanas`: input number (obligatorio, >= 0)
- `meet_url`: input URL (opcional)

#### Scenario: Crear slot recurrente exitosamente

- **WHEN** el usuario completa todos los campos obligatorios con valores validos y presiona "Guardar"
- **THEN** el formulario se deshabilita durante el envio
- **THEN** se muestra un indicador de carga
- **THEN** al recibir respuesta 201, se redirige a la lista de encuentros con un mensaje de exito
- **THEN** el mensaje de exito indica la cantidad de instancias generadas

#### Scenario: Validacion client-side de campos obligatorios

- **WHEN** el usuario presiona "Guardar" sin completar campos obligatorios
- **THEN** se muestran mensajes de error debajo de cada campo invalido
- **THEN** el formulario no se envia al servidor

#### Scenario: Error del servidor al crear slot

- **WHEN** el servidor responde con error 422 (validacion) o 403 (sin permiso)
- **THEN** se muestra un ErrorDisplay con el mensaje del servidor
- **THEN** el formulario se rehabilita para permitir correcciones

### Requirement: El sistema SHALL proveer una pagina para crear encuentro unico

El sistema DEBE proveer una pagina con formulario validado para crear un encuentro unico (POST /api/materias/{id}/encuentros/unico). El formulario SHALL incluir los siguientes campos:

- `materia_id`: selector de materia (obligatorio)
- `titulo`: texto (obligatorio, max 255 chars)
- `fecha`: date picker (obligatorio)
- `hora`: input time (obligatorio)
- `meet_url`: input URL (opcional)

#### Scenario: Crear encuentro unico exitosamente

- **WHEN** el usuario completa el formulario con fecha, hora, titulo y materia validos
- **THEN** al recibir respuesta 201, se redirige a la lista de encuentros
- **THEN** el encuentro aparece en la lista con estado "Programado"

#### Scenario: Alternar entre modo recurrente y unico

- **WHEN** el usuario accede a la pagina de creacion
- **THEN** puede seleccionar entre "Slot recurrente" y "Encuentro unico" mediante un toggle o tabs
- **THEN** el formulario se adapta mostrando los campos correspondientes a cada modo

### Requirement: El sistema SHALL proveer una pagina para editar una instancia de encuentro

El sistema DEBE proveer una pagina con formulario para editar una instancia de encuentro individual (PUT /api/encuentros/{id}). La pagina SHALL cargar los datos actuales del encuentro y permitir modificar:

- `estado`: selector enum (Programado, Realizado, Cancelado) -- obligatorio
- `meet_url`: input URL (opcional)
- `video_url`: input URL (opcional, visible solo si estado=Realizado o se permite post-evento)
- `comentario`: textarea multilinea (opcional)

#### Scenario: Cargar datos del encuentro al abrir edicion

- **WHEN** el usuario navega a `/encuentros/:id/editar`
- **THEN** se muestra un indicador de carga mientras se obtienen los datos
- **THEN** al cargar, el formulario se inicializa con los valores actuales del encuentro

#### Scenario: Editar estado del encuentro exitosamente

- **WHEN** el usuario cambia el estado a "Realizado" y presiona "Guardar"
- **THEN** se envia PUT /api/encuentros/{id} con los datos modificados
- **THEN** al recibir respuesta 200, se redirige a la lista de encuentros
- **THEN** se muestra un mensaje de exito

#### Scenario: Agregar video_url y comentario post-evento

- **WHEN** el usuario establece estado=Realizado, completa video_url y comentario
- **THEN** el formulario permite guardar todos los campos simultaneamente
- **THEN** al recargar la pagina, los campos persisten con los valores guardados

#### Scenario: Error al editar encuentro inexistente

- **WHEN** el id del encuentro no existe (respuesta 404)
- **THEN** se muestra un ErrorDisplay con mensaje "Encuentro no encontrado"
- **THEN** se provee un boton para volver a la lista

#### Scenario: Edicion sin permiso

- **WHEN** el usuario no tiene permiso `encuentros:editar` (respuesta 403)
- **THEN** se muestra un ErrorDisplay con mensaje de permiso denegado

### Requirement: El sistema SHALL proveer una pagina para generar snippet embed de encuentros para Moodle

El sistema DEBE proveer una pagina donde el usuario selecciona una materia, solicita el snippet (POST /api/materias/{id}/encuentros/embed) y puede copiar el resultado al portapapeles. La pagina SHALL ofrecer:

- Selector de materia
- Selector de formato: HTML o Markdown
- Boton "Generar snippet"
- Textarea de solo lectura con el resultado
- Boton "Copiar al portapapeles" con feedback visual

#### Scenario: Generar snippet HTML exitosamente

- **WHEN** el usuario selecciona una materia, formato HTML y presiona "Generar"
- **THEN** se muestra un indicador de carga
- **THEN** al recibir respuesta, el textarea muestra el snippet HTML generado
- **THEN** el boton "Copiar al portapapeles" se habilita

#### Scenario: Copiar snippet al portapapeles

- **WHEN** el usuario presiona "Copiar al portapapeles"
- **THEN** el contenido del textarea se copia al portapapeles del navegador
- **THEN** el boton muestra brevemente un feedback visual (ej: "Copiado!" por 2 segundos)

#### Scenario: Generar snippet Markdown

- **WHEN** el usuario selecciona formato Markdown y presiona "Generar"
- **THEN** el snippet se genera en formato Markdown
- **THEN** el textarea muestra el contenido Markdown

#### Scenario: Materia sin encuentros programados

- **WHEN** la materia seleccionada no tiene encuentros con estado Programado
- **THEN** se muestra un EmptyState indicando que no hay encuentros programados para esa materia

#### Scenario: Error de generacion

- **WHEN** el servidor responde con error al generar el snippet
- **THEN** se muestra un ErrorDisplay con el mensaje de error
- **THEN** el usuario puede reintentar

### Requirement: El sistema SHALL proveer una pagina de vista transversal de encuentros para COORDINADOR y ADMIN

El sistema DEBE proveer una pagina en `/admin/encuentros` que muestre todas las instancias de encuentro del tenant (GET /api/admin/encuentros). La pagina SHALL incluir:

- Tabla con columnas: Fecha, Hora, Titulo, Estado, Materia, Enlace Meet, Acciones
- Filtros: por materia (autocomplete), por estado (select enum), por rango de fechas
- Paginacion
- Boton de accion "Editar" por fila que redirige a `/encuentros/:id/editar`

#### Scenario: Cargar lista transversal de encuentros

- **WHEN** el usuario COORDINADOR o ADMIN navega a `/admin/encuentros`
- **THEN** se muestra un indicador de carga
- **THEN** al cargar, se muestra la tabla paginada con todos los encuentros del tenant
- **THEN** cada fila muestra materia_nombre ademas de los datos del encuentro

#### Scenario: Filtrar encuentros por materia

- **WHEN** el usuario selecciona una materia en el filtro
- **THEN** la tabla se actualiza mostrando solo encuentros de esa materia
- **THEN** el filtro se aplica via query param `materia_id`

#### Scenario: Filtrar encuentros por estado

- **WHEN** el usuario selecciona un estado (Programado, Realizado, Cancelado)
- **THEN** la tabla se actualiza mostrando solo encuentros con ese estado

#### Scenario: Sin encuentros registrados

- **WHEN** no hay encuentros en el tenant
- **THEN** se muestra un EmptyState con mensaje "No hay encuentros registrados"

#### Scenario: Error al cargar encuentros

- **WHEN** el servidor responde con error
- **THEN** se muestra un ErrorDisplay con opcion de reintentar
