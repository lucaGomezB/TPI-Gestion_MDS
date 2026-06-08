# Design: C-01 — Foundation Setup

## Technical Approach

Scaffold the entire project substrate in a single additive pass: backend layer structure with a FastAPI app exposing `GET /api/health`, a Vite+React frontend skeleton, Docker compose for local development with PostgreSQL 16 + n8n placeholder, and GitHub Actions CI. No business logic — only wiring, config, and directory conventions.

The design follows the directory layout defined in `docs/ARQUITECTURA.md` §4 and the Clean Architecture flow: `Routers → Services → Repositories → Models → PostgreSQL`.

---

## Architecture Decisions

| Decision | Options | Tradeoff | Chosen |
|----------|---------|----------|--------|
| **Package manager** | poetry vs pip+venv vs uv | Poetry locks deterministically and is the Python industry standard for publishable packages; pip+venv is lighter but lacks lock guarantees; uv is faster but newer | **pip + requirements.txt** — simpler for a containerized app, no need for publishable packages |
| **Async SQLAlchemy** | sync vs async SQLAlchemy 2.0 | Async matches FastAPI's async nature, avoids thread pool blocking, and is the project's chosen ORM mode per ARQUITECTURA.md | **AsyncSession** with `async_sessionmaker` |
| **Logger** | structlog vs stdlib + JSON formatter | structlog is richer (context binding, processors) but adds a dependency; stdlib + custom JSON formatter is zero-dependency and sufficient for structured logs | **stdlib `logging` + custom JSONFormatter** — lightweight, meets the JSON logs requirement without extra deps |
| **Frontend bundler** | Vite vs CRA vs Next.js | Vite is faster (esbuild dev, Rollup prod), CRA is deprecated upstream, Next.js is overkill for an SPA that doesn't need SSR | **Vite** with `react-ts` template |
| **Testing framework** | pytest vs unittest | Pytest is the FastAPI ecosystem standard, has fixture injection, async support via `pytest-asyncio`, and is already mandated in the stack | **pytest** + pytest-asyncio + httpx (for TestClient) |
| **Docker base image** | slim vs alpine vs full python | Alpine breaks many manylinux wheels (encryption libs); slim is Debian-based, smaller than full, compatible with all wheels | **python:3.13-slim** — smallest compatible with native deps |
| **Multi-stage Docker** | single-stage vs multi-stage | Multi-stage separates build deps from runtime image, reducing final image size and attack surface | **Multi-stage** — compile/builder stage, then clean runtime stage |
| **Frontend Docker (prod)** | serve with Nginx vs Vite preview | Nginx is production-grade (static serving, compression, reverse proxy), Vite preview is development-only | **Nginx** (alpine) serving built static files |
| **CI parallelism** | sequential jobs vs matrix vs separate jobs | Matrix (one job matrix per stack) is DRY but adds yaml complexity; separate named jobs are clearer for a two-stack project | **Separate jobs** — `backend-lint`, `backend-test`, `frontend-lint`, `frontend-test` running in parallel |

---

## File Changes

All paths are relative to project root. Every file listed below is **Create** — nothing is modified (first change in the project).

```
project-root/
├── backend/
│   ├── Dockerfile                    # Multi-stage: builder → runtime
│   ├── requirements.txt              # Pinned deps: fastapi, uvicorn, sqlalchemy, asyncpg, alembic, pydantic-settings, httpx, pytest
│   ├── requirements-dev.txt          # Dev deps: ruff, pytest, pytest-asyncio, pytest-cov
│   ├── alembic/
│   │   ├── env.py                    # Alembic env
│   │   └── script.py.mako           # Migration template
│   ├── alembic.ini                   # Alembic config
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app: lifespan, exception handlers, mount health router
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       └── routers/
│   │   │           ├── __init__.py
│   │   │           └── health.py     # GET /api/health → {"status":"ok","version":"0.1.0"}
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Settings via pydantic-settings (DATABASE_URL, SECRET_KEY, ENCRYPTION_KEY, etc.)
│   │   │   ├── database.py           # Async engine + async_sessionmaker
│   │   │   ├── logging.py            # JSONFormatter for structured logs
│   │   │   ├── dependencies.py       # Placeholder: get_db session DI
│   │   │   ├── exceptions.py         # Standard HTTP exception handlers (400, 401, 403, 404, 500)
│   │   │   └── security.py           # Placeholder: AES encrypt/decrypt stubs
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # AppModel, TimestampMixin (created_at, updated_at, deleted_at, is_active)
│   │   │   └── mixins.py             # TenantMixin (tenant_id), SoftDeleteMixin
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # BaseSchema with extra='forbid', HealthResponse
│   │   │   └── health.py             # Health response schema
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   └── base.py               # BaseRepository[T] stub with tenant scope placeholder
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── __init__.py           # (empty, placeholder)
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   └── __init__.py           # (empty, placeholder)
│   │   └── workers/
│   │       └── __init__.py           # (empty, placeholder)
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py               # pytest fixtures: test client, test db session
│       └── test_health.py            # Test GET /api/health returns 200 + expected body
├── frontend/
│   ├── Dockerfile                    # Nginx serving built static files
│   ├── nginx.conf                    # Nginx config with SPA routing
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts                # Proxy /api → backend, react plugin
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx                  # React entry point
│   │   ├── App.tsx                   # Router placeholder
│   │   ├── features/
│   │   │   └── auth/                 # Placeholder feature module
│   │   │       ├── components/
│   │   │       ├── hooks/
│   │   │       ├── services/
│   │   │       ├── types/
│   │   │       └── pages/
│   │   └── shared/
│   │       ├── services/
│   │       │   └── api.ts            # Axios instance with interceptors (JWT placeholder)
│   │       ├── components/
│   │       └── hooks/
│   └── tests/                        # Vitest tests placeholder
│       └── example.test.ts
├── docker-compose.yml                # Services: app (backend), db (postgres:16), n8n (placeholder)
├── .env.example                      # All env vars with documented defaults
├── .gitignore                        # Python + Node + IDE ignores
├── .pre-commit-config.yaml           # ruff + eslint hooks
└── .github/workflows/
    └── ci.yml                        # Parallel jobs: backend lint, backend test, frontend lint, frontend build
```

Key directories with **`__init__.py`** files: every Python package under `backend/app/` needs one (including empty sub-packages like `integrations/`, `workers/`, `services/`).

---

## Interfaces / Contracts

### Health Endpoint

```
GET /api/health
Accept: application/json
---
200 OK
{
  "status": "ok",
  "version": "0.1.0"
}
```

### Pydantic Settings (`core/config.py`)

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `DATABASE_URL` | `PostgresDsn` | `postgresql+asyncpg://postgres:postgres@db:5432/activia` | Async PG connection |
| `SECRET_KEY` | `str` | — | JWT signing key (≥32 chars) |
| `ENCRYPTION_KEY` | `str` | — | AES-256 key (exactly 32 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `15` | JWT access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `int` | `7` | Refresh token TTL |
| `ENVIRONMENT` | `str` | `development` | Runtime env label |
| `LOG_LEVEL` | `str` | `INFO` | Logging threshold |
| `CORS_ORIGINS` | `list[str]` | `["http://localhost:5173"]` | Allowed CORS origins |

### Base ORM Model (`models/base.py`)

- `AppModel`: declarative base with `__tablename__` auto-generation (snake_case plural)
- `TimestampMixin`: `created_at: datetime` (server_default now), `updated_at: datetime` (onupdate now)
- `SoftDeleteMixin`: `deleted_at: datetime | None`, `is_active: bool` (default True)
- `TenantMixin`: `tenant_id: uuid.UUID | None` (FK to `tenants` — FK placeholder, no model yet)
- All models use UUID primary keys with `server_default=text("gen_random_uuid()")`

---

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Health endpoint | `httpx.AsyncClient` with FastAPI `TestClient`, verify 200 + body shape |
| Unit | Settings loading | Verify `.env.example` values are used as defaults |
| Unit | JSON logger | Verify log output is valid JSON with expected keys |
| Integration | DB session factory | Verify engine connects (requires running PG — use fixture) |

---

## Migration / Rollout

No data migration required. This is purely additive (files + config). Rollback: delete the created directories and config files.

---

## Open Questions

None. All decisions documented in ADRs above. Specs and tasks can proceed.
