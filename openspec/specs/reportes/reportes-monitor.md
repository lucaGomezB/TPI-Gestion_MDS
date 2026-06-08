# Reportes — Monitor de Actividades

> **Purpose**: Define the activity monitoring endpoints (F2.7 — general monitor for COORDINADOR/ADMIN; F2.8/F2.9 — seguimiento per subject for TUTOR, PROFESOR, COORDINADOR, ADMIN).

---

## ADDED Requirements

### Requirement: The system SHALL provide GET /api/admin/monitor/actividades for cross-tenant activity monitoring

The system MUST provide an endpoint for COORDINADOR and ADMIN roles to view a cross-subject, tenant-wide activity status of all students. The endpoint SHALL return consolidated data with filters.

#### Scenario: Monitor geral with full data
- **WHEN** a COORDINADOR calls GET /api/admin/monitor/actividades with no filters
- **THEN** the response SHALL include all students in the tenant with their activity status across all subjects
- **THEN** each item SHALL include `entrada_padron_id`, `nombre`, `apellidos`, `comision`, `regional`, `materia_nombre`, `total_actividades`, `total_aprobadas`, `total_pendientes`, `ultima_actividad`
- **THEN** the response SHALL include top-level metrics: `total_alumnos`, `total_materias`, `total_actividades`, `total_aprobadas`

#### Scenario: Monitor geral filtered by materia
- **WHEN** GET /api/admin/monitor/actividades?materia_id=M1
- **THEN** the response SHALL only include students from materia_id=M1

#### Scenario: Monitor geral filtered by regional
- **WHEN** GET /api/admin/monitor/actividades?regional=Centro
- **THEN** the response SHALL only include students whose EntradaPadron.regional == "Centro"

#### Scenario: Monitor geral filtered by comision
- **WHEN** GET /api/admin/monitor/actividades?comision=A
- **THEN** the response SHALL only include students whose EntradaPadron.comision == "A"

#### Scenario: Monitor geral filtered by estado actividad
- **WHEN** GET /api/admin/monitor/actividades?estado_actividad=pendiente
- **THEN** the response SHALL only include students with at least one activity still pending (no Calificacion record for any actividad in the materia)
- **WHEN** GET /api/admin/monitor/actividades?estado_actividad=completo
- **THEN** the response SHALL only include students with Calificacion records for all detected actividades in the materia

#### Scenario: Monitor geral filtered by busqueda
- **WHEN** GET /api/admin/monitor/actividades?busqueda=garcia
- **THEN** the response SHALL only include students whose nombre or apellidos contain "garcia" (case-insensitive)

#### Scenario: Monitor geral filtered by date range
- **WHEN** GET /api/admin/monitor/actividades?fecha_desde=2026-03-01&fecha_hasta=2026-06-01
- **THEN** only Calificacion records within the date range SHALL be considered for activity counts

#### Scenario: Monitor geral with no data
- **WHEN** no students or Calificacion records exist for the tenant
- **THEN** the response SHALL return `200` with `{ "items": [], "total": 0, "total_alumnos": 0, "total_materias": 0, "total_actividades": 0, "total_aprobadas": 0 }`

#### Scenario: Permission denied for PROFESOR
- **WHEN** a PROFESOR (not COORDINADOR or ADMIN) calls GET /api/admin/monitor/actividades
- **THEN** the endpoint SHALL return `403`

#### Scenario: Permission denied for TUTOR
- **WHEN** a TUTOR calls the monitor general endpoint
- **THEN** the endpoint SHALL return `403`

### Requirement: The system SHALL provide GET /api/materias/{id}/seguimiento for per-subject student monitoring

The system MUST provide an endpoint for per-subject student activity monitoring. The endpoint SHALL behave differently based on the user's role (F2.8 for TUTOR/PROFESOR, F2.9 for COORDINADOR/ADMIN).

For TUTOR/PROFESOR: scope limited to students in their assigned comisiones, with filters: alumno, comision, regional, actividad, minimo_actividades_cumplidas.
For COORDINADOR/ADMIN: all students in the materia, with additional date range filters.

#### Scenario: Seguimiento for PROFESOR with full data
- **WHEN** a PROFESOR assigned to `materia_id=M1` calls GET /api/materias/M1/seguimiento
- **THEN** the response SHALL include all students with grades imported by the PROFESOR
- **THEN** each item SHALL include `entrada_padron_id`, `nombre`, `apellidos`, `comision`, `actividades` (list with `actividad_nombre`, `nota_numerica`, `nota_textual`, `aprobado`), `total_actividades`, `total_aprobadas`, `porcentaje_cumplimiento`
- **THEN** the response SHALL include metrics: `total_alumnos`, `promedio_cumplimiento`

#### Scenario: Seguimiento for PROFESOR filtered by actividad
- **WHEN** GET /api/materias/M1/seguimiento?actividad=TP+1
- **THEN** the response SHALL only include status for activity "TP 1"

#### Scenario: Seguimiento for PROFESOR filtered by minimo_actividades_cumplidas
- **WHEN** GET /api/materias/M1/seguimiento?minimo_actividades_cumplidas=3
- **THEN** the response SHALL only include students with at least 3 approved activities

#### Scenario: Seguimiento for PROFESOR filtered by busqueda
- **WHEN** GET /api/materias/M1/seguimiento?busqueda=perez
- **THEN** the response SHALL only include students matching "perez" (case-insensitive)

#### Scenario: Seguimiento for COORDINADOR includes all data
- **WHEN** a COORDINADOR calls GET /api/materias/M1/seguimiento
- **THEN** the response SHALL include ALL students in the materia, not only one PROFESOR's data
- **THEN** the COORDINADOR SHALL be able to use `fecha_desde` and `fecha_hasta` query parameters (F2.9)

#### Scenario: Seguimiento for COORDINADOR with date range
- **WHEN** a COORDINADOR calls GET /api/materias/M1/seguimiento?fecha_desde=2026-03-01&fecha_hasta=2026-06-01
- **THEN** only Calificacion records within the date range SHALL be considered

#### Scenario: Seguimiento with no data
- **WHEN** no Calificacion records exist for `materia_id=M1`
- **THEN** the response SHALL return `200` with `{ "items": [], "total": 0, "total_alumnos": 0, "promedio_cumplimiento": 0.0 }`

#### Scenario: Seguimiento filtered by regional
- **WHEN** GET /api/materias/M1/seguimiento?regional=Centro
- **THEN** the response SHALL only include students whose EntradaPadron.regional == "Centro"

#### Scenario: Seguimiento filtered by comision
- **WHEN** GET /api/materias/M1/seguimiento?comision=A
- **THEN** the response SHALL only include students whose EntradaPadron.comision == "A"

#### Scenario: Permission denied for non-assigned PROFESOR
- **WHEN** a PROFESOR not assigned to `materia_id=M1` calls GET /api/materias/M1/seguimiento
- **THEN** the endpoint SHALL return `403`

#### Scenario: TUTOR sees only assigned comisiones
- **WHEN** a TUTOR assigned to comision "A" in `materia_id=M1` calls GET /api/materias/M1/seguimiento
- **THEN** the response SHALL only include students from comision "A"
- **THEN** students from other comisiones SHALL NOT appear

### Requirement: New permissions for reportes:monitor_general and reportes:seguimiento

The system SHALL add `reportes:monitor_general` for COORDINADOR and ADMIN, and `reportes:seguimiento` for TUTOR, PROFESOR, COORDINADOR, and ADMIN.

#### Scenario: COORDINADOR has reportes:monitor_general
- **WHEN** checking permissions for COORDINADOR role
- **THEN** `reportes:monitor_general` SHALL be in the COORDINADOR permissions set

#### Scenario: ADMIN has reportes:monitor_general
- **WHEN** checking permissions for ADMIN role
- **THEN** `reportes:monitor_general` SHALL be in the ADMIN permissions set

#### Scenario: TUTOR has reportes:seguimiento
- **WHEN** checking permissions for TUTOR role
- **THEN** `reportes:seguimiento` SHALL be in the TUTOR permissions set

#### Scenario: PROFESOR has reportes:seguimiento
- **WHEN** checking permissions for PROFESOR role
- **THEN** `reportes:seguimiento` SHALL be in the PROFESOR permissions set

#### Scenario: COORDINADOR has reportes:seguimiento
- **WHEN** checking permissions for COORDINADOR role
- **THEN** `reportes:seguimiento` SHALL be in the COORDINADOR permissions set

#### Scenario: ADMIN has reportes:seguimiento
- **WHEN** checking permissions for ADMIN role
- **THEN** `reportes:seguimiento` SHALL be in the ADMIN permissions set

### Requirement: The system SHALL register audit log entries for monitor queries

#### Scenario: Audit log on monitor general query
- **WHEN** a COORDINADOR calls GET /api/admin/monitor/actividades
- **THEN** an AuditLog record SHALL be created with `accion='MONITOR_GENERAL_CONSULTAR'`

#### Scenario: Audit log on seguimiento query
- **WHEN** a PROFESOR calls GET /api/materias/M1/seguimiento
- **THEN** an AuditLog record SHALL be created with `accion='SEGUIMIENTO_CONSULTAR'`
- **THEN** the audit record SHALL include `actor_id`, `materia_id`
