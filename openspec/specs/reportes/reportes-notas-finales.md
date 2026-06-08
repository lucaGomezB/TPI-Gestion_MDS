# Reportes — Notas Finales

> **Purpose**: Define the final grade calculation endpoint (F2.5) that aggregates activities and computes a final grade per student, ready for export or formal recording.

---

## ADDED Requirements

### Requirement: The system SHALL provide GET /api/materias/{id}/notas-finales to list final grades per student

The system MUST provide an endpoint to calculate and return final grades for all students in a subject. The endpoint aggregates all Calificacion records, computes the average of numeric grades, and determines the final approval status for each student.

The endpoint SHALL respect scope: PROFESOR only sees grades they imported. COORDINADOR/ADMIN sees all data for the materia.

The endpoint SHALL support `?exportar=csv` query parameter to return a downloadable CSV file.

#### Scenario: Notas finales with numeric grades only
- **WHEN** a PROFESOR calls GET /api/materias/M1/notas-finales where `alumno_A` has grades [80, 90, 70] (avg=80.00) and `alumno_B` has grades [50, 60, 55] (avg=55.00)
- **THEN** `alumno_A` SHALL have `nota_final: 80.00` and `estado: "aprobado"`
- **THEN** `alumno_B` SHALL have `nota_final: 55.00` and `estado: "reprobado"`
- **THEN** the response SHALL include `total_alumnos: 2`, `promedio_general: 67.50`

#### Scenario: Notas finales with mixed grade types
- **WHEN** `alumno_C` has numeric grades [75, 85] and textual grade "Satisfactorio" (aprobado=true)
- **THEN** the numeric grades SHALL be averaged (80.00) for `nota_final`
- **THEN** textual grades SHALL NOT affect the numeric average but SHALL be counted toward `total_actividades`
- **THEN** `estado` SHALL be "aprobado" if the numeric average >= umbral_pct

#### Scenario: Notas finales with no data
- **WHEN** no Calificacion records exist for `materia_id=M1`
- **THEN** the response SHALL return `200` with `{ "items": [], "total": 0, "total_alumnos": 0, "promedio_general": 0.0 }`

#### Scenario: Notas finales respects PROFESOR scope
- **WHEN** a PROFESOR calls GET /api/materias/M1/notas-finales and another PROFESOR also has grades for the same materia
- **THEN** the response SHALL only include students with grades imported by the requesting PROFESOR
- **THEN** students with grades only from other PROFESORes SHALL NOT appear

#### Scenario: Notas finales with student info
- **WHEN** the endpoint returns data
- **THEN** each item SHALL include `entrada_padron_id`, `nombre`, `apellidos`, `comision`, `total_actividades`, `nota_final`, `estado`

#### Scenario: Export notas finales to CSV
- **WHEN** GET /api/materias/M1/notas-finales?exportar=csv
- **THEN** the response SHALL have `Content-Type: text/csv`
- **THEN** the CSV SHALL include headers: nombre, apellidos, comision, total_actividades, nota_final, estado
- **THEN** the CSV SHALL include the same data rows as the JSON response

#### Scenario: Permission denied for non-assigned PROFESOR
- **WHEN** a PROFESOR not assigned to `materia_id=M1` attempts to view notas-finales
- **THEN** the endpoint SHALL return `403`

### Requirement: New permissions for reportes:notas_finales

The system SHALL add the `reportes:notas_finales` permission for PROFESOR role.

#### Scenario: PROFESOR has reportes:notas_finales permission
- **WHEN** checking permissions for PROFESOR role
- **THEN** `reportes:notas_finales` SHALL be in the PROFESOR permissions set

### Requirement: The system SHALL register audit log entries for notas-finales queries

#### Scenario: Audit log on notas-finales query
- **WHEN** a PROFESOR calls GET /api/materias/M1/notas-finales
- **THEN** an AuditLog record SHALL be created with `accion='NOTAS_FINALES_CONSULTAR'`
- **THEN** the audit record SHALL include `actor_id`, `materia_id`
