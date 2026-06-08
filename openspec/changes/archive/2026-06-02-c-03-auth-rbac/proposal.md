## Why

The system has user identities (Usuario model) but no way to authenticate them or enforce permissions. Every protected endpoint needs JWT-based auth, role-based access control (RBAC), and secure password management before any domain feature can be built.

## What Changes

- Add `password_hash` (Argon2id), `totp_secret`, `totp_enabled` fields to Usuario model
- Create `Rol`, `UsuarioRol`, `RefreshToken` domain models
- Add JWT access (15min) + refresh token rotation auth flow
- Argon2id password hashing in `core/security.py`
- RBAC permissions matrix in `core/permissions.py` — 7 roles × permissions (`modulo:accion`)
- `require_permission("modulo:accion")` FastAPI dependency
- Rate limiting: 5 attempts / 60s per IP+email on login
- Migration 002: new tables and Usuario columns
- Endpoints: login, refresh, logout, forgot-password, reset-password, me
- Add `PyJWT`, `argon2-cffi`, `pyotp` to `requirements.txt`

## Capabilities

### New Capabilities
- `user-auth`: Authentication (JWT + refresh rotation, Argon2id, optional TOTP 2FA), RBAC (roles matrix, `require_permission` dependency), password recovery flow, rate limiting on login

### Modified Capabilities
- `core-models`: Usuario gets `password_hash`, `totp_secret`, `totp_enabled` fields. New models: `Rol`, `UsuarioRol`, `RefreshToken` added to the domain model catalog

## Impact

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/core/security.py` | Modified | Add `hash_password()`, `verify_password()`, JWT `create_access_token()`, `decode_access_token()`, `create_refresh_token()`, `decode_refresh_token()` |
| `backend/app/core/dependencies.py` | Modified | Add `get_current_user`, `require_permission` dependencies |
| `backend/app/core/config.py` | Modified | Add `REFRESH_TOKEN_EXPIRE_DAYS`, `TOTP_ISSUER_NAME` settings |
| `backend/app/core/permissions.py` | **New** | Permissions matrix: rol → set of `modulo:accion` permissions |
| `backend/app/models/usuario.py` | Modified | Add `password_hash`, `totp_secret`, `totp_enabled` columns |
| `backend/app/models/auth.py` | **New** | `Rol`, `UsuarioRol`, `RefreshToken` models |
| `backend/app/models/__init__.py` | Modified | Export new models |
| `backend/app/repositories/auth.py` | **New** | `UsuarioRepository` (find by email_hash), `RefreshTokenRepository` |
| `backend/app/services/auth.py` | **New** | Auth service: login, refresh, logout, password reset logic |
| `backend/app/services/rate_limiter.py` | **New** | In-memory rate limiter (5/60s per IP+email) |
| `backend/app/schemas/auth.py` | **New** | Pydantic schemas for auth requests/responses |
| `backend/app/api/v1/routers/auth.py` | **New** | Auth endpoints: login, refresh, logout, forgot-password, reset-password, me |
| `backend/app/api/v1/routers/__init__.py` | Modified | Register auth router |
| `backend/alembic/versions/` | **New** | Migration 002: roles, usuario_roles, refresh_tokens + Usuario columns |
| `backend/requirements.txt` | Modified | Add `PyJWT`, `argon2-cffi`, `pyotp` |
