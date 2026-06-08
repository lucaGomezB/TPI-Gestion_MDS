# Proposal: C-01 — Foundation Setup

## Intent

Sentar las bases del proyecto activia-trace: estructura de directorios, configuración inicial del backend (FastAPI) y frontend (Vite + React), contenedores Docker para desarrollo local, y CI básico. Sin esta base ningún change posterior puede ejecutarse.

## Scope

### In Scope
- `backend/`: estructura de capas vacía (routers, services, repositories, models, core, schemas, integrations, workers), FastAPI app mínima con health check `GET /api/health`, settings con pydantic-settings, logger estructurado JSON, async DB session factory (SQLAlchemy 2.0 async + PostgreSQL)
- `frontend/`: scaffolding Vite + React 18 + TypeScript + Tailwind, Axios configurado con interceptor, estructura feature-based vacía
- `Dockerfile` para backend + `docker-compose.yml` (app, PostgreSQL, n8n placeholder)
- `.env.example` con todas las variables documentadas
- GitHub Actions CI: lint + test + build en paralelo
- Convenciones iniciales: `extra='forbid'` en schemas Pydantic, soft delete flag en modelos base

### Out of Scope
- Modelos de negocio concretos (usuarios, tenants, alumnos) — son changes posteriores (C-02 en adelante)
- Autenticación JWT / Argon2id (C-02)
- Tests unitarios de negocio (se escriben con cada change)
- CI/CD deploy (solo CI por ahora)

## Capabilities

<!-- Foundation change — no new business capabilities, no existing specs to modify -->

### New Capabilities

None. Este change no introduce capacidades de negocio nuevas. Las specs del proyecto comienzan con C-02.

### Modified Capabilities

None. No existen specs previas (primer change del proyecto).

## Approach

1. **Backend**: crear estructura `backend/app/{core,models,schemas,repositories,services,api/v1/routers,integrations,workers}`. App FastAPI con lifespan, health router en `/api/health`, config vía `pydantic-settings`, logger JSON estructurado con structlog o logging estándar + JSON formatter, async engine SQLAlchemy con session factory, base declarativa con `updated_at`/`created_at`/`deleted_at` (soft delete).
2. **Frontend**: `npm create vite@latest` con template React-TS, instalar Tailwind CSS v3, Axios, React Router. Estructura `src/{features,shared/services,shared/components,shared/hooks}`. Axios instance con interceptors placeholder para JWT.
3. **Docker**: Dockerfile multistage para backend, `docker-compose.yml` con servicios `app`, `db` (PostgreSQL 16), `n8n` (imagen oficial, placeholder).
4. **CI**: workflow GitHub Actions con jobs paralelos: lint (ruff/flake8 + eslint), test (pytest placeholder + vitest placeholder), build (Docker build).
5. **Convenciones**: modelo base `AppModel` con soft delete, `TimestampMixin`, Pydantic `BaseSchema` con `extra='forbid'`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/` | New | Full directory structure + app scaffold |
| `frontend/` | New | Full directory structure + Vite scaffold |
| `Dockerfile` | New | Backend container definition |
| `docker-compose.yml` | New | Local dev services |
| `.env.example` | New | Documented env vars |
| `.github/workflows/ci.yml` | New | CI pipeline |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Version conflicts (Python deps, Node deps) | Low | Pin versions in `requirements.txt` / `package.json` |
| PostgreSQL connection in Docker on first run | Low | Health check in compose + retry in app startup |
| Frontend scaffold mismatch with Vite latest | Low | Use `--template react-ts` flag, pin Vite version |

## Rollback Plan

Eliminar los directorios `backend/`, `frontend/`, `.github/` y archivos `Dockerfile`, `docker-compose.yml`, `.env.example`. El change es puramente aditivo — no hay migraciones de datos que revertir.

## Dependencies

- Python 3.13+ instalado localmente (o Docker)
- Node.js 20+ (o Docker)
- Docker + docker-compose v2

## Success Criteria

- [ ] `GET /api/health` devuelve `{"status": "ok"}` con HTTP 200
- [ ] Frontend `npm run dev` inicia servidor de desarrollo sin errores
- [ ] `docker compose up --build` levanta app, db y n8n sin errores
- [ ] CI pipeline ejecuta lint + test + build exitosamente
- [ ] Pydantic schema con `extra='forbid'` rechaza campos extra
