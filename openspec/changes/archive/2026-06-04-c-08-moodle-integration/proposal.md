## Why

The system ingests academic data (grades, enrollment, user profiles) from Moodle, the institution's LMS. Currently there is no integration mechanism — all data would require manual upload. The PRD mandates (RF-06) automatic sync via Moodle Web Services (nocturnal + on-demand), with fallback manual import (RF-07) for tenants without WS access or for historical loads. Without this change, the core ingestion pipeline of the product (Epic 1 — Ingesta de Datos desde el LMS) cannot operate.

## What Changes

- Create `integrations/moodle_ws.py` — abstract client for Moodle Web Services API, isolated from core business logic
- Implement Moodle WS functions: `core_grades_get_grades` (grades per activity), `core_enrol_get_enrolled_users` (enrolled students), `core_user_get_users` (user profiles), `gradereport_user_get_grade_items` (activity catalog)
- Create sync engine service coordinating WS calls → domain model mapping → persistence
- Add scheduled nocturnal sync via async worker (background job)
- Add on-demand sync endpoint: `POST /api/v1/materias/{dictado_id}/sync-moodle` (triggers sync for a single dictado)
- Add fallback manual import service for `.xlsx`/`.csv` files (grades and enrollment roster), with preview step (F1.1–F1.4)
- Add per-tenant encrypted configuration for Moodle WS credentials (`MOODLE_WS_URL`, `MOODLE_WS_TOKEN`) stored in tenant settings (JSONB), AES-256 encrypted
- Add migration 005 to add `config_moodle` column to `tenants` table (JSONB with encrypted fields)
- Add `calificaciones:importar` permission check on sync endpoints (PROFESOR scope by dictado, COORDINADOR scope by tenant)
- Error handling: Moodle WS errors → HTTP 502 with retry semantic; malformed files → HTTP 400 with detail
- Add `aiohttp` to `requirements.txt` (async HTTP client for Moodle WS)
- Add `openpyxl` to `requirements.txt` (`.xlsx` parsing for manual import)

## Capabilities

### New Capabilities
- `moodle-integration`: Moodle Web Services client (`integrations/moodle_ws.py`), sync engine (nocturnal scheduled + on-demand), per-tenant encrypted WS credential management, domain mapping from WS responses to internal models (grades, enrollment, users)
- `manual-import`: Fallback import pipeline for `.xlsx`/`.csv` files (grades and enrollment roster), with file validation, preview-generation, and confirmed import steps. Replaces WS sync when Moodle access is unavailable or for historical data loads.

### Modified Capabilities
- *(No existing capabilities have spec-level behavioral changes — this change adds new capabilities without altering existing auth or core-model contracts)*

## Impact

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/integrations/moodle_ws.py` | **New** | Abstract Moodle WS client: async HTTP calls, token auth, retry logic, error wrapping |
| `backend/app/services/moodle_sync_service.py` | **New** | Sync orchestration: fetch from WS → map to domain DTOs → persist via repositories |
| `backend/app/services/manual_import_service.py` | **New** | File parsing (xlsx/csv), validation, preview generation, confirmed import |
| `backend/app/workers/moodle_sync_worker.py` | **New** | Scheduled background job for nocturnal sync |
| `backend/app/api/v1/routers/moodle_sync.py` | **New** | Endpoints: `POST /api/v1/materias/{dictado_id}/sync-moodle`, `POST /api/v1/materias/{dictado_id}/import` |
| `backend/app/models/tenant.py` | Modified | Add `config_moodle` JSONB column for encrypted per-tenant Moodle settings |
| `backend/app/schemas/moodle.py` | **New** | Pydantic schemas for Moodle WS responses, sync request/response DTOs |
| `backend/app/repositories/moodle_sync_repository.py` | **New** | Repository for grade/enrollment persistence during sync |
| `backend/alembic/versions/` | **New** | Migration 005: `config_moodle` column on tenants |
| `backend/requirements.txt` | Modified | Add `aiohttp`, `openpyxl` |
| `backend/app/core/config.py` | Modified | Add `MOODLE_SYNC_HOUR` (default 03:00), `MOODLE_REQUEST_TIMEOUT` settings |
