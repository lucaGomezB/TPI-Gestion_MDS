# User Auth

> **Purpose**: Define the authentication and authorization system — password-based login with optional TOTP 2FA, JWT access tokens with refresh rotation, RBAC permission enforcement, rate limiting, and password recovery. All auth operations respect multi-tenant boundaries.

---

## Requirements

### Requirement: The system SHALL authenticate users via email and password with Argon2id

The system MUST provide a login endpoint at `POST /api/auth/login` that accepts `email` and `password`. Passwords MUST be hashed using Argon2id. Login lookups MUST use `email_hash` (SHA-256 of lowercased email) to avoid decrypting the PII email column.

#### Scenario: Successful login without 2FA
- **WHEN** a POST request is sent to `/api/auth/login` with valid `email` and `password` for a user who has `totp_enabled=false`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `access_token`, `refresh_token`, and `token_type: "bearer"`
- **THEN** the `access_token` SHALL be a JWT with `sub`, `tenant_id`, `roles`, `exp`, `iat`, `jti`

#### Scenario: Login with invalid password
- **WHEN** a POST request is sent to `/api/auth/login` with a valid email but wrong password
- **THEN** the response SHALL have status `401`
- **THEN** the response body SHALL contain `detail: "Invalid email or password"` (generic message, no hint of which is wrong)

#### Scenario: Login with non-existent email
- **WHEN** a POST request is sent to `/api/auth/login` with an email that does not exist in the system
- **THEN** the response SHALL have status `401`
- **THEN** the response body SHALL contain `detail: "Invalid email or password"` (same generic message)

#### Scenario: Login for inactive user
- **WHEN** a POST request is sent to `/api/auth/login` with credentials of a soft-deleted user (`estado=Inactivo`)
- **THEN** the response SHALL have status `401`

#### Scenario: Login with wrong tenant context
- **WHEN** a user from tenant A attempts to log in
- **THEN** only users from that same tenant SHALL be considered in the email lookup (tenant boundary enforced by query scope)

### Requirement: The system SHALL support optional TOTP 2FA during login

The system MUST support optional Time-based One-Time Password (TOTP) two-factor authentication. When enabled for a user, the login flow requires an additional step with a TOTP code.

#### Scenario: Login with 2FA enabled — first step
- **WHEN** a POST request is sent to `/api/auth/login` with valid credentials for a user with `totp_enabled=true`
- **THEN** the response SHALL have status `202`
- **THEN** the response body SHALL contain `requires_2fa: true` and a `temp_token`
- **THEN** the `temp_token` SHALL be a short-lived JWT (max 2 minutes) with `purpose: "totp_verification"` and `sub`

#### Scenario: Login with 2FA — complete with valid code
- **WHEN** a POST request is sent to `/api/auth/login/totp` with a valid `temp_token` and `totp_code` (6 digits)
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `access_token`, `refresh_token`, and `token_type: "bearer"`

#### Scenario: Login with 2FA — invalid TOTP code
- **WHEN** a POST request is sent to `/api/auth/login/totp` with a valid `temp_token` but wrong `totp_code`
- **THEN** the response SHALL have status `401`
- **THEN** the response SHALL contain `detail: "Invalid verification code"`

#### Scenario: Login with 2FA — expired temp_token
- **WHEN** a POST request is sent to `/api/auth/login/totp` with an expired `temp_token`
- **THEN** the response SHALL have status `401`

### Requirement: The system SHALL provide JWT refresh with token rotation

The system MUST provide a refresh endpoint at `POST /api/auth/refresh` that accepts a valid refresh token and returns a new access token and a new refresh token. The old refresh token MUST be revoked (rotation).

#### Scenario: Successful token refresh
- **WHEN** a POST request is sent to `/api/auth/refresh` with a valid, non-expired, non-revoked `refresh_token`
- **THEN** the old token SHALL be marked as revoked in the database
- **THEN** the response SHALL contain a new `access_token` and a new `refresh_token`
- **THEN** the new refresh token SHALL belong to the same `token_family` as the old one

#### Scenario: Refresh with revoked token (theft detection)
- **WHEN** a POST request is sent to `/api/auth/refresh` with a `refresh_token` that was already revoked
- **THEN** ALL tokens in that `token_family` SHALL be revoked (family-wide revocation)
- **THEN** the response SHALL have status `401`

#### Scenario: Refresh with expired token
- **WHEN** a POST request is sent to `/api/auth/refresh` with an expired `refresh_token`
- **THEN** the response SHALL have status `401`

### Requirement: The system SHALL support logout by token revocation

The system MUST provide a logout endpoint at `POST /api/auth/logout` that accepts a refresh token and revokes it.

#### Scenario: Successful logout
- **WHEN** an authenticated POST request is sent to `/api/auth/logout` with a valid `refresh_token`
- **THEN** the token SHALL be marked as revoked
- **THEN** the response SHALL have status `204`

### Requirement: The system SHALL provide password recovery with single-use tokens

The system MUST provide a forgot-password flow that generates a single-use, time-limited token and a reset-password endpoint that consumes it.

#### Scenario: Forgot password request
- **WHEN** a POST request is sent to `/api/auth/forgot-password` with a registered `email`
- **THEN** the system SHALL generate a cryptographically random token (32 bytes, hex-encoded)
- **THEN** the token SHALL be stored with a 1-hour expiry
- **THEN** the response SHALL have status `200` with message `"If the email exists, a recovery link has been sent"`

#### Scenario: Forgot password for unknown email
- **WHEN** a POST request is sent to `/api/auth/forgot-password` with an unregistered `email`
- **THEN** the response SHALL have status `200` with the same generic message (no information leakage)

#### Scenario: Successful password reset
- **WHEN** a POST request is sent to `/api/auth/reset-password` with a valid `token` and a `new_password` (at least 8 characters)
- **THEN** the password SHALL be updated (hashed with Argon2id)
- **THEN** the token SHALL be marked as used
- **THEN** ALL refresh tokens for that user SHALL be revoked
- **THEN** the response SHALL have status `200`

#### Scenario: Reset with expired token
- **WHEN** a POST request is sent to `/api/auth/reset-password` with an expired token
- **THEN** the response SHALL have status `400`

#### Scenario: Reset with already-used token
- **WHEN** a POST request is sent to `/api/auth/reset-password` with a token that was already consumed
- **THEN** the response SHALL have status `400`

### Requirement: The system SHALL expose the current user profile

The system MUST provide an endpoint at `GET /api/auth/me` that returns the authenticated user's profile.

#### Scenario: Get current user
- **WHEN** an authenticated GET request is sent to `/api/auth/me`
- **THEN** the response SHALL have status `200`
- **THEN** the response body SHALL contain `id`, `nombre`, `apellidos`, `email`, `roles`, `tenant_id`
- **THEN** the response SHALL NOT expose `password_hash`, `totp_secret`, or `deleted_at`

#### Scenario: Get current user without auth
- **WHEN** a GET request is sent to `/api/auth/me` without a valid JWT
- **THEN** the response SHALL have status `401`

### Requirement: The system SHALL enforce RBAC via require_permission dependency

The system MUST provide a `require_permission(permission: str)` FastAPI dependency that checks the authenticated user's roles against a permissions matrix. The matrix SHALL define which permissions each role has, in `modulo:accion` format.

#### Scenario: User with required permission passes
- **WHEN** a user with a role that includes `calificaciones:importar` accesses a route protected by `require_permission("calificaciones:importar")`
- **THEN** the request SHALL proceed to the handler

#### Scenario: User without required permission is rejected
- **WHEN** a user whose roles do NOT include `calificaciones:importar` accesses a protected route
- **THEN** the response SHALL have status `403`
- **THEN** the response body SHALL contain `detail: "Not enough permissions"`

#### Scenario: Unauthenticated user is rejected
- **WHEN** a request without a valid JWT accesses any protected route
- **THEN** the response SHALL have status `401`

### Requirement: The system SHALL rate-limit login attempts

The system MUST enforce a rate limit of 5 failed login attempts per 60-second sliding window, keyed by the combination of source IP address and email.

#### Scenario: Rate limit exceeded
- **WHEN** 6 or more failed login attempts occur within 60 seconds for the same IP+email combination
- **THEN** the 6th attempt SHALL receive status `429`
- **THEN** the response SHALL contain `detail: "Too many login attempts. Try again in 60 seconds."`

#### Scenario: Rate limit resets after successful login
- **WHEN** a successful login occurs after some failed attempts
- **THEN** the rate limit counter for that IP+email SHALL be reset

#### Scenario: Rate limit resets after cooldown
- **WHEN** 60 seconds have passed since the oldest attempt in the window
- **THEN** the next login attempt SHALL be allowed (sliding window)

### Requirement: The system SHALL define the RBAC permissions matrix for 7 roles

The system SHALL define a permissions matrix with the following roles and capabilities. Permissions are expressed as `modulo:accion` strings.

| Capacidad | ALUMNO | TUTOR | PROFESOR | COORDINADOR | ADMIN | FINANZAS |
|-----------|:------:|:-----:|:--------:|:-----------:|:-----:|:--------:|
| `estado_academico:ver_propio` | ✅ | — | — | — | — | — |
| `evaluacion:reservar` | ✅ | — | — | — | — | — |
| `aviso:confirmar` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `calificaciones:importar` | — | — | ✅ | ✅ | ✅ | — |
| `atrasados:ver` | — | ✅ | ✅ | ✅ | ✅ | — |
| `entrega:detectar_pendiente` | — | ✅ | ✅ | ✅ | ✅ | — |
| `comunicacion:enviar` | — | — | ✅ | ✅ | ✅ | — |
| `comunicacion:aprobar` | — | — | — | ✅ | ✅ | — |
| `encuentro:gestionar` | — | ✅ | ✅ | ✅ | ✅ | — |
| `guardia:registrar` | — | ✅ | ✅ | ✅ | ✅ | — |
| `tarea_interna:gestionar` | — | — | ✅ | ✅ | ✅ | — |
| `aviso:publicar` | — | — | — | ✅ | ✅ | — |
| `equipo_docente:asignar` | — | — | — | ✅ | ✅ | — |
| `estructura_academica:gestionar` | — | — | — | — | ✅ | — |
| `usuario:gestionar` | — | — | — | — | ✅ | — |
| `auditoria:ver` | — | — | — | ✅ | ✅ | ✅ |
| `grilla_salarial:operar` | — | — | — | — | — | ✅ |
| `liquidacion:calcular` | — | — | — | — | — | ✅ |
| `liquidacion:cerrar` | — | — | — | — | — | ✅ |
| `factura:gestionar` | — | — | — | — | — | ✅ |
| `tenant:configurar` | — | — | — | — | ✅ | — |

**Note:** `✅` indicates the role has the permission. `✅ (propio)` is represented as the base permission — scope filtering is enforced at the handler level, not in the auth layer.

#### Scenario: Permissions matrix is authoritative
- **WHEN** `require_permission("factura:gestionar")` is checked for an ADMIN user
- **THEN** the response SHALL be `403` (ADMIN does not have `factura:gestionar`)
- **WHEN** the same permission is checked for a FINANZAS user
- **THEN** the response SHALL proceed to the handler

#### Scenario: NEXO role has no permissions in MVP
- **WHEN** `require_permission(any_permission)` is checked for a user with only the NEXO role
- **THEN** the response SHALL be `403` for all permissions except `aviso:confirmar`

### Requirement: The JWT SHALL NOT contain permissions

The JWT access token payload MUST contain only `sub` (user UUID), `tenant_id` (tenant UUID), `roles` (list of role name strings), `exp`, `iat`, and `jti`. Permissions MUST NOT be embedded in the token.

#### Scenario: JWT payload structure
- **WHEN** a valid JWT is decoded
- **THEN** it SHALL contain exactly these claims: `sub`, `tenant_id`, `roles`, `exp`, `iat`, `jti`
- **THEN** it SHALL NOT contain any claim named `permissions` or `perms`
