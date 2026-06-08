# Tasks: C-01 — Foundation Setup

## Phase 1: Project Root + Backend Config

- [x] 1.1 Create `.gitignore` (Python + Node + IDE), `.env.example` (all vars documented), `.pre-commit-config.yaml` (ruff + eslint)
- [x] 1.2 Create `backend/requirements.txt`, `backend/requirements-dev.txt` with pinned deps, `pyproject.toml`
- [x] 1.3 Create all `__init__.py` files: `backend/app/`, `api/`, `api/v1/`, `api/v1/routers/`, `core/`, `models/`, `schemas/`, `repositories/`, `services/`, `integrations/`, `workers/`

## Phase 2: Core Backend Implementation

- [x] 2.1 `[TDD]` Create `core/config.py` (Settings via pydantic-settings) + test verifying `.env` defaults
- [x] 2.2 `[TDD]` Create `core/logging.py` (JSONFormatter) + test verifying JSON output shape
- [x] 2.3 `[TDD]` Create `core/database.py` (async engine + async_sessionmaker) + connection test
- [x] 2.4 Create `models/base.py` + `models/mixins.py` — `AppModel` (UUID PK, snake_case tablename), `TimestampMixin`, `SoftDeleteMixin`, `TenantMixin`
- [x] 2.5 Create `schemas/base.py` (`BaseSchema` with `extra='forbid'`) + `schemas/health.py` (`HealthResponse`)
- [x] 2.6 `[TDD]` Create `api/v1/routers/health.py`, `core/exceptions.py`, `app/main.py` (lifespan, mount health) + test `GET /api/health` → 200 `{status, version}`
- [x] 2.7 Create `core/dependencies.py` (`get_db` stub) + `core/security.py` (AES encrypt/decrypt stubs)

## Phase 3: Frontend Scaffold

- [x] 3.1 Init Vite project (`react-ts` template): `package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `postcss.config.js`, `index.html`; proxy `/api` → backend
- [x] 3.2 Create `src/main.tsx`, `src/App.tsx`, `src/shared/services/api.ts` (Axios instance with JWT interceptor stubs)
- [x] 3.3 Create feature skeleton: `features/auth/{components,hooks,services,types,pages}/`

## Phase 4: Infrastructure (Docker + CI + Alembic)

- [x] 4.1 Init Alembic: `alembic.ini`, `alembic/env.py` (async), `alembic/script.py.mako`
- [x] 4.2 Create `backend/Dockerfile` (multi-stage: builder → runtime + venv), `frontend/Dockerfile` (Nginx alpine), `frontend/nginx.conf` (SPA fallback)
- [x] 4.3 Create `docker-compose.yml`: services `app` (backend), `db` (postgres:16, healthcheck), `n8n` (placeholder, image)
- [x] 4.4 Create `.github/workflows/ci.yml` — parallel jobs: backend-lint (ruff), backend-test (pytest), frontend-lint (eslint), frontend-build (Vite build)
