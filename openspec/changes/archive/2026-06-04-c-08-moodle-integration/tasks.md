## 1. Dependencies and Configuration

- [x] 1.1 Add `aiohttp` and `openpyxl` to `backend/requirements.txt`
- [x] 1.2 Add `MOODLE_SYNC_HOUR` (default 3), `MOODLE_REQUEST_TIMEOUT` (default 30) to `Settings` in `core/config.py`
- [x] 1.3 Add `MOODLE_WS_URL`, `MOODLE_WS_TOKEN` to `.env.example` (document per-tenant config pattern)
- [x] 1.4 Verify `ENCRYPTION_KEY` is validated (min 32 chars) in `core/config.py` — needed for Moodle credential encryption

## 2. Moodle WS Client (`integrations/moodle_ws.py`)

- [x] 2.1 Create `MoodleWSClient` class with `aiohttp` session, token auth, configurable timeout
- [x] 2.2 Implement retry logic: 2 retries with exponential backoff (1s, 3s) on 5xx/network errors; no retry on 4xx
- [x] 2.3 Implement `get_grade_items(course_id)` — wraps `gradereport_user_get_grade_items`
- [x] 2.4 Implement `get_grades(course_id)` — wraps `core_grades_get_grades`
- [x] 2.5 Implement `get_enrolled_users(course_id)` — wraps `core_enrol_get_enrolled_users`
- [x] 2.6 Implement `get_users(criteria)` — wraps `core_user_get_users`
- [x] 2.7 Create Pydantic response models: `MoodleGradeResponse`, `MoodleEnrolledUser`, `MoodleUserProfile`, `MoodleGradeItem`, `MoodleGrade`
- [x] 2.8 Create custom exceptions: `MoodleConnectionError`, `MoodleAuthenticationError`, `MoodleServerError`
- [x] 2.9 Export all public types and client from `integrations/__init__.py`

## 3. Per-tenant Moodle Configuration

- [x] 3.1 Add `config_moodle` JSONB column to `Tenant` model (nullable, with typed dict accessor)
- [x] 3.2 Create `schemas/moodle_config.py` with `MoodleConfigSchema` (Pydantic, `extra='forbid'`): `ws_url`, `ws_token`, `ws_enabled`, `moodle_version`
- [x] 3.3 Create `services/moodle_config_service.py`:
  - `get_moodle_config(tenant_id) -> MoodleConfigSchema` — loads + decrypts
  - `set_moodle_config(tenant_id, config) -> None` — encrypts + saves
  - `is_moodle_enabled(tenant_id) -> bool` — quick check
- [x] 3.4 Add AES-256 encryption/decryption helpers in `core/security.py` for dict-level encrypt/decrypt
- [x] 3.5 Create migration 005: add `config_moodle` column to `tenants` table (JSONB, nullable)

## 4. Sync Log Model

- [x] 4.1 Create `models/sync_log.py`: `SyncLog` model with fields: id, tenant_id, dictado_id (nullable), sync_type, status, started_at, finished_at, details (JSONB), error_message, created_at
- [x] 4.2 Create `repositories/sync_log_repository.py`: create entry, update status, list by dictado, list by tenant
- [x] 4.3 Create migration 006: create `sync_log` table with indexes on (tenant_id), (dictado_id), (status)
- [x] 4.4 Export `SyncLog` from `models/__init__.py`

## 5. Sync Engine Service

- [x] 5.1 Create `services/moodle_sync_service.py` with `sync_dictado(tenant_id, dictado_id) -> SyncResult`:
  - Load Moodle config, decrypt credentials
  - Step 1: Fetch grade items from Moodle → map to internal `Actividad` DTOs
  - Step 2: Fetch enrolled users from Moodle → map to internal enrollment DTOs
  - Step 3: Fetch grades from Moodle → map to internal `Calificacion` DTOs
  - Step 4: Persist activities (upsert) via repository
  - Step 5: Persist enrollment (upsert with RN-05 destructive replacement) via repository
  - Step 6: Persist grades (upsert) via repository
  - Step 7: Create sync_log entry with result
- [x] 5.2 Implement granular error handling: each step has its own try/except; partial success creates `status=partial` sync_log entry
- [x] 5.3 Implement lock check: do not start sync if `sync_log` has `status=running` for same dictado
- [x] 5.4 Create `schemas/moodle_sync.py` with `SyncResult`, `SyncStep`, `SyncRequest` Pydantic schemas (all with `extra='forbid'`)

## 6. Sync Repositories

- [x] 6.1 Create `repositories/moodle_sync_repository.py`:
  - `upsert_activities(tenant_id, dictado_id, activities: list[ActividadDTO]) -> int`
  - `upsert_grades(tenant_id, dictado_id, grades: list[CalificacionDTO]) -> int`
  - `upsert_enrollment(tenant_id, dictado_id, student_ids: list[UUID]) -> int` (with RN-05 destructive replacement)
  - `get_dictado_by_moodle_course(tenant_id, moodle_course_id) -> Dictado | None`
  - `get_active_dictados_for_sync(tenant_id) -> list[Dictado]` (dictados with moodle_course_id IS NOT NULL)

## 7. On-demand Sync Endpoint

- [x] 7.1 Create `api/v1/routers/moodle_sync.py`:
  - `POST /api/v1/materias/{dictado_id}/sync-moodle` — trigger on-demand sync
  - Requires `calificaciones:importar` permission; scope: PROFESOR only own dictados, COORDINADOR any tenant dictado
- [x] 7.2 Add sync status endpoint: `GET /api/v1/materias/{dictado_id}/sync-log` — returns recent sync history
- [x] 7.3 Register moodle_sync router in `api/v1/routers/__init__.py`
- [x] 7.4 Wire into main app

## 8. Admin Moodle Config Endpoint

- [x] 8.1 Create `api/v1/routers/admin_moodle.py`:
  - `GET /api/v1/admin/tenants/moodle-config` — get current Moodle config (decrypted values masked)
  - `PUT /api/v1/admin/tenants/moodle-config` — set Moodle config (encrypts before storage)
  - `DELETE /api/v1/admin/tenants/moodle-config` — disable/clear Moodle config
- [x] 8.2 All admin endpoints require `tenant:configurar` permission
- [x] 8.3 Register admin_moodle router

## 9. Scheduled Nocturnal Sync Worker

- [x] 9.1 Create `workers/moodle_sync_worker.py`:
  - Async worker function that runs in background
  - Calculates seconds until next sync hour, sleeps until then
  - Iterates tenants with `ws_enabled=true`, then their dictados with `moodle_course_id IS NOT NULL`
  - Calls `sync_dictado` for each; continues on per-dictado failure
  - Logs summary to application logger
- [x] 9.2 Wire worker startup in `main.py` via `asyncio.create_task` on `lifespan` startup
- [x] 9.3 Add configuration: `MOODLE_SYNC_HOUR` env var (default 3 = 03:00 AM)

## 10. Manual Import Service (Fallback)

- [x] 10.1 Create `services/manual_import_service.py`:
  - `parse_and_preview(file, dictado_id) -> PreviewResult` — parse xlsx/csv, detect grade columns (RN-01), identify students, return preview
  - `confirm_import(dictado_id, activity_ids, session_token) -> ImportResult` — persist selected activities + grades
- [x] 10.2 Implement xlsx parser (openpyxl): detect header row, identify `(Real)` columns, extract student rows
- [x] 10.3 Implement CSV parser: detect separator (comma, semicolon, tab), same detection logic as xlsx
- [x] 10.4 Implement textual scale handling per RN-02: map "Satisfactorio"/"Supera lo esperado" as approved; cross-reference against tenant's scale catalog
- [x] 10.5 Create `schemas/manual_import.py`: `PreviewResult`, `ImportResult`, `ImportConfirmRequest` (all with `extra='forbid'`)
- [x] 10.6 Create `repositories/import_repository.py`: `save_imported_activities`, `save_imported_grades`, `replace_enrollment`

## 11. Manual Import Endpoints

- [x] 11.1 Create `api/v1/routers/manual_import.py`:
  - `POST /api/v1/materias/{dictado_id}/import/preview` — upload file, get preview
  - `POST /api/v1/materias/{dictado_id}/import/confirm` — confirm import with activity selection
- [x] 11.2 Requires `calificaciones:importar` permission; same scope rules as sync
- [x] 11.3 Register manual_import router

## 12. Unit Tests

- [x] 12.1 Unit test for `MoodleWSClient` with mocked HTTP responses:
  - Valid grade fetch response (3 cases: numeric, textual, empty)
  - Authentication error
  - Connection timeout → retry logic
  - Invalid URL
- [x] 12.2 Unit test for `MoodleConfigService` encrypt/decrypt roundtrip (3 cases: valid config, empty config, URL with special chars)
- [x] 12.3 Unit test for manual import parser with sample xlsx/csv files:
  - Valid grade file with `(Real)` columns (2 cases: xlsx, csv)
  - File with no `(Real)` columns → error
  - File with textual scale values (2 cases: approved, not approved per RN-02)
  - Corrupt file → parse error
- [x] 12.4 Unit test for sync engine lock check (2 cases: lock free → proceed, lock held → reject)
- [x] 12.5 Unit test for tenant boundary enforcement (2 cases: same tenant → allowed, different tenant → 404)
- [x] 12.6 Unit test for RBAC permission on sync endpoints (3 cases: has permission, lacks permission, unauthenticated)

## 13. Integration Tests

- [x] 13.1 Integration test for `POST /api/v1/materias/{dictado_id}/sync-moodle` with mocked Moodle WS — **Requires PostgreSQL**
- [x] 13.2 Integration test for on-demand sync with actual file data flow — **Requires PostgreSQL**
- [x] 13.3 Integration test for manual import upload + preview + confirm cycle — **Requires PostgreSQL**
- [x] 13.4 Integration test for tenant boundary: tenant A cannot access tenant B's dictado data — **Requires PostgreSQL**
- [x] 13.5 Integration test for admin Moodle config CRUD endpoints — **Requires PostgreSQL**
- [x] 13.6 Integration test for sync_log creation after successful/failed sync — **Requires PostgreSQL**

(End of file - total 134 lines)
