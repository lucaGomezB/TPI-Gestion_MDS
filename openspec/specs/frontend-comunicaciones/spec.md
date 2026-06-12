## ADDED Requirements

### Requirement: Frontend feature module for communications

The frontend SHALL provide a feature module at `features/comunicaciones/` containing pages, hooks, services, and components for all communication features. The module SHALL follow the existing feature-based structure with lazy-loaded pages.

### Requirement: Mail preview before send (F3.1, RN-16)

The system SHALL provide a UI flow where the user fills a form (subject, body, optional alumnos) and previews the rendered email before confirming the send.

#### Scenario: Preview renders subject and body with sample data
- **GIVEN** a materia is selected
- **WHEN** the user fills asunto and cuerpo with template variables ({{alumno.nombre}}, {{materia.nombre}})
- **WHEN** the user clicks "Vista previa"
- **THEN** a modal SHALL display the rendered subject and body for sample recipients
- **THEN** the "Confirmar y enviar" button SHALL become enabled

#### Scenario: Send requires preview confirmation
- **WHEN** the user clicks "Confirmar y enviar" after preview
- **THEN** the system SHALL send POST `/api/materias/{id}/comunicaciones/enviar` with `preview_confirmado: true`
- **THEN** on success, the page SHALL redirect to the status tracking view

#### Scenario: Send button disabled without preview
- **WHEN** the user has not completed a preview
- **THEN** the "Confirmar y enviar" button SHALL be disabled

#### Scenario: Loading and error states
- **WHEN** the preview request is in progress
- **THEN** a loading indicator SHALL be shown
- **WHEN** the preview request fails
- **THEN** an error message SHALL be displayed with a retry option

### Requirement: Bulk send status tracking (F3.2)

The frontend SHALL display the status of sent lots (lotes) per materia with real-time tracking.

#### Scenario: Status page shows lotes list
- **WHEN** the user navigates to `/materias/{id}/comunicaciones`
- **THEN** the page SHALL display all LoteComunicacion records for that materia
- **THEN** each lote SHALL show: asunto, cantidad total, enviados, fallidos, estado, fecha
- **THEN** the status SHALL be color-coded via `LoteStatusBadge`

#### Scenario: Empty state when no communications sent
- **WHEN** the materia has no communications
- **THEN** an empty state message SHALL be shown: "No hay comunicaciones enviadas"

#### Scenario: Error state on API failure
- **WHEN** the API request fails
- **THEN** an ErrorDisplay component SHALL be shown with retry button

### Requirement: Approve/reject bulk sends (F3.3, RN-17)

The system SHALL provide an admin interface for approving or rejecting pending lotes.

#### Scenario: Approve list shows only pending lotes
- **WHEN** an admin navigates to `/admin/comunicaciones/aprobar`
- **THEN** the page SHALL list all lotes with estado `AprobacionPendiente`
- **THEN** each lote SHALL show: asunto, remitente, cantidad destinatarios, fecha

#### Scenario: Admin approves a lote
- **WHEN** the admin clicks "Aprobar" on a pending lote
- **THEN** a confirmation dialog SHALL appear
- **WHEN** confirmed, the system SHALL send PUT `/api/admin/comunicaciones/{id}/aprobar` with `accion: "aprobar"`
- **THEN** the lote SHALL disappear from the pending list

#### Scenario: Admin rejects a lote with motivo
- **WHEN** the admin clicks "Rechazar"
- **THEN** a dialog SHALL appear with an optional motivo field
- **WHEN** submitted, the system SHALL send PUT `/api/admin/comunicaciones/{id}/aprobar` with `accion: "rechazar"` and optional motivo
- **THEN** the lote SHALL disappear from the pending list

#### Scenario: Empty state — no pending lotes
- **WHEN** there are no lotes awaiting approval
- **THEN** an empty state message SHALL be shown: "No hay envios pendientes de aprobacion"

### Requirement: Public notice board (F3.5, RN-18..RN-20)

The frontend SHALL display visible avisos for the authenticated user, respecting scope, vigencia, and role filters.

#### Scenario: Notice board shows visible avisos
- **WHEN** an authenticated user navigates to `/avisos`
- **THEN** the page SHALL display all avisos visible to that user, ordered by orden ASC, created_at DESC
- **THEN** each aviso SHALL show: titulo, cuerpo, severidad (color-coded), vigencia dates

#### Scenario: ACK button for avisos requiring confirmation
- **WHEN** an aviso has `requiere_ack: true` and the user has not yet acknowledged it
- **THEN** a "Confirmar lectura" button SHALL be displayed on the aviso
- **WHEN** the user clicks the button
- **THEN** the system SHALL send POST `/api/avisos/{id}/ack`
- **THEN** the button SHALL be replaced with a "Leido" indicator

#### Scenario: ACK button hidden when already acknowledged
- **WHEN** an aviso has already been acknowledged by the user
- **THEN** no ACK button SHALL be shown

#### Scenario: Empty state — no visible avisos
- **WHEN** the user has no visible avisos
- **THEN** an empty state message SHALL be shown: "No hay avisos disponibles"

### Requirement: Admin CRUD for avisos (F3.5)

The frontend SHALL provide an admin interface for managing avisos.

#### Scenario: Admin table lists all avisos
- **WHEN** an admin navigates to `/admin/avisos`
- **THEN** a table SHALL display all avisos for the tenant with columns: titulo, alcance, severidad, vigencia, activo, orden
- **THEN** each row SHALL have edit and deactivate actions

#### Scenario: Create new aviso
- **WHEN** the admin clicks "Nuevo aviso"
- **THEN** a form SHALL open with fields: titulo, cuerpo, alcance, severidad, inicio_en, fin_en, orden, requiere_ack
- **WHEN** alcance is "PorMateria", materia_id SHALL be required
- **WHEN** alcance is "PorCohorte", cohorte_id SHALL be required
- **WHEN** submitted, the system SHALL send POST `/api/admin/avisos` with validated data
- **THEN** the form SHALL validate that inicio_en is before fin_en
- **THEN** on success, the table SHALL refresh

#### Scenario: Edit existing aviso
- **WHEN** the admin clicks edit on an aviso
- **THEN** a pre-filled form SHALL open with the existing data
- **WHEN** submitted, the system SHALL send PUT `/api/admin/avisos/{id}`
- **THEN** on success, the table SHALL refresh

#### Scenario: Deactivate aviso (soft delete)
- **WHEN** the admin clicks deactivate on an aviso
- **THEN** a confirmation dialog SHALL appear
- **WHEN** confirmed, the system SHALL send DELETE `/api/admin/avisos/{id}`
- **THEN** the aviso SHALL show as inactive in the table

### Requirement: Internal message inbox with threads (F3.4, F11.2)

The frontend SHALL provide an inbox with thread grouping and reply capability.

#### Scenario: Inbox lists thread summaries
- **WHEN** an authenticated user navigates to `/mensajes`
- **THEN** the system SHALL call GET `/api/mensajes`
- **THEN** each thread SHALL show: other participant name, asunto, ultimo_mensaje preview, fecha, no_leidos count
- **THEN** threads SHALL be ordered by most recent message first
- **THEN** threads with unread messages SHALL be visually distinguished

#### Scenario: Thread detail shows full history
- **WHEN** the user clicks a thread
- **THEN** the system SHALL navigate to `/mensajes/{id}`
- **THEN** all messages in the thread SHALL be displayed ordered by date ascending
- **THEN** messages addressed to the current user with `leido: false` SHALL be auto-marked as read

#### Scenario: Reply within thread
- **WHEN** the user types a message and clicks "Enviar" in the thread view
- **THEN** the system SHALL call POST `/api/mensajes/{id}/responder`
- **THEN** the new message SHALL appear in the thread immediately

#### Scenario: Send new message
- **WHEN** the user clicks "Nuevo mensaje" in the inbox
- **THEN** a form SHALL open with fields: destinatario (user search/select), asunto, cuerpo
- **WHEN** submitted, the system SHALL call POST `/api/mensajes`
- **THEN** on success, the user SHALL be redirected to the new thread

#### Scenario: Empty inbox
- **WHEN** the user has no messages
- **THEN** an empty state SHALL be shown: "No tienes mensajes"

#### Scenario: Unread count in sidebar
- **WHEN** the user has unread messages
- **THEN** the sidebar "Mensajes" item SHALL display a badge with the unread count
