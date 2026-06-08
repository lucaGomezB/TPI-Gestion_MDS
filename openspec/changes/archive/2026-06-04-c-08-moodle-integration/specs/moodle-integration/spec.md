# Moodle Integration

> **Purpose**: Define the Moodle Web Services client, sync engine, scheduled worker, and on-demand sync capabilities. This capability enables automatic ingestion of grades, enrollment, and user data from Moodle via WS API.

---

## ADDED Requirements

### Requirement: The system SHALL connect to Moodle via Web Services token authentication

The system MUST provide a Moodle Web Services client (`integrations/moodle_ws.py`) that authenticates using a per-tenant `wstoken` passed as a query parameter. The client SHALL support both Moodle REST protocol (Moodle 3.1+) and detect protocol version on initial handshake.

#### Scenario: Successful connection with valid token
- **WHEN** the client is configured with a valid `ws_url` and `ws_token` for a tenant
- **THEN** the client SHALL successfully authenticate and execute WS function calls
- **THEN** the connection SHALL use `aiohttp` with a configurable timeout (default 30s)

#### Scenario: Connection fails with invalid token
- **WHEN** the client is configured with an invalid or expired `ws_token`
- **THEN** the client SHALL raise a `MoodleAuthenticationError`
- **THEN** the error SHALL NOT be retried (retry only for 5xx/network errors)

#### Scenario: Connection times out
- **WHEN** the Moodle server does not respond within the configured timeout
- **THEN** the client SHALL raise a `MoodleConnectionError`
- **THEN** the client SHALL retry up to 2 times with exponential backoff (1s, 3s)

### Requirement: The system SHALL fetch grades from Moodle

The system SHALL implement `core_grades_get_grades` to fetch all grades for a given Moodle course. Grades SHALL be mapped to internal domain models (`Actividad`, `Calificacion`) with the numeric grade column identified by the `(Real)` suffix (RN-01).

#### Scenario: Fetch grades for a course
- **WHEN** `core_grades_get_grades` is called with a valid `courseid`
- **THEN** the response SHALL contain grade items with their numeric values
- **THEN** each grade SHALL be mapped to an internal `Calificacion` record
- **THEN** grade items SHALL be mapped to internal `Actividad` records

#### Scenario: Fetch grades returns empty
- **WHEN** `core_grades_get_grades` is called for a course with no grades
- **THEN** the response SHALL contain an empty grade list
- **THEN** the sync SHALL complete with zero grades imported (not an error)

#### Scenario: Grade item has text scale (non-numeric)
- **WHEN** a grade item uses a text scale (e.g., "Satisfactorio", "Supera lo esperado")
- **THEN** the value SHALL be stored as text scale per RN-02
- **THEN** "Satisfactorio" and "Supera lo esperado" SHALL count as approved
- **THEN** "No satisfactorio" and "No alcanzado" SHALL NOT count as approved

### Requirement: The system SHALL fetch enrolled users from Moodle

The system SHALL implement `core_enrol_get_enrolled_users` to fetch the enrollment roster for a given Moodle course. The roster SHALL be synced to the internal `AlumnoDictado` mapping.

#### Scenario: Fetch enrolled users for a course
- **WHEN** `core_enrol_get_enrolled_users` is called with a valid `courseid`
- **THEN** the response SHALL contain user profiles (id, fullname, email)
- **THEN** each user SHALL be upserted into the internal enrollment mapping
- **THEN** users no longer in the roster SHALL have their enrollment soft-deleted (RN-05)

#### Scenario: Enrolled user has no email in Moodle profile
- **WHEN** a user profile lacks an email field
- **THEN** the sync SHALL still process the user with available data
- **THEN** the sync log SHALL note the missing email as a warning

### Requirement: The system SHALL sync grade items (activity catalog)

The system SHALL implement `gradereport_user_get_grade_items` to obtain the catalog of grade items (activities) for a given Moodle course.

#### Scenario: Fetch grade items for a course
- **WHEN** `gradereport_user_get_grade_items` is called with a valid `courseid`
- **THEN** the response SHALL contain all grade items with their names and scale types
- **THEN** each grade item SHALL map to an internal `Actividad` record

### Requirement: The system SHALL provide on-demand sync via API

The system SHALL expose `POST /api/v1/materias/{dictado_id}/sync-moodle` to trigger an immediate sync for a specific dictado. The endpoint SHALL authenticate the user and verify the `calificaciones:importar` permission.

#### Scenario: On-demand sync triggers successfully
- **WHEN** an authenticated user with `calificaciones:importar` calls `POST /api/v1/materias/{dictado_id}/sync-moodle`
- **THEN** the system SHALL execute the full sync pipeline for that dictado
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `status`, `activities_synced`, `students_synced`, `grade_items_synced`, `errors`

#### Scenario: On-demand sync for non-existent dictado
- **WHEN** `dictado_id` does not exist
- **THEN** the response SHALL have status `404`

#### Scenario: On-demand sync without permission
- **WHEN** a user without `calificaciones:importar` calls the endpoint
- **THEN** the response SHALL have status `403`

#### Scenario: On-demand sync when Moodle WS is disabled for tenant
- **WHEN** the tenant has `config_moodle.ws_enabled = false`
- **THEN** the response SHALL have status `400`
- **THEN** the response SHALL contain `detail: "Moodle Web Services is not enabled for this tenant"`

#### Scenario: On-demand sync already running for same dictado
- **WHEN** a sync is already in progress for the same dictado (status `running` in sync_log)
- **THEN** the response SHALL have status `409`
- **THEN** the response SHALL contain `detail: "A sync is already in progress for this dictado"`

#### Scenario: Moodle connection error during on-demand sync
- **WHEN** the Moodle server is unreachable during sync
- **THEN** the response SHALL have status `502`
- **THEN** the sync_log entry SHALL record the error

### Requirement: The system SHALL provide scheduled nocturnal sync

The system SHALL run an automatic sync for all active dictados with a `moodle_course_id` at the configured hour (default 03:00 AM). The worker SHALL run as an async background task.

#### Scenario: Scheduled sync runs for all tenants
- **WHEN** the scheduled time is reached
- **THEN** the worker SHALL iterate over all tenants with `ws_enabled=true`
- **THEN** for each tenant, it SHALL iterate over all dictados with `moodle_course_id IS NOT NULL`
- **THEN** each dictado SHALL be synced individually
- **THEN** each sync result SHALL be recorded in `sync_log`

#### Scenario: Scheduled sync continues after per-dictado failure
- **WHEN** one dictado sync fails (Moodle timeout, invalid courseid)
- **THEN** the worker SHALL log the error and continue with the next dictado
- **THEN** subsequent dictados SHALL NOT be affected by the failure

### Requirement: The system SHALL store per-tenant Moodle configuration encrypted

The system SHALL store `MOODLE_WS_URL` and `MOODLE_WS_TOKEN` per tenant in a `config_moodle` JSONB column on the `tenants` table. Both fields SHALL be encrypted with AES-256 using the system `ENCRYPTION_KEY`.

#### Scenario: Store Moodle configuration
- **WHEN** an ADMIN user sets Moodle configuration for a tenant
- **THEN** `ws_url` and `ws_token` SHALL be encrypted before storage
- **THEN** `ws_enabled` SHALL default to `true`
- **THEN** the configuration SHALL be scoped to that tenant only

#### Scenario: Read Moodle configuration
- **WHEN** the sync engine reads the tenant's Moodle configuration
- **THEN** `ws_url` and `ws_token` SHALL be decrypted in memory
- **THEN** the decrypted values SHALL NOT be logged or exposed in API responses

#### Scenario: Tenant without Moodle configuration
- **WHEN** a tenant has `config_moodle` as NULL or empty
- **THEN** the sync engine SHALL skip that tenant (no error, logged as info)

### Requirement: The system SHALL maintain a sync log for traceability

The system SHALL create a `sync_log` table to record every sync execution (nocturnal, on-demand, and manual import). Each entry SHALL record the tenant, dictado, sync type, status, timing, and error details.

#### Scenario: Sync log entry created after successful sync
- **WHEN** a sync completes successfully
- **THEN** a `sync_log` entry SHALL be created with `status=completed`
- **THEN** the entry SHALL include `started_at`, `finished_at`, and `details` (steps executed, records affected)

#### Scenario: Sync log entry created after failed sync
- **WHEN** a sync fails with an error
- **THEN** a `sync_log` entry SHALL be created with `status=failed`
- **THEN** the entry SHALL include `error_message` and `details` (which step failed)

#### Scenario: Sync log entry for partial success
- **WHEN** some steps succeed and others fail during sync
- **THEN** a `sync_log` entry SHALL be created with `status=partial`
- **THEN** the entry SHALL include details of both successful and failed steps

### Requirement: The system SHALL provide tenant boundary isolation in sync operations

All sync operations SHALL be scoped to the authenticated user's tenant. The sync engine SHALL only process dictados belonging to the tenant resolved from the JWT.

#### Scenario: User syncs only their tenant's dictados
- **WHEN** a user triggers on-demand sync for a dictado
- **THEN** the system SHALL verify the dictado belongs to the user's tenant
- **THEN** if tenant mismatch, return `404` (dictado not found from user's perspective)
- **THEN** tenant A's sync SHALL never access tenant B's Moodle configuration

#### Scenario: Nocturnal sync processes each tenant independently
- **WHEN** the nocturnal sync worker runs
- **THEN** each tenant SHALL be processed with its own Moodle configuration
- **THEN** tenant A's sync failures SHALL NOT affect tenant B's sync
