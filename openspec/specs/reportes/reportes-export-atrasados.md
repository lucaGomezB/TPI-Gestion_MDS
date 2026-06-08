# Reportes — Export Atrasados (TP sin corregir)

> **Purpose**: Define the endpoint (F2.6) for exporting a list of practical assignments that have been submitted by students but not yet graded, following RN-07 and RN-08 (textual-scale activities only).

---

## ADDED Requirements

### Requirement: The system SHALL provide GET /api/materias/{id}/export/atrasados to export uncorrected TPs

The system MUST provide an endpoint to detect and export practical assignments that are potentially uncorrected. The detection follows RN-07 (cross-reference LMS completion data with imported grades) and RN-08 (textual activities only).

Since the dedicated LMS completion report import (F1.2) is not yet implemented, the initial implementation SHALL use available Calificacion data to detect potential uncorrected TPs: students who are enrolled in the active padron but lack a textual Calificacion record for activities where textual grades exist for other students.

The endpoint SHALL support `?exportar=csv` to return a downloadable file.

#### Scenario: Export atrasados with textual activities
- **WHEN** GET /api/materias/M1/export/atrasados where `materia_id=M1` has activities "TP 1" (textual) and "TP 2" (textual), and `alumno_A` has "Satisfactorio" in both, `alumno_B` has "Satisfactorio" in "TP 1" but no record in "TP 2"
- **THEN** the response SHALL include `alumno_B` — "TP 2" as a potentially uncorrected TP
- **THEN** `alumno_A` SHALL NOT appear (both activities graded)
- **THEN** each item SHALL include `nombre`, `apellidos`, `comision`, `actividad`, `estado: "sin_corregir"`

#### Scenario: Export atrasados with numeric activities excluded (RN-08)
- **WHEN** `materia_id=M1` has "TP 1" (textual) and "Examen" (numeric), and `alumno_C` lacks records for both
- **THEN** "Examen" SHALL NOT appear in the export (numeric, per RN-08)
- **THEN** "TP 1" SHALL appear if it has textual records for other students

#### Scenario: Export atrasados with no textual activities
- **WHEN** `materia_id=M1` has only numeric activities (no Calificacion with `nota_textual IS NOT NULL`)
- **THEN** the response SHALL return `200` with empty items and `total: 0`
- **THEN** no items SHALL appear (nothing to detect per RN-08)

#### Scenario: Export atrasados with all grades complete
- **WHEN** every student in the active padron has a Calificacion record for all textual activities in the materia
- **THEN** the response SHALL return `200` with empty items and `total: 0`

#### Scenario: Export atrasados to CSV
- **WHEN** GET /api/materias/M1/export/atrasados?exportar=csv
- **THEN** the response SHALL have `Content-Type: text/csv`
- **THEN** the CSV SHALL include headers: nombre, apellidos, comision, actividad, estado
- **THEN** the CSV SHALL include the same data rows as the JSON response

#### Scenario: Export atrasados with date range filter
- **WHEN** GET /api/materias/M1/export/atrasados?fecha_desde=2026-03-01&fecha_hasta=2026-06-01
- **THEN** only textual activities with Calificacion records within the date range SHALL be considered for detection

#### Scenario: Export atrasados with comision filter
- **WHEN** GET /api/materias/M1/export/atrasados?comision=A
- **THEN** only students from comision "A" SHALL be included

#### Scenario: Permission denied for non-assigned PROFESOR
- **WHEN** a PROFESOR not assigned to `materia_id=M1` attempts to export atrasados
- **THEN** the endpoint SHALL return `403`

### Requirement: New permissions for reportes:exportar_atrasados

The system SHALL add the `reportes:exportar_atrasados` permission for PROFESOR and COORDINADOR roles.

#### Scenario: PROFESOR has reportes:exportar_atrasados permission
- **WHEN** checking permissions for PROFESOR role
- **THEN** `reportes:exportar_atrasados` SHALL be in the PROFESOR permissions set

#### Scenario: COORDINADOR has reportes:exportar_atrasados permission
- **WHEN** checking permissions for COORDINADOR role
- **THEN** `reportes:exportar_atrasados` SHALL be in the COORDINADOR permissions set

### Requirement: The system SHALL register audit log entries for export-atrasados queries

#### Scenario: Audit log on export-atrasados query
- **WHEN** a PROFESOR calls GET /api/materias/M1/export/atrasados
- **THEN** an AuditLog record SHALL be created with `accion='EXPORT_ATRASADOS_CONSULTAR'`
- **THEN** the audit record SHALL include `actor_id`, `materia_id`
