# Manual Import

> **Purpose**: Define the fallback manual import capability for tenants without Moodle Web Services access, or for historical data loads. Supports importing grades and enrollment rosters from `.xlsx` and `.csv` files exported from Moodle.

---

## ADDED Requirements

### Requirement: The system SHALL accept grade import via .xlsx/.csv files

The system SHALL accept file uploads in `.xlsx` (Excel) and `.csv` (comma/tab/semicolon separated) formats for grade import. The parser SHALL detect the header row and identify grade columns matching the `(Real)` suffix pattern (RN-01).

#### Scenario: Upload valid xlsx file for preview
- **WHEN** a user with `calificaciones:importar` uploads a valid `.xlsx` grade file to `POST /api/v1/materias/{dictado_id}/import/preview`
- **THEN** the system SHALL parse the file and detect columns ending in `(Real)` as numeric grade columns
- **THEN** the response SHALL contain a `PreviewResult` with:
  - `activities`: list of detected activities with name and scale type
  - `students_count`: number of students detected
  - `sample_students`: first 5 student names
  - `warnings`: any parsing issues encountered
- **THEN** the response SHALL have status `200`

#### Scenario: Upload file with no recognizable grade columns
- **WHEN** a file is uploaded but no columns match the `(Real)` suffix pattern
- **THEN** the response SHALL have status `400`
- **THEN** the response SHALL contain `detail` describing which columns were found and the expected pattern

#### Scenario: Upload malformed file
- **WHEN** a file cannot be parsed (corrupt xlsx, wrong format)
- **THEN** the response SHALL have status `400`
- **THEN** the response SHALL contain a descriptive error message

#### Scenario: Upload unsupported format
- **WHEN** a file with an extension other than `.xlsx` or `.csv` is uploaded
- **THEN** the response SHALL have status `400`
- **THEN** the response SHALL indicate the supported formats

### Requirement: The system SHALL provide preview before committing import

The system SHALL generate a preview of the parsed data without persisting it. The preview SHALL return detected activities, students, and any warnings to the user for review before confirmation.

#### Scenario: Preview shows activities from grade columns
- **WHEN** a file with columns `[Activity 1 (Real), Activity 2 (Real), Other Column]` is uploaded
- **THEN** `Activity 1` and `Activity 2` SHALL appear in the `activities` list
- **THEN** `Other Column` SHALL be ignored (logged as info)
- **THEN** each activity SHALL include its `scale_type` (numeric or textual)

#### Scenario: Preview shows students with enrollment data
- **WHEN** a file contains student rows with name/email/DNI columns
- **THEN** the preview SHALL return the count of students detected
- **THEN** the preview SHALL return the first 5 student names as a sample

#### Scenario: Preview with textual scale values
- **WHEN** a grade column uses textual values like "Satisfactorio", "No satisfactorio"
- **THEN** the preview SHALL identify the column as `scale_type=textual`
- **THEN** the scale config values SHALL be cross-referenced against the tenant's catalog (RN-02)

### Requirement: The system SHALL confirm and persist grades from preview

The system SHALL accept a confirmation request that specifies which detected activities to include, then persist the selected grades and update the enrollment roster.

#### Scenario: Confirm import with selected activities
- **WHEN** a user confirms import via `POST /api/v1/materias/{dictado_id}/import/confirm` with a list of `activity_ids` to include
- **THEN** the system SHALL persist the selected activities and their grades
- **THEN** the enrollment roster SHALL be upserted (RN-05)
- **THEN** the response SHALL have status `200`
- **THEN** the response SHALL contain `activities_imported` and `grades_imported` counts

#### Scenario: Confirm import without selecting activities
- **WHEN** the `activity_ids` list is empty
- **THEN** the response SHALL have status `400`
- **THEN** the response SHALL indicate that at least one activity must be selected

#### Scenario: Confirm import with expired preview session
- **WHEN** the preview session has expired (TTL exceeded) or is invalid
- **THEN** the response SHALL have status `400`
- **THEN** the user SHALL be asked to re-upload the file

### Requirement: The system SHALL import enrollment rosters from files

The system SHALL support importing student enrollment rosters from `.xlsx`/`.csv` files, with upsert destructive behavior as defined in RN-05: the new roster replaces the previous one for that dictado.

#### Scenario: Import enrollment roster replaces previous
- **WHEN** a new enrollment roster file is imported for a dictado
- **THEN** all students from the new roster SHALL be enrolled
- **THEN** students present in the old roster but absent from the new one SHALL have their enrollment soft-deleted
- **THEN** the operation SHALL be atomic (all-or-nothing per dictado)

### Requirement: The system SHALL enforce permission scoping on import operations

Import operations SHALL require the `calificaciones:importar` permission. PROFESOR users SHALL only import to dictados where they have an active teaching assignment. COORDINADOR users SHALL import to any dictado within their tenant.

#### Scenario: PROFESOR imports to own dictado
- **WHEN** a PROFESOR with active assignment to a dictado uploads to that dictado
- **THEN** the import SHALL proceed

#### Scenario: PROFESOR imports to non-assigned dictado
- **WHEN** a PROFESOR without an active assignment to a dictado attempts to import
- **THEN** the response SHALL have status `403`

#### Scenario: COORDINADOR imports to any tenant dictado
- **WHEN** a COORDINADOR uploads to any dictado in their tenant
- **THEN** the import SHALL proceed

### Requirement: The system SHALL record manual imports in the sync log

Every manual import SHALL be recorded in the `sync_log` table with `sync_type=manual_import`, including the number of activities and grades imported, and any errors encountered.

#### Scenario: Manual import creates sync log entry
- **WHEN** a manual import completes
- **THEN** a `sync_log` entry SHALL be created with `sync_type=manual_import`
- **THEN** the entry SHALL include `details.activities_imported` and `details.grades_imported`
- **THEN** the entry SHALL reference the `dictado_id`
