## Why

The system has academic structure (C-04), user identity with RBAC (C-03), and role assignments (C-05), but there is no way to send email communications to students. Teachers and coordinators need to communicate with students via email — individual or bulk — with tracking of delivery status, template-based personalization, and optional administrative approval for mass communications. Without this change, the Epica 3 (Comunicacion) capabilities cannot function, blocking downstream changes C-12 (avisos-tablon) and C-13 (mensajeria-interna).

## What Changes

- Create `Comunicacion` SQLAlchemy model with states Pendiente/Enviando/Enviado/Error/Cancelado (RN-15), tracking `lote_id` for bulk grouping, and email encryption for `destinatario` (PII)
- Create `POST /api/materias/{id}/comunicaciones/preview` — mandatory preview of subject and rendered body before sending (RN-16)
- Create `POST /api/materias/{id}/comunicaciones/enviar` — enqueue bulk communication with optional approval flow (RN-17)
- Create `GET /api/materias/{id}/comunicaciones` — real-time status tracking per lote or individual
- Create `PUT /api/admin/comunicaciones/{id}/aprobar` — approve/reject bulk communications requiring authorization (RN-17)
- Create worker async loop: processes Pendiente queue → sends email → marks Enviado/Error with configurable retries
- Create template engine supporting variables `{{alumno.nombre}}`, `{{materia.nombre}}` (RF-20) for body and subject personalization
- Create `LoteComunicacion` model to group bulk sends under a single batch with summary metadata (total, sent, failed, status)
- Permission guards: `comunicacion:enviar` for PROFESOR/COORDINADOR/ADMIN, `comunicacion:aprobar` for COORDINADOR/ADMIN
- Migration 007: tables `comunicaciones`, `lotes_comunicaciones` with indexes for querying by tenant, lote, estado, and materia
- Tests: lifecycle (Pendiente → Enviando → OK/Fail), preview rendering, template substitution, approval flow, multi-tenant isolation, permission enforcement

## Capabilities

### New Capabilities
- `communication-queue`: Full communication queue with states, async worker processing, bulk lote grouping, email sending, and real-time status tracking. Includes mandatory preview before send (RN-16), configurable retry on failure, and PII encryption for recipient addresses.

### Modified Capabilities

<!-- No existing capabilities change their requirements — the communication-queue capability is additive. -->

## Impact

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/comunicacion.py` | **New** | `Comunicacion` model: id, tenant_id, enviado_por (FK Usuario), materia_id (FK Materia), destinatario (cifrado), asunto, cuerpo, estado (enum), lote_id (FK LoteComunicacion), enviado_at (nullable). `LoteComunicacion` model: id, tenant_id, materia_id, enviado_por, total, enviados, fallidos, estado (enum), created_at |
| `backend/app/models/__init__.py` | Modified | Export Comunicacion, LoteComunicacion models |
| `backend/app/schemas/communication.py` | **New** | Pydantic schemas: ComunicacionCreate, ComunicacionResponse, PreviewRequest, PreviewResponse, EnviarRequest, AprobarRequest, LoteResponse. All with `extra='forbid'` |
| `backend/app/repositories/communication.py` | **New** | ComunicacionRepository and LoteRepository with tenant-scoped queries, batch status updates, lote aggregation |
| `backend/app/services/communication.py` | **New** | Service layer: preview rendering, enqueue, approval, status tracking, template rendering |
| `backend/app/services/template_engine.py` | **New** | Template engine: substitute `{{alumno.nombre}}`, `{{materia.nombre}}` variables in subject/body |
| `backend/app/workers/communication_worker.py` | **New** | Async worker loop: processes Pendiente items, sends email via SMTP/Mailgun/etc, updates status with retries |
| `backend/app/api/v1/routers/communication.py` | **New** | Router with endpoints for preview, send, tracking, approval |
| `backend/app/api/v1/routers/__init__.py` | Modified | Register communication router |
| `backend/app/core/permissions.py` | Modified | Add `comunicacion:enviar` and `comunicacion:aprobar` permissions |
| `backend/app/core/config.py` | Modified | Add SMTP/mail configuration + worker interval settings |
| `backend/alembic/versions/` | **New** | Migration 007: comunicaciones + lotes_comunicaciones tables with indexes |
| `backend/tests/` | **New** | Unit + integration tests for lifecycle, preview, template rendering, approval, multi-tenant |
