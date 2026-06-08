# Atrasados y Ranking

> **Purpose**: Define the endpoints and business logic for detecting at-risk students (atrasados), ranking by approved activities, and consolidated subject-level reports. All endpoints are read-only and operate on existing Calificacion and EntradaPadron data.

---

## ADDED Requirements

### Requirement: The system SHALL provide GET /api/materias/{materia_id}/atrasados to list at-risk students

The system MUST provide an endpoint to list students who are "atrasados" (at-risk) according to RN-06. An atrasado student is one who either has no grades recorded (faltante) OR has numeric grades below the configured threshold.

The endpoint SHALL respect RN-08: PROFESOR only sees students whose grades they imported. COORDINADOR/ADMIN sees all students in the materia.

#### Scenario: List atrasados with no data
- **WHEN** a PROFESOR assigned to `materia_id=M1` calls GET /api/materias/M1/atrasados
- **THEN** the response SHALL return `200` with `{ "items": [], "total": 0, "metrics": { "total_alumnos": 0, "total_atrasados": 0 } }`

#### Scenario: List atrasados with active padron but no calificaciones
- **WHEN** a PROFESOR has an active padron (5 students) for `materia_id=M1` but has not imported any grades yet
- **THEN** all 5 students SHALL appear as atrasados (faltantes)
- **THEN** each item SHALL include `nombre`, `apellidos`, `email`, `comision`, `razon: "faltante"`, `total_actividades: 0`

#### Scenario: List atrasados with grades below threshold
- **WHEN** a PROFESOR has imported grades where `alumno_A` scored 45/100 (umbral=60)
- **THEN** `alumno_A` SHALL appear as atrasado with `razon: "nota_baja"`, `nota_minima: 45.0`, `umbral: 60`

#### Scenario: List atrasados with mixed conditions
- **WHEN** a PROFESOR has 10 students in padron, 2 with no grades, 1 with nota_baja, and 7 with all notas >= umbral
- **THEN** the response SHALL include 3 atrasados (2 faltantes + 1 nota_baja)
- **THEN** `metrics.total_atrasados` SHALL be 3

#### Scenario: Filter by comision
- **WHEN** GET /api/materias/M1/atrasados?comision=A
- **THEN** the response SHALL only include students whose EntradaPadron.comision == "A"

#### Scenario: Filter by busqueda (text search)
- **WHEN** GET /api/materias/M1/atrasados?busqueda=garcia
- **THEN** the response SHALL only include students whose nombre or apellidos contain "garcia" (case-insensitive)

#### Scenario: Filter by fecha_desde / fecha_hasta
- **WHEN** GET /api/materias/M1/atrasados?fecha_desde=2026-01-01&fecha_hasta=2026-06-01
- **THEN** the system SHALL only consider Calificaciones with `importado_at` within the date range when determining atrasados

#### Scenario: COORDINADOR sees all data
- **WHEN** a COORDINADOR calls GET /api/materias/M1/atrasados
- **THEN** the response SHALL include students from ALL PROFESOR imports, not only one user's data

#### Scenario: Permission denied for non-assigned PROFESOR
- **WHEN** a PROFESOR not assigned to `materia_id=M1` attempts to list atrasados
- **THEN** the endpoint SHALL return `403`

### Requirement: The system SHALL provide GET /api/materias/{materia_id}/ranking to list ranking by approved activities

The system MUST provide an endpoint to rank students by the number of approved activities, following RN-09. Only students with at least one approved activity SHALL appear in the ranking.

#### Scenario: Ranking with approved activities
- **WHEN** a PROFESOR has grades with: `alumno_A` has 3 approved + 1 not approved, `alumno_B` has 2 approved, `alumno_C` has 0 approved
- **THEN** the ranking SHALL be: 1st: `alumno_A` (3 aprobadas), 2nd: `alumno_B` (2 aprobadas)
- **THEN** `alumno_C` SHALL NOT appear (0 approved, RN-09)
- **THEN** each item SHALL include `nombre`, `apellidos`, `comision`, `total_aprobadas`, `total_actividades`, `porcentaje_aprobacion`

#### Scenario: Ranking with no data
- **WHEN** no Calificaciones exist for `materia_id=M1`
- **THEN** the response SHALL return `200` with `{ "items": [], "total": 0 }`

#### Scenario: Ranking with all students at 0 approved
- **WHEN** all students have `aprobado=false` for all activities
- **THEN** the response SHALL return `200` with `{ "items": [], "total": 0 }` (empty because RN-09 excludes 0 approved)

#### Scenario: Ranking filtered by comision
- **WHEN** GET /api/materias/M1/ranking?comision=A
- **THEN** the ranking SHALL only include students from comision "A"

#### Scenario: Ranking filtered by busqueda
- **WHEN** GET /api/materias/M1/ranking?busqueda=perez
- **THEN** the ranking SHALL only include students matching "perez" (case-insensitive)

#### Scenario: Ranking respects scope (PROFESOR only sees own data)
- **WHEN** a PROFESOR calls GET /api/materias/M1/ranking
- **THEN** the ranking SHALL only consider Calificaciones where `cargado_por` matches the PROFESOR's user ID
- **THEN** students with grades imported by other PROFESORes SHALL NOT appear in this ranking

### Requirement: The system SHALL provide GET /api/materias/{materia_id}/reportes to get consolidated metrics

The system MUST provide an endpoint that returns key metrics for a subject, giving the user a quick overview of the academic state.

#### Scenario: Reportes with full data
- **WHEN** a PROFESOR calls GET /api/materias/M1/reportes with 30 padron entries, 25 have calificaciones, 8 atrasados, all have grades
- **THEN** the response SHALL include:
  - `total_alumnos`: 30
  - `alumnos_con_calificaciones`: 25
  - `total_atrasados`: 8
  - `total_aprobadas`: 45 (sum of all aprobado=true across all activities)
  - `total_calificaciones`: 120 (total grade records)
  - `actividades`: list of distinct activity names with counts
  - `porcentaje_atrasados`: 26.67 (8/30 * 100)

#### Scenario: Reportes with no padron
- **WHEN** no active padron exists for `materia_id=M1`
- **THEN** the response SHALL return `200` with `{ "total_alumnos": 0, "alumnos_con_calificaciones": 0, "total_atrasados": 0, "total_aprobadas": 0, "total_calificaciones": 0, "actividades": [], "porcentaje_atrasados": 0.0 }`

#### Scenario: Reportes respects scope (PROFESOR)
- **WHEN** a PROFESOR calls GET /api/materias/M1/reportes
- **THEN** the metrics SHALL only reflect Calificaciones where `cargado_por` matches the PROFESOR's user ID

### Requirement: The system SHALL support export to CSV for atrasados and ranking

Both the atrasados and ranking endpoints SHALL support an `?exportar=csv` query parameter that returns a downloadable CSV file instead of JSON.

#### Scenario: Export atrasados to CSV
- **WHEN** GET /api/materias/M1/atrasados?exportar=csv
- **THEN** the response SHALL have `Content-Type: text/csv`
- **THEN** the response SHALL have `Content-Disposition: attachment; filename="atrasados-M1.csv"`
- **THEN** the CSV SHALL include headers: nombre, apellidos, email, comision, razon, nota_minima, umbral, total_actividades
- **THEN** the CSV SHALL include the same data rows as the JSON response

#### Scenario: Export ranking to CSV
- **WHEN** GET /api/materias/M1/ranking?exportar=csv
- **THEN** the response SHALL have `Content-Type: text/csv`
- **THEN** the CSV SHALL include headers: nombre, apellidos, comision, total_aprobadas, total_actividades, porcentaje_aprobacion

#### Scenario: Export with no data
- **WHEN** GET /api/materias/M1/atrasados?exportar=csv and no atrasados exist
- **THEN** the response SHALL return CSV with only headers and no data rows
- **THEN** `Content-Type` SHALL be `text/csv`
- **THEN** status code SHALL be `200`

### Requirement: The system SHALL register audit log entries for report queries

For compliance, queries to the atrasados, ranking, and reportes endpoints SHALL generate audit log entries.

#### Scenario: Audit log on atrasados query
- **WHEN** a PROFESOR calls GET /api/materias/M1/atrasados
- **THEN** an AuditLog record SHALL be created with `accion='ATRASADOS_CONSULTAR'`
- **THEN** the audit record SHALL include `actor_id`, `materia_id`

#### Scenario: Audit log on ranking query
- **WHEN** a PROFESOR calls GET /api/materias/M1/ranking
- **THEN** an AuditLog record SHALL be created with `accion='RANKING_CONSULTAR'`

### Requirement: New permissions SHALL be added for reportes and export

The system SHALL add two new permissions to the RBAC matrix for this change.

#### Scenario: PROFESOR has reportes:ver permission
- **WHEN** checking permissions for PROFESOR role
- **THEN** `reportes:ver` SHALL be in the PROFESOR permissions set

#### Scenario: COORDINADOR has reportes:ver permission
- **WHEN** checking permissions for COORDINADOR role
- **THEN** `reportes:ver` SHALL be in the COORDINADOR permissions set

#### Scenario: ADMIN has reportes:ver permission
- **WHEN** checking permissions for ADMIN role
- **THEN** `reportes:ver` SHALL be in the ADMIN permissions set

#### Scenario: PROFESOR has calificaciones:exportar permission
- **WHEN** checking permissions for PROFESOR role
- **THEN** `calificaciones:exportar` SHALL be in the PROFESOR permissions set

#### Scenario: COORDINADOR has calificaciones:exportar permission
- **WHEN** checking permissions for COORDINADOR role
- **THEN** `calificaciones:exportar` SHALL be in the COORDINADOR permissions set

#### Scenario: ADMIN has calificaciones:exportar permission
- **WHEN** checking permissions for ADMIN role
- **THEN** `calificaciones:exportar` SHALL be in the ADMIN permissions set

### Requirement: The system SHALL add new audit action codes

The system SHALL add action codes for atrasados and ranking queries to the audit catalog.

#### Scenario: Action codes exist
- **WHEN** referencing audit action codes
- **THEN** `ATRASADOS_CONSULTAR` SHALL be a valid action code
- **THEN** `RANKING_CONSULTAR` SHALL be a valid action code
