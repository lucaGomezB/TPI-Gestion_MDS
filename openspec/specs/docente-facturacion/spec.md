## ADDED Requirements

### Requirement: The system SHALL provide the Factura model for teacher invoices

The system MUST provide a `Factura` model (E20) representing an invoice submitted by a facturante teacher for a given period.

| Attribute | Type | Constraints |
|-----------|------|-------------|
| `id` | UUID (string) | PK, auto-generated |
| `tenant_id` | UUID (string) | FK -> tenants.id, NOT NULL |
| `usuario_id` | UUID (string) | FK -> usuarios.id, NOT NULL, user must have facturador=true |
| `periodo` | String(7) | NOT NULL, format YYYY-MM |
| `detalle` | Text | NOT NULL, free-text description of service billed |
| `referencia_archivo` | String(255) | NOT NULL, opaque reference to PDF in storage service |
| `tamano_kb` | Numeric(10,2) | NOT NULL, file size in KB |
| `estado` | String(10) | NOT NULL, default 'Pendiente', values: Pendiente, Abonada |
| `cargada_at` | DateTime(tz) | server default now() |
| `abonada_at` | DateTime(tz) | nullable, set when estado transitions to Abonada |

Indexes:
- `ix_facturas_periodo` on (tenant_id, periodo)
- `ix_facturas_usuario_id` on (usuario_id)
- `ix_facturas_estado` on (tenant_id, estado)

#### Scenario: Create factura with all required fields
- **WHEN** the system creates a Factura for a teacher in a period
- **THEN** the model SHALL store tenant_id, usuario_id, periodo, detalle, referencia_archivo, tamano_kb
- **THEN** estado SHALL default to 'Pendiente'
- **THEN** cargada_at SHALL be set to current timestamp
- **THEN** abonada_at SHALL be null

#### Scenario: Factura rejects usuario without facturador flag
- **WHEN** the system attempts to create a Factura for a Usuario with facturador=false
- **THEN** the system SHALL return 400 with error indicating user is not a facturante teacher

#### Scenario: Factura estado transitions from Pendiente to Abonada
- **WHEN** a Factura with estado='Pendiente' is marked as abonada
- **THEN** estado SHALL become 'Abonada'
- **THEN** abonada_at SHALL be set to current timestamp

#### Scenario: Factura already Abonada cannot be modified
- **WHEN** attempting to mark an Abonada factura as abonada again
- **THEN** the system SHALL return 409 Conflict

### Requirement: The system SHALL allow facturante teachers to upload invoices

The system MUST provide POST /api/docentes/facturas for authenticated teachers with facturador=true to upload a PDF invoice (RF-61). The request SHALL accept multipart/form-data with fields: archivo (PDF), periodo (YYYY-MM), detalle (text).

Response: 201 with the created Factura object.

#### Scenario: Upload invoice successfully
- **WHEN** a teacher with facturador=true sends POST /api/docentes/facturas with archivo=valid.pdf, periodo=2026-06, detalle="Honorarios junio 2026"
- **THEN** the system SHALL return 201 with the created Factura
- **THEN** referencia_archivo SHALL contain the storage reference
- **THEN** tamano_kb SHALL reflect the uploaded file size
- **THEN** estado SHALL be 'Pendiente'

#### Scenario: Upload rejected for non-facturante teacher
- **WHEN** a teacher with facturador=false sends POST /api/docentes/facturas
- **THEN** the system SHALL return 403 Forbidden

#### Scenario: Upload with invalid file type
- **WHEN** a facturante teacher sends POST /api/docentes/facturas with archivo=document.docx (not PDF)
- **THEN** the system SHALL return 400 with error indicating only PDF files accepted

#### Scenario: Upload without authentication
- **WHEN** an unauthenticated request is sent to POST /api/docentes/facturas
- **THEN** the system SHALL return 401

### Requirement: The system SHALL expose GET /api/docentes/facturas for teacher invoice history

The system MUST provide an endpoint returning all invoices submitted by the authenticated teacher, ordered by cargada_at descending. Supports pagination.

#### Scenario: Get own invoice history
- **WHEN** a facturante teacher sends GET /api/docentes/facturas
- **THEN** the system SHALL return 200 with paginated list of their own Facturas ordered by cargada_at desc
- **THEN** items SHALL only include facturas where usuario_id matches the authenticated user

#### Scenario: Non-facturante teacher gets empty history
- **WHEN** a teacher with facturador=false sends GET /api/docentes/facturas
- **THEN** the system SHALL return 200 with empty items array

#### Scenario: Filter own history by periodo
- **WHEN** GET /api/docentes/facturas?periodo=2026-06
- **THEN** the system SHALL filter to only show facturas for that period belonging to the authenticated user

### Requirement: The system SHALL expose GET /api/admin/facturas for admin invoice management (F10.5)

The system MUST provide an endpoint for FINANZAS/ADMIN users to view all teacher invoices with filtering capabilities.

Query parameters:
- `estado` (optional, Pendiente/Abonada) -- filter by status
- `periodo` (optional, YYYY-MM) -- filter by period
- `usuario_id` (optional, UUID) -- filter by teacher
- `q` (optional, string) -- free-text search on detalle
- `page`, `page_size` (optional, pagination defaults)

Response:
```json
{
  "items": [{ Factura detail with teacher name }],
  "total": 50,
  "page": 1,
  "page_size": 50
}
```

#### Scenario: Get all invoices as admin
- **WHEN** FINANZAS/ADMIN user sends GET /api/admin/facturas
- **THEN** the system SHALL return 200 with paginated list of all Facturas in the tenant
- **THEN** each item SHALL include teacher nombre and apellidos

#### Scenario: Filter invoices by estado
- **WHEN** GET /api/admin/facturas?estado=Pendiente
- **THEN** the system SHALL return only facturas with estado='Pendiente'

#### Scenario: Filter invoices by periodo
- **WHEN** GET /api/admin/facturas?periodo=2026-06
- **THEN** the system SHALL return only facturas for that period

#### Scenario: Filter invoices by teacher
- **WHEN** GET /api/admin/facturas?usuario_id=uuid-123
- **THEN** the system SHALL return only facturas for that teacher

#### Scenario: Free-text search on detalle
- **WHEN** GET /api/admin/facturas?q=honorarios
- **THEN** the system SHALL return facturas whose detalle contains "honorarios" (case-insensitive)

#### Scenario: Empty result set
- **WHEN** no facturas match the applied filters
- **THEN** the system SHALL return 200 with empty items array

#### Scenario: Reject non-admin access
- **WHEN** a PROFESOR user without facturas:gestionar sends GET /api/admin/facturas
- **THEN** the system SHALL return 403

### Requirement: The system SHALL expose PUT /api/admin/facturas/{id}/abonar to mark invoice as paid

The system MUST allow FINANZAS/ADMIN users to mark a Pendiente factura as Abonada. The endpoint SHALL optionally accept a query parameter `?descargar=true` to return the PDF file in the response.

Behavior:
- Sets estado = 'Abonada'
- Sets abonada_at = current timestamp
- If descargar=true, returns the PDF file as attachment
- Returns 409 if already Abonada
- Returns 404 if factura not found

#### Scenario: Mark invoice as paid
- **WHEN** FINANZAS user sends PUT /api/admin/facturas/{id}/abonar
- **THEN** the system SHALL set estado='Abonada' and abonada_at to current timestamp
- **THEN** SHALL return 200 with the updated Factura

#### Scenario: Mark invoice as paid with download
- **WHEN** FINANZAS user sends PUT /api/admin/facturas/{id}/abonar?descargar=true
- **THEN** the system SHALL mark as Abonada AND return the PDF as file attachment

#### Scenario: Mark already paid invoice returns 409
- **WHEN** PUT /api/admin/facturas/{id}/abonar is sent for an Abonada factura
- **THEN** the system SHALL return 409 Conflict

#### Scenario: Mark non-existent invoice returns 404
- **WHEN** PUT /api/admin/facturas/{id}/abonar is sent with a non-existent id
- **THEN** the system SHALL return 404

### Requirement: The system SHALL enforce authorization for all factura endpoints

Based on permission schema:
- `facturas:subir` -- POST /api/docentes/facturas (requires facturador=true)
- `facturas:gestionar` -- GET /api/admin/facturas, PUT /api/admin/facturas/{id}/abonar

Permission mapping (from AGENTS.md):
- PROFESOR with facturador=true: facturas:subir
- TUTOR with facturador=true: facturas:subir
- FINANZAS: facturas:gestionar
- ADMIN: facturas:gestionar

#### Scenario: Profesor facturante can upload
- **WHEN** a PROFESOR with facturador=true sends POST /api/docentes/facturas
- **THEN** the system SHALL allow the request (subject to validation)

#### Scenario: Profesor non-facturante cannot upload
- **WHEN** a PROFESOR with facturador=false sends POST /api/docentes/facturas
- **THEN** the system SHALL return 403

#### Scenario: FINANZAS can manage all invoices
- **WHEN** a FINANZAS user sends GET /api/admin/facturas or PUT /api/admin/facturas/{id}/abonar
- **THEN** the system SHALL allow the request

#### Scenario: Unauthenticated request rejected
- **WHEN** an unauthenticated request is sent to any /api/docentes/facturas or /api/admin/facturas endpoint
- **THEN** the system SHALL return 401
