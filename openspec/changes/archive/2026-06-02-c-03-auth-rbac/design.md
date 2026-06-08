## Context

El sistema tiene identidades (modelo `Usuario`) pero ningún mecanismo de autenticación o autorización. Todo endpoint protegido requiere JWT + RBAC antes de construir funcionalidad de dominio. El modelo `Usuario` actual no tiene `password_hash`, y no existen tablas de roles, asignaciones ni refresh tokens.

**Current state:** Migration 001 (tenants + usuarios). Seed con tenant TUPAD + admin user. Sin contraseña ni roles.
**Governance level:** CRITICAL — cada decisión de seguridad impacta la integridad del sistema.

---

## Goals

- Autenticación stateless via JWT (access 15 min) + refresh token rotation (7 days)
- Password hashing con Argon2id (OWASP recomendado)
- 7 roles RBAC con matriz de permisos `modulo:accion`
- Rate limiting 5/60s por IP+email en login
- 2FA TOTP opcional por usuario
- Password recovery (token de un solo uso, 1 hora de vigencia)
- Endpoints: login, refresh, logout, forgot-password, reset-password, me

## Non-Goals

- **Impersonación** — cambio futuro (requiere auditoría dedicada, permiso `impersonacion:usar`)
- **UI de gestión de roles** — cambio futuro
- **Catálogo de permisos administrable por tenant** — cambio futuro (C-10+). Para MVP se hardcodea la matriz en Python
- **Redis para rate limiting** — cambio futuro. MVP usa diccionario en memoria (se pierde al reiniciar, aceptable)
- **Moodle SSO / OAuth2** — excluido por ADR-001. Auth propio para MVP

---

## Decisions

### D-01: Argon2id para password hashing

| Criterio | Decisión |
|----------|----------|
| Algoritmo | Argon2id (OWASP recommended, resistente a side-channel y GPU) |
| Librería | `argon2-cffi` (binding nativo C, maduro, soporte Python 3.13) |
| Parámetros | `memory_cost=19456` (19 MiB), `time_cost=2`, `parallelism=1` |
| Almacenamiento | String codificado PHC format (`$argon2id$v=19$...`) en columna `password_hash VARCHAR(255)` |

**Alternativa descartada:** bcrypt — no hay razón técnica para preferirlo sobre Argon2id. scrypt — buena alternativa pero menos soporte en ecosistema Python.

### D-02: PyJWT con HS256

| Criterio | Decisión |
|----------|----------|
| Librería | `PyJWT` (mantenida activamente, API simple) |
| Algoritmo | HS256 (HMAC-SHA256) con `SECRET_KEY` (mín. 32 chars) |
| Payload | `sub` (UUID usuario), `tenant_id`, `roles` (lista strings), `exp`, `iat`, `jti` (UUID) |

**NO** se incluyen permisos en el token — reduce tamaño y permite cambiar permisos sin re-login.

**Alternativa descartada:** `python-jose` — no mantenida desde 2021. RS256 — innecesario para MVP single-service, se migrará cuando haya múltiples servicios.

### D-03: Refresh token rotation con token family

- Opaque tokens: 32 bytes random de `os.urandom()`, codificados en hex (64 chars)
- SHA-256 del token almacenado en DB (nunca el token plano)
- Cada refresh: old token revoked, nuevo token emitido (misma familia)
- **Detección de robo:** si se usa un token ya revocado, se revocan TODOS los tokens de esa familia (el atacante o el usuario legítimo perdió el token)
- Expiry: 7 días (configurable vía `REFRESH_TOKEN_EXPIRE_DAYS`)
- Columna `token_family` (UUID) agrupa tokens de una misma sesión original

### D-04: TOTP 2FA flow

- Librería: `pyotp` (estándar, implementación TOTP RFC 6238)
- Secret almacenado cifrado en `totp_secret` (via `EncryptedString`)
- Columna `totp_enabled: Boolean(default=False)` controla si el usuario tiene 2FA activo
- **Login flow con 2FA:**
  1. POST `/api/auth/login` con email+password → si `totp_enabled=true`, devuelve `{"requires_2fa": true, "temp_token": "..."}` con HTTP 202
  2. Posteriormente POST `/api/auth/login/totp` con `temp_token` + `totp_code` → devuelve access + refresh tokens
- `temp_token`: JWT de vida muy corta (2 min), con `sub` + `purpose: "totp_verification"`, FIRMADO con misma SECRET_KEY
- Sin 2FA: login normal devuelve tokens directamente

### D-05: Rate limiting in-memory

- Estructura: `dict[str, list[float]]` clave = `"{ip}:{email_hash}"`, valor = timestamps de intentos
- Ventana deslizante de 60 segundos, máximo 5 intentos
- Se resetea al hacer login exitoso
- Implementado como FastAPI dependency (`check_login_rate_limit`)
- **Limitación:** no sobrevive restart del proceso — aceptable para MVP. En producción se migrará a Redis

### D-06: RBAC — matriz hardcodeada en Python (MVP)

- `core/permissions.py` define `ROL_PERMISSIONS: dict[str, set[str]]` con la matriz completa
- `require_permission("modulo:accion")` → Factory que retorna una FastAPI dependency
- La dependency extrae `roles` del JWT decodeado, recorre cada rol y busca el permiso en la matriz
- 403 si ningún rol del usuario tiene el permiso solicitado
- **Intencional para MVP:** la KB dice que la matriz debe ser administrable como datos. Se hará en un change futuro (C-10+) cuando exista UI de gestión

### D-07: Modelos nuevos

| Modelo | Propósito | Columnas clave |
|--------|-----------|----------------|
| `Rol` | Catálogo de roles por tenant | `id`, `nombre` (unique per tenant), `descripcion`, `permisos` (JSONB), `tenant_id` |
| `UsuarioRol` | Asignación rol ↔ usuario con vigencia | `id`, `usuario_id` (FK), `rol_id` (FK), `tenant_id`, `vigencia_desde`, `vigencia_hasta` |
| `RefreshToken` | Tokens de refresco con rotation | `id`, `usuario_id` (FK), `token_hash`, `expires_at`, `revoked_at`, `token_family`, `tenant_id` |

Usuario existente gana: `password_hash` (String(255), nullable para migración), `totp_secret` (EncryptedString, nullable), `totp_enabled` (Boolean, default=False).

### D-08: Password recovery flow

1. POST `/api/auth/forgot-password` con email → genera token aleatorio (32 bytes hex), lo guarda en tabla `password_reset_tokens` con expiry 1 hora. En MVP: devuelve token en respuesta (sin email configurado aún)
2. POST `/api/auth/reset-password` con `token` + `new_password` → valida token, hashea nueva password, actualiza usuario, invalida token
3. Token de un solo uso: se marca como usado (columna `used_at`)

### D-09: Identity resolution

- El `tenant_id` se resuelve **exclusivamente del JWT**, nunca de parámetros de request
- El endpoint `GET /api/auth/me` extrae `sub` del JWT y consulta el usuario completo
- Toda consulta posterior a dominio filtra por `tenant_id` del JWT via `BaseRepository`

---

## Migration 002: Auth schema

```sql
-- New columns on usuarios
ALTER TABLE usuarios ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE usuarios ADD COLUMN totp_secret TEXT;  -- encrypted, nullable
ALTER TABLE usuarios ADD COLUMN totp_enabled BOOLEAN NOT NULL DEFAULT false;

-- Roles catalog
CREATE TABLE roles (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    nombre VARCHAR(50) NOT NULL,
    descripcion VARCHAR(255),
    permisos JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, nombre)
);

-- User-role assignments
CREATE TABLE usuario_roles (
    id UUID PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    rol_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    vigencia_desde TIMESTAMPTZ,
    vigencia_hasta TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(usuario_id, rol_id)
);

-- Refresh tokens (for rotation + theft detection)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token_hash VARCHAR(64) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    token_family UUID NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens(token_hash);
CREATE INDEX ix_refresh_tokens_token_family ON refresh_tokens(token_family);
```

---

## Risks / Trade-offs

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Token reuse detection falsa (rollback DB) | Baja | En 2FA flow, gracia de 5 min antes de revocar toda la familia |
| Rate limit in-memory perdido al reiniciar | Media | Aceptable para MVP. El reintento post-restart es válido |
| Argon2id params muy lentos en hardware limitado | Baja | `time_cost=2` es conservador. Ajustable via settings en futuro |
| Permisos hardcodeados requieren deploy para cambios | Alta | Intencional para MVP. Se migrará a data-driven en C-10+ |
| Password reset sin email real | Alta | MVP retorna el token en la respuesta. La integración con email es cambio futuro |

---

## Open Questions

1. ¿Se necesita `NEXO` en la matriz desde el inicio? — Sí, está en la KB como uno de los 7 roles. Su matriz de permisos es la más acotada.

---

## Architecture Flow

```
POST /api/auth/login
  → check_login_rate_limit(ip, email_hash)
  → UsuarioRepository.find_by_email(email)  # via email_hash
  → verify_password(plain, hash)
  → [if totp_enabled] return temp_token
  → create JWT access (15 min) + refresh token (7 days)
  → store refresh token hash in DB
  → return {access_token, refresh_token, token_type}

POST /api/auth/refresh
  → validate refresh token (not revoked, not expired)
  → revoke old token
  → issue new access + refresh (same family)
  → [if old token was already revoked] revoke entire family
  → return new tokens

POST /api/auth/login/totp
  → validate temp_token (2 min expiry, purpose=totp_verification)
  → verify TOTP code against user's secret
  → issue JWT + refresh tokens
```

```
Ruta protegida
  → get_current_user (JWT dependency)
      → decode JWT, extract sub, tenant_id, roles
      → verify JWT signature + expiry
      → return Usuario from DB (or cached)
  → require_permission("modulo:accion")
      → get roles from current_user
      → check ROL_PERMISSIONS[any_role] has "modulo:accion"
      → 403 if not found
  → router handler
```
