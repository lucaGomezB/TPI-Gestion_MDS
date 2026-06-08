## 1. Permission Matrix Update

- [x] 1.1 Add `comunicacion:enviar` permission to PROFESOR, COORDINADOR, and ADMIN roles in `core/permissions.py`
- [x] 1.2 Add `comunicacion:aprobar` permission to COORDINADOR and ADMIN roles in `core/permissions.py`
- [x] 1.3 Add SMTP and worker configuration settings to `core/config.py`: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS, SMTP_FROM_EMAIL, SMTP_FROM_NAME, WORKER_POLL_INTERVAL, WORKER_MAX_RETRIES

## 2. Model Layer

- [x] 2.1 Create `EstadoComunicacion` and `EstadoLote` enums in `models/comunicacion.py` with all states per RN-15 and design D-02
- [x] 2.2 Create `Comunicacion` model in `models/comunicacion.py`
- [x] 2.3 Create `LoteComunicacion` model in `models/comunicacion.py`
- [x] 2.4 Update `models/__init__.py` to export `Comunicacion`, `LoteComunicacion`, `EstadoComunicacion`, `EstadoLote`

## 3. Pydantic Schemas

- [x] 3.1 Create `schemas/communication.py` with all schemas (all with `extra='forbid'`)

## 4. Migration 008 — Comunicaciones Schema

- [x] 4.1 Generate Alembic migration (revision 008, depends_on revision `d4e5f6a7b8c9`)
- [x] 4.2 Implement `downgrade()` — DROP TABLE comunicaciones, DROP TABLE lotes_comunicaciones

## 5. Repository Layer

- [x] 5.1 Create `repositories/communication.py` with `ComunicacionRepository`
- [x] 5.2 Create `repositories/communication.py` with `LoteRepository`
- [x] 5.3 Export `ComunicacionRepository` and `LoteRepository` from `repositories/__init__.py`

## 6. Template Engine

- [x] 6.1 Create `services/template_engine.py` with `render_template` and `build_preview_context`

## 7. Email Sender

- [x] 7.1 Create `services/email_sender.py` with `send_email` and typed exceptions

## 8. Service Layer

- [x] 8.1 Create `services/communication.py` with full business logic
- [x] 8.2 Create helper functions in `services/communication.py`: `_mask_email`, `_check_materia_access`, `_get_tenant_approval_config`
- [x] 8.3 Export all service functions from `services/__init__.py`

## 9. Router Layer

- [x] 9.1 Create `api/v1/routers/communication.py` with all 6 endpoints
- [x] 9.2 `POST /preview` and `POST /enviar` protected with `require_permission("comunicacion:enviar")`
- [x] 9.3 `PUT /aprobar` protected with `require_permission("comunicacion:aprobar")`
- [x] 9.4 All endpoints inject `get_current_user` dependency for tenant resolution
- [x] 9.5 PROFESOR scope enforcement: materia access verified via Asignacion/equipo membership
- [x] 9.6 Register `communication` router in `api/v1/routers/__init__.py`
- [x] 9.7 Wire the new router into `main.py`

## 10. Async Worker

- [x] 10.1 `workers/__init__.py` already exists with module initialization
- [x] 10.2 Create `workers/communication_worker.py` with full worker logic
- [x] 10.3 Add worker entry point script `run_worker.py`

## 11. Tenant Config Update

- [x] 11.1 Tenant already has `configuracion` JSONB field — `requiere_aprobacion_masiva` read from there
- [x] 11.2 Default value is `false` via `.get()` pattern in service
- [x] 11.3 `_get_tenant_approval_config` helper in CommunicationService reads from Tenant.configuracion

## 12. Docker/Infrastructure

- [x] 12.1 Add worker service to `docker-compose.yml`
- [x] 12.2 Update `Dockerfile` to include `run_worker.py`

## 13. Tests — Unit

- [x] 13.1 Unit test for `render_template` — covered in `tests/services/test_template_engine.py` (11 tests)
- [x] 13.2 Unit test for `_mask_email` — covered in `tests/services/test_email_sender.py` (7 tests)
- [x] 13.3 Unit test for `_compute_estado_vigencia` logic — already exists in `tests/schemas/test_team_management.py` (8 tests from C-05)
- [x] 13.4 Unit test for schema validation — covered in `tests/schemas/test_communication.py` (21 tests)
- [x] 13.5 Unit test for permission matrix — covered in `tests/core/test_permissions.py::TestCommunicationPermissions` (12 tests)
- [x] 13.6 Unit test for `EstadoComunicacion` enum transition logic — covered in `tests/models/test_comunicacion_enums.py` (13 tests)

## 14. Tests — Integration

- [x] 14.1 Integration test for preview endpoint — `test_preview_success`
- [x] 14.2 Integration test for preview without access (403) — `test_preview_without_access_403`
- [x] 14.3 Integration test for enqueue with preview_confirmado=true (201) — `test_enqueue_success`
- [x] 14.4 Integration test for enqueue without preview_confirmado (400) — `test_enqueue_without_preview_confirmado_400`
- [x] 14.5 Integration test for GET lotes list — `test_list_lotes`
- [x] 14.6 Integration test for approval flow — approve — `test_approval_flow_approve`
- [x] 14.7 Integration test for approval flow — reject — `test_approval_flow_reject`
- [x] 14.8 Integration test for approve without permission (403) — `test_approve_without_permission_403`
- [x] 14.9 Integration test for worker processing — `test_worker_process_lote`
- [x] 14.10 Integration test for cancellation — `test_cancel_comunicacion`
- [x] 14.11 Integration test for multi-tenant isolation — `test_multi_tenant_isolation`
- [x] 14.12 Integration test for unauthenticated (401) — 4 tests: `test_unauthenticated_preview_401`, `test_unauthenticated_enviar_401`, `test_unauthenticated_list_401`, `test_unauthenticated_aprobar_401`
- [x] 14.13 Integration test for PROFESOR scope enforcement — `test_profesor_scope_enforcement`
