## ADDED Requirements

### Requirement: Acknowledge reading an aviso (RN-19)

The system SHALL provide an endpoint at `POST /api/avisos/{id}/ack` that allows an authenticated user to confirm they have read an aviso marked with `requiere_ack = true`. The acknowledgment SHALL be recorded in the `AcknowledgmentAviso` table with user and timestamp. The endpoint SHALL be idempotent (safe to call multiple times).

#### Scenario: Confirm reading an aviso with requiere_ack
- **WHEN** an authenticated user sends POST to `/api/avisos/{id}/ack` and the aviso exists, is visible to the user (passes scope/vigencia filter), and has `requiere_ack = true`
- **THEN** the system SHALL create an AcknowledgmentAviso record with the user's id and current timestamp, and return HTTP 200 with `{ "acknowledged": true, "leido_en": "<timestamp>" }`

#### Scenario: Idempotent ack (safe retry)
- **WHEN** a user sends POST to `/api/avisos/{id}/ack` for an aviso they already acknowledged
- **THEN** the system SHALL return HTTP 200 with the existing acknowledgment record (no duplicate created) and `{ "acknowledged": true, "leido_en": "<existing_timestamp>" }`

#### Scenario: Reject ack for aviso without requiere_ack
- **WHEN** a user sends POST to `/api/avisos/{id}/ack` for an aviso where `requiere_ack = false`
- **THEN** the system SHALL reject the request with HTTP 400 and an error message indicating that this aviso does not require acknowledgment

#### Scenario: Reject ack for non-visible aviso
- **WHEN** a user sends POST to `/api/avisos/{id}/ack` for an aviso that is not visible to them (e.g., outside vigencia, wrong scope, wrong rol)
- **THEN** the system SHALL return HTTP 404 (aviso not found)

#### Scenario: Reject ack for non-existent aviso
- **WHEN** a user sends POST to `/api/avisos/{id}/ack` and no aviso with that id exists
- **THEN** the system SHALL return HTTP 404

#### Scenario: Multi-tenant ack isolation
- **WHEN** a user from tenant A sends POST to `/api/avisos/{id}/ack` for an aviso belonging to tenant B
- **THEN** the system SHALL return HTTP 404

#### Scenario: Ack count is derived from AcknowledgmentAviso table
- **WHEN** an admin views aviso details via GET /api/admin/avisos/{id}
- **THEN** the response SHALL include `ack_count` and `view_count` derived from the AcknowledgmentAviso table (not stored as denormalized fields)
