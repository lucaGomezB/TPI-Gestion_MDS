## ADDED Requirements

### Requirement: Communication queue with lifecycle states (RN-15)

The system SHALL provide a communication queue where each outbound message follows a strict lifecycle: Pendiente > Enviando > Enviado | Error | Cancelado. Each message SHALL be tracked individually with a unique identifier (UUID), status, and timestamp of state transitions. The system SHALL support grouping messages into a lote (batch) for bulk sends, where each lote also has its own aggregated state tracking.

#### Scenario: Individual message lifecycle from Pendiente to Enviado
- **WHEN** a communication is enqueued
- **THEN** its initial estado SHALL be "Pendiente"
- **WHEN** the worker picks it up for processing
- **THEN** its estado SHALL transition to "Enviando"
- **WHEN** the email is successfully sent via SMTP
- **THEN** its estado SHALL transition to "Enviado" AND enviado_at SHALL be set to the current timestamp

#### Scenario: Message transitions to Error on send failure
- **WHEN** the worker attempts to send a message and the SMTP operation fails
- **THEN** its estado SHALL transition to "Error" AND error_msg SHALL contain the failure details AND retry_count SHALL be incremented
- **WHEN** retry_count is less than 3
- **THEN** the worker SHALL reset estado to "Pendiente" on next poll cycle for retry

#### Scenario: Message reaches terminal state after max retries
- **WHEN** retry_count reaches 3 (maximum configured retries)
- **THEN** the message SHALL remain in "Error" state permanently (terminal)

#### Scenario: Message cancellation
- **WHEN** an authorized user cancels a communication before it is sent
- **THEN** its estado SHALL transition to "Cancelado" AND it SHALL NOT be processed by the worker

#### Scenario: Lote aggregated status tracks batch progress
- **WHEN** a bulk send is created with multiple recipients
- **THEN** a LoteComunicacion record SHALL be created with estado "Pendiente" and total counter set to the number of recipients
- **WHEN** all individual messages in the lote reach "Enviado"
- **THEN** the lote estado SHALL transition to "Completado" AND enviados counter SHALL equal total
- **WHEN** some messages reach "Enviado" and some reach "Error"
- **THEN** the lote estado SHALL transition to "Parcial" AND counters SHALL reflect actual counts

---

### Requirement: Mandatory preview before send (RN-16)

The system SHALL require a preview step before any communication can be sent. The preview SHALL render the subject and body templates with actual data for at least one sample recipient. The send operation SHALL reject requests that do not explicitly confirm the preview.

#### Scenario: Preview endpoint returns rendered content
- **WHEN** a user with `comunicacion:enviar` permission sends a POST request to `/api/materias/{id}/comunicaciones/preview` with asunto template, cuerpo template, and optional list of alumno_ids
- **THEN** the system SHALL render the templates against actual EntradaPadron and Materia data AND return the rendered asunto and cuerpo for each requested or sampled student

#### Scenario: Preview samples up to 5 students when alumno_ids omitted
- **WHEN** the preview request does not include alumno_ids
- **THEN** the system SHALL select up to 5 random students from the materia's active padron for the preview

#### Scenario: Send requires preview_confirmado
- **WHEN** a send request is made without preview_confirmado set to true
- **THEN** the system SHALL reject the request with HTTP 400 AND an error message indicating preview confirmation is required

#### Scenario: PROFESOR can only preview for assigned materias
- **WHEN** a PROFESOR sends a preview request for a materia they are not assigned to
- **THEN** the system SHALL reject the request with HTTP 403

---

### Requirement: Bulk send with lote grouping and queue (F3.2)

The system SHALL support sending communications to multiple recipients in a single operation. Recipients are resolved from the materia's active padron (or a specific subset if alumno_ids are provided). The send operation SHALL create one Comunicacion per recipient and one LoteComunicacion to group them.

#### Scenario: Bulk send to all padron entries for a materia
- **WHEN** a user sends a POST to `/api/materias/{id}/comunicaciones/enviar` with asunto, cuerpo, and preview_confirmado=true, without alumno_ids
- **THEN** the system SHALL create one Comunicacion per active EntradaPadron entry for that materia, all linked to a single LoteComunicacion, AND return HTTP 201 with the lote ID

#### Scenario: Bulk send to specific recipients
- **WHEN** a user sends a POST to `/api/materias/{id}/comunicaciones/enviar` with a list of alumno_ids
- **THEN** the system SHALL create Comunicaciones only for the specified EntradaPadron entries that belong to the materia

#### Scenario: Bulk send creates lotes with estado tracking
- **WHEN** the bulk send is created without approval requirement
- **THEN** the LoteComunicacion SHALL be in estado "Pendiente" and immediately eligible for worker processing
- **WHEN** the bulk send is created with approval requirement (tenant config)
- **THEN** the LoteComunicacion SHALL be in estado "AprobacionPendiente" and NOT eligible for worker processing until approved

#### Scenario: Real-time status tracking by materia
- **WHEN** a user sends GET to `/api/materias/{id}/comunicaciones`
- **THEN** the system SHALL return all LoteComunicacion records for that materia, with each lote showing: id, total, enviados, fallidos, estado, created_at, and requiere_aprobacion

---

### Requirement: Template engine with variable substitution (RF-20)

The system SHALL support template variables in the subject and body of communications. The supported variables SHALL be `{{alumno.nombre}}` and `{{materia.nombre}}`. Variables SHALL be replaced with actual values at send time.

#### Scenario: Template renders alumno nombre correctly
- **WHEN** a communication body contains `{{alumno.nombre}}`
- **THEN** the system SHALL replace it with the corresponding EntradaPadron.alumno_nombre value for each recipient

#### Scenario: Template renders materia nombre correctly
- **WHEN** a communication body contains `{{materia.nombre}}`
- **THEN** the system SHALL replace it with the corresponding Materia.nombre value

#### Scenario: Unknown variable preserved as-is
- **WHEN** a template contains a variable that does not match known patterns
- **THEN** the system SHALL leave the variable text unchanged (no substitution, no error)

---

### Requirement: Administrative approval for bulk sends (RN-17)

The system SHALL support an optional approval flow for bulk communications, controlled by tenant-level configuration. When enabled, bulk sends require explicit approval from a user with `comunicacion:aprobar` permission before the worker processes them.

#### Scenario: Approval requirement is tenant-configurable
- **WHEN** a tenant has `requiere_aprobacion_masiva: true` in its configuration
- **THEN** all bulk sends (more than 1 recipient) SHALL require approval before processing
- **WHEN** a tenant has `requiere_aprobacion_masiva: false` (or unset)
- **THEN** bulk sends SHALL proceed directly to queue without approval

#### Scenario: Admin approves a pending bulk send
- **WHEN** an authorized user sends PUT to `/api/admin/comunicaciones/{id}/aprobar` with `accion: "aprobar"`
- **THEN** the system SHALL set LoteComunicacion.estado to "Enviando", set aprobado_por to the approver's user ID, set aprobado_at to current timestamp, AND the worker SHALL begin processing the lote

#### Scenario: Admin rejects a pending bulk send
- **WHEN** an authorized user sends PUT to `/api/admin/comunicaciones/{id}/aprobar` with `accion: "rechazar"` and optional motivo
- **THEN** the system SHALL set LoteComunicacion.estado to "Cancelado", set all associated Comunicaciones to "Cancelado" with the reject motivo in error_msg

#### Scenario: Unauthorized user cannot approve
- **WHEN** a user without `comunicacion:aprobar` permission sends a request to the approve endpoint
- **THEN** the system SHALL reject with HTTP 403

---

### Requirement: Async worker for queue processing

The system SHALL run a background worker that periodically polls the queue and processes Pendiente communications. The worker SHALL run in a separate process/container and SHALL support configurable poll interval and retry policy.

#### Scenario: Worker picks up Pendiente items
- **WHEN** the worker runs its poll cycle
- **THEN** it SHALL query for LoteComunicacion records with estado in (Pendiente, Enviando) AND their associated Comunicaciones with estado = Pendiente and retry_count < 3

#### Scenario: Worker processes items sequentially
- **WHEN** the worker picks up a batch of communications for a lote
- **THEN** it SHALL send each via SMTP, updating each Comunicacion's estado to Enviado or Error after the send attempt, and update the Lote aggregated counters and estado when all items in the batch are processed

#### Scenario: Worker configurable via environment variables
- **WHEN** the worker starts
- **THEN** it SHALL read WORKER_POLL_INTERVAL and WORKER_MAX_RETRIES from configuration
- **WHEN** the worker stops or crashes
- **THEN** items in "Enviando" state SHALL be reprocessed on next worker restart (idempotent — emails sent but not committed will fail on duplicate detection)

---

### Requirement: PII encryption for recipient email

The system SHALL encrypt the `destinatario` field of each Comunicacion using AES-256 with the tenant's encryption key, following the existing PII encryption pattern from `core/security.py`.

#### Scenario: Destinatario is encrypted at rest
- **WHEN** a Comunicacion record is created with a recipient email address
- **THEN** the `destinatario` field in the database SHALL contain the AES-256 encrypted value, not the plaintext email

#### Scenario: API response masks the email
- **WHEN** a Comunicacion is returned via API
- **THEN** the response SHALL show a masked version of the email (e.g., "j***@example.com"), never the full plaintext
