## 1. Dependencies and Configuration

- [x] 1.1 Add `PyJWT`, `argon2-cffi`, `pyotp` to `backend/requirements.txt`
- [x] 1.2 Add `REFRESH_TOKEN_EXPIRE_DAYS=7` and `TOTP_ISSUER_NAME=activia-trace` to `Settings` in `core/config.py`
- [x] 1.3 Verify `.env.example` includes `SECRET_KEY` with 32+ chars (document requirement)
  — `config.py` Field validates `SECRET_KEY` with `min_length=32`. Enforced at Settings level.

## 2. Auth Models (new + modified)

- [x] 2.1 Add `password_hash`, `totp_secret` (EncryptedString, nullable), `totp_enabled` (Boolean, default=False) to `Usuario` model
- [x] 2.2 Create `Rol` model in `models/rol.py`: id, tenant_id, nombre (unique per tenant), descripcion, permisos (JSONB), timestamps
- [x] 2.3 Create `UsuarioRol` model in `models/usuario_rol.py`: id, usuario_id (FK), rol_id (FK), tenant_id, vigencia_desde, vigencia_hasta, created_at. Unique on (usuario_id, rol_id)
- [x] 2.4 Create `RefreshToken` model in `models/refresh_token.py`: id, usuario_id (FK), token_hash, expires_at, revoked_at, token_family, tenant_id, created_at. Indexes on token_hash and token_family
- [x] 2.5 Create `PasswordResetToken` model in `models/password_reset_token.py`: id, usuario_id (FK), token_hash, expires_at, used_at, created_at. Index on token_hash
- [x] 2.6 Update `models/__init__.py` to export all new models

## 3. Migration 002 — Auth Schema

- [x] 3.1 Generate Alembic migration (revision 002, depends_on 001) with upgrade:
  - Add columns to usuarios: `password_hash` (VARCHAR(255)), `totp_secret` (TEXT, nullable), `totp_enabled` (BOOLEAN, default=false)
  - Create `roles` table
  - Create `usuario_roles` table
  - Create `refresh_tokens` table (with indexes)
  - Create `password_reset_tokens` table (with indexes)
- [x] 3.2 Implement `downgrade()` — reverse all changes
- [ ] 3.3 Run migration and verify against test database — **Requires PostgreSQL**

## 4. Core Security — password hashing and JWT

- [x] 4.1 Add `hash_password(plain: str) -> str` using Argon2id (`memory_cost=19456`, `time_cost=2`, `parallelism=1`)
- [x] 4.2 Add `verify_password(plain: str, hash: str) -> bool` using Argon2id
- [x] 4.3 Add `create_access_token(sub: str, tenant_id: str, roles: list[str]) -> str` — HS256, 15 min expiry, includes jti (UUID)
- [x] 4.4 Add `decode_access_token(token: str) -> dict` — raises on expiry/invalid signature
- [x] 4.5 Add `create_refresh_token() -> tuple[str, str, str]` — returns (raw_token, token_hash, token_family_uuid)
- [x] 4.6 Add `create_temp_token(sub: str, purpose: str, expiry_minutes: int) -> str` — for TOTP 2FA handshake
- [x] 4.7 Export all new functions from `core/security.py`

## 5. Rate Limiter

- [x] 5.1 Create `core/rate_limiter.py` with in-memory sliding window rate limiter
  - Window: 60 seconds, max 5 attempts
  - Key: `{ip}:{email_hash}`
  - Reset on successful login
- [x] 5.2 Create FastAPI dependency `check_login_rate_limit(request: Request, email: str) -> None` that returns 429 if exceeded

## 6. RBAC Permissions Matrix

- [x] 6.1 Create `core/permissions.py` with `ROL_PERMISSIONS: dict[str, set[str]]` defining the full matrix (7 roles × ~20 permissions)
- [x] 6.2 Create `require_permission(permission: str) -> callable` factory that returns a FastAPI dependency
  - Extracts `roles` from JWT via `get_current_user`
  - Cross-references each role against `ROL_PERMISSIONS`
  - Returns 403 if no role has the permission

## 7. FastAPI Dependencies

- [x] 7.1 Add `get_current_user` dependency in `core/dependencies.py`:
  - Extract Authorization header (Bearer token)
  - Decode JWT via `decode_access_token`
  - Return id+roles+tenant_id from token payload
  - Return `401` on invalid/missing token
- [x] 7.2 Export `get_current_user` and `require_permission` from `core/dependencies.py`

## 8. Pydantic Schemas

- [x] 8.1 Create `schemas/auth.py` with all 8 schemas, all with `extra='forbid'`

## 9. Auth Repository

- [x] 9.1 Create `repositories/auth_repository.py` with all 9 methods

## 10. Auth Service

- [x] 10.1 Create `services/auth_service.py` with all 6 service methods:
  - `login()` — password verify + optional 2FA
  - `verify_totp()` — TOTP code validation
  - `refresh()` — rotation + theft detection
  - `logout()` — token revocation
  - `forgot_password()` — idempotent, no info leak
  - `reset_password()` — consume token, update password, revoke all tokens

## 11. Auth Router

- [x] 11.1 Create `api/v1/routers/auth.py` with all 7 endpoints
- [x] 11.2 Register auth router in `api/v1/routers/__init__.py`
- [x] 11.3 Wire routers into `main.py` under `/api/v1`

## 12. Seed Update

- [x] 12.1 Create rol instances for each of the 7 roles in seed_001
- [x] 12.2 Assign ADMIN role to the existing admin user via UsuarioRol
- [x] 12.3 Set Argon2id-hashed password for admin user (default: `admin123456` or via `ADMIN_DEFAULT_PASSWORD` env var)
- [x] 12.4 Make seed idempotent on re-run (check role existence before insert)

## 13. Tests

- [x] 13.1 Unit test for `hash_password` + `verify_password` roundtrip (6 cases, in `test_security_auth.py`)
- [x] 13.2 Unit test for JWT roundtrip, expiry, wrong key (8 cases, in `test_security_auth.py`)
- [ ] 13.3 Integration test for `POST /api/auth/login` — **Requires PostgreSQL**
- [ ] 13.4 Integration test for `POST /api/auth/refresh` — **Requires PostgreSQL**
- [ ] 13.5 Integration test for `POST /api/auth/logout` — **Requires PostgreSQL**
- [ ] 13.6 Integration test for rate limiting — **Requires PostgreSQL**
- [ ] 13.7 Integration test for password recovery — **Requires PostgreSQL**
- [ ] 13.8 Integration test for `GET /api/auth/me` — **Requires PostgreSQL**
- [ ] 13.9 Integration test for TOTP 2FA flow — **Requires PostgreSQL**
- [ ] 13.10 Integration test for `require_permission` — **Requires PostgreSQL**

> **Note**: Integration tests (13.3–13.10) require a running PostgreSQL database with a seeded test schema.
> Unit tests for security (hashing, JWT, rate limiter, permissions) are fully implemented and passing (49 tests).
