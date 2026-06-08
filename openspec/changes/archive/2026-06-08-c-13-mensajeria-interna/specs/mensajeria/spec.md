## ADDED Requirements

### Requirement: Enviar mensaje a otro usuario del mismo tenant (F3.4, F11.2)

The system SHALL provide an endpoint `POST /api/mensajes` that allows an authenticated user to send a message to another user within the same tenant. If no thread exists between the two users with the same asunto, the system SHALL create a new `HiloMensaje`.

- Request body SHALL include: `destinatario_id` (UUID), `asunto` (string, max 255), `cuerpo` (string).
- The system SHALL validate that `destinatario_id` exists and belongs to the same tenant.
- The system SHALL create a `HiloMensaje` if no existing thread matches the same `asunto` between the same sender-receiver pair, or use an existing thread with the same asunto.
- The system SHALL create a `Mensaje` with `remitente_id = current_user.id`, `leido = false`.
- The system SHALL return HTTP 201 with the created message and thread data.
- The system SHALL require the permission `mensajeria:enviar`.

#### Scenario: Send message creates new thread

- **WHEN** user A sends POST `/api/mensajes` with `{destinatario_id: "user-b", asunto: "Novedades", cuerpo: "Hola"}` to user B and no thread exists between A and B with asunto "Novedades"
- **THEN** the system SHALL return HTTP 201
- **THEN** the response SHALL include `hilo_id` for the newly created thread
- **THEN** the response SHALL include `id` for the newly created message
- **THEN** the created message SHALL have `leido = false`

#### Scenario: Send message reuses existing thread

- **WHEN** user A sends POST `/api/mensajes` with the same `destinatario_id` and `asunto` as a previous message
- **THEN** the system SHALL reuse the existing `HiloMensaje`
- **THEN** the new message SHALL have the same `hilo_id` as the previous one

#### Scenario: Rejects send to non-existent user

- **WHEN** user A sends POST `/api/mensajes` with a `destinatario_id` that does not exist
- **THEN** the system SHALL return HTTP 404

#### Scenario: Rejects send to user in different tenant

- **WHEN** user A sends POST `/api/mensajes` with a `destinatario_id` belonging to a different tenant
- **THEN** the system SHALL return HTTP 404 (user not found — no tenant info leakage)

#### Scenario: Rejects send without mensajeria:enviar permission

- **WHEN** a user without the `mensajeria:enviar` permission sends POST `/api/mensajes`
- **THEN** the system SHALL return HTTP 403

#### Scenario: Rejects send with empty cuerpo

- **WHEN** user A sends POST `/api/mensajes` with `cuerpo` being empty or whitespace-only
- **THEN** the system SHALL return HTTP 400

---

### Requirement: Responder dentro de un hilo (F3.4, F11.2)

The system SHALL provide an endpoint `POST /api/mensajes/{id}/responder` that allows an authenticated user to reply within an existing message thread.

- The `{id}` parameter SHALL reference an existing `Mensaje` (to identify the thread via `hilo_id`).
- The authenticated user MUST be either `remitente_id` or `destinatario_id` of messages in that thread.
- Request body SHALL include: `cuerpo` (string).
- The system SHALL create a new `Mensaje` with the same `hilo_id`, `remitente_id = current_user.id`, and `leido = false`.
- The system SHALL auto-set `destinatario_id` to the other participant in the thread (the user who is NOT `current_user`).
- The system SHALL return HTTP 201.

#### Scenario: Reply to thread as original sender

- **WHEN** user A sent the first message to user B, and user A sends POST `/api/mensajes/{id}/responder` with `{cuerpo: "Respuesta"}`
- **THEN** the system SHALL return HTTP 201
- **THEN** the new message SHALL have `remitente_id = user A`
- **THEN** the new message SHALL have `destinatario_id = user B`
- **THEN** the new message SHALL have the same `hilo_id` as the original message

#### Scenario: Reply to thread as receiver

- **WHEN** user B received a message from user A, and user B sends POST `/api/mensajes/{id}/responder` with `{cuerpo: "Gracias"}`
- **THEN** the system SHALL return HTTP 201
- **THEN** the new message SHALL have `remitente_id = user B`
- **THEN** the new message SHALL have `destinatario_id = user A`

#### Scenario: Rejects reply from non-participant

- **WHEN** user C (not a participant in the thread) sends POST `/api/mensajes/{id}/responder`
- **THEN** the system SHALL return HTTP 403

#### Scenario: Rejects reply with empty cuerpo

- **WHEN** a participant sends POST `/api/mensajes/{id}/responder` with empty `cuerpo`
- **THEN** the system SHALL return HTTP 400

---

### Requirement: Ver bandeja de entrada del usuario autenticado (F3.4)

The system SHALL provide an endpoint `GET /api/mensajes` that returns the authenticated user's inbox: all threads where the user is a participant, ordered by most recent message first.

- Each item SHALL include: `hilo_id`, `asunto`, `ultimo_mensaje` (cuerpo del ultimo mensaje truncado), `ultima_fecha`, `remitente_nombre`, `no_leidos` (count of unread messages in that thread for this user).
- The response SHALL be paginated with configurable `limit` (default 20) and `offset` (default 0).
- The response SHALL include a `total` field for total count.
- Soft-deleted threads (where the user has deleted their copy) SHALL NOT appear.

#### Scenario: Returns inbox with threads grouped

- **WHEN** an authenticated user sends GET `/api/mensajes`
- **THEN** the system SHALL return HTTP 200
- **THEN** the response SHALL contain a `data` array of thread summaries
- **THEN** each summary SHALL include `hilo_id`, `asunto`, `ultimo_mensaje`, `ultima_fecha`, `no_leidos`
- **THEN** threads SHALL be ordered by `ultima_fecha` descending

#### Scenario: Returns paginated results

- **WHEN** an authenticated user sends GET `/api/mensajes?limit=5&offset=0`
- **THEN** the response SHALL contain at most 5 items in `data`
- **THEN** the response SHALL include `total` with the overall count
- **THEN** the response SHALL include `limit` and `offset` matching the request

#### Scenario: Returns empty inbox

- **WHEN** an authenticated user with no messages sends GET `/api/mensajes`
- **THEN** the system SHALL return HTTP 200 with `data: []` and `total: 0`

#### Scenario: Multi-tenant isolation

- **WHEN** two users from different tenants each access GET `/api/mensajes`
- **THEN** each SHALL only see their own tenant's messages

---

### Requirement: Ver hilo completo de mensajes (F3.4)

The system SHALL provide an endpoint `GET /api/mensajes/{id}` that returns all messages in a thread where the authenticated user is a participant.

- The `{id}` parameter SHALL reference a `Mensaje` UUID.
- The authenticated user MUST be a participant in that thread (remitente_id or destinatario_id of any message in the hilo).
- All messages in the thread SHALL be returned ordered by `created_at` ascending.
- Messages that were deleted by the current user SHALL NOT be returned.
- When the response is returned, all messages in that thread where `destinatario_id = current_user.id` and `leido = false` SHALL be marked as `leido = true`.

#### Scenario: Returns thread messages ordered by date

- **WHEN** an authenticated participant sends GET `/api/mensajes/{id}`
- **THEN** the system SHALL return HTTP 200
- **THEN** the response SHALL include `hilo_id`, `asunto`, `participantes`, and `mensajes` array
- **THEN** messages SHALL be ordered by `created_at` ascending
- **THEN** each message SHALL include `id`, `remitente_id`, `destinatario_id`, `cuerpo`, `created_at`, `leido`

#### Scenario: Auto-marks messages as read

- **WHEN** a participant views a thread with unread messages addressed to them
- **THEN** those messages SHALL be marked `leido = true`
- **THEN** subsequent GET requests for that thread SHALL show `leido = true`

#### Scenario: Rejects access for non-participant

- **WHEN** a user who is not a participant in the thread sends GET `/api/mensajes/{id}`
- **THEN** the system SHALL return HTTP 403

#### Scenario: Returns empty array when all messages deleted by user

- **WHEN** a participant sends GET `/api/mensajes/{id}` and all messages in the thread have been deleted by that user
- **THEN** the system SHALL return HTTP 200 with `mensajes: []`

---

### Requirement: Contador de mensajes no leidos (F3.4)

The system SHALL provide an endpoint `GET /api/mensajes/no-leidos` that returns the count of unread messages for the authenticated user.

- The endpoint SHALL return `{ count: N }` where N is the number of messages with `destinatario_id = current_user.id` and `leido = false`.
- The count SHALL be scoped to the user's tenant.
- This endpoint SHALL NOT require the `mensajeria:enviar` permission (any authenticated user can check their inbox).

#### Scenario: Returns unread count

- **WHEN** an authenticated user has 3 unread messages and sends GET `/api/mensajes/no-leidos`
- **THEN** the system SHALL return HTTP 200 with `{ count: 3 }`

#### Scenario: Returns zero when no unread messages

- **WHEN** an authenticated user has no unread messages and sends GET `/api/mensajes/no-leidos`
- **THEN** the system SHALL return HTTP 200 with `{ count: 0 }`
