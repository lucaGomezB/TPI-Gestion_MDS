## 1. Models and Migration

- [x] 1.1 Create `HiloMensaje` model in `backend/app/models/hilo_mensaje.py` with fields: id, tenant_id, asunto, participantes (JSONB), created_at, updated_at
- [x] 1.2 Create `Mensaje` model in `backend/app/models/mensaje.py` with fields: id, tenant_id, hilo_id (FK HiloMensaje), remitente_id (FK Usuario), destinatario_id (FK Usuario), asunto, cuerpo, leido (bool), created_at, updated_at
- [x] 1.3 Create `MensajeEliminado` model in `backend/app/models/mensaje_eliminado.py` for per-user soft-delete tracking with fields: id, mensaje_id (FK Mensaje), usuario_id (FK Usuario), created_at
- [x] 1.4 Register models in `backend/app/models/__init__.py`
- [x] 1.5 Generate Alembic migration for new tables with indices: `(destinatario_id, leido, tenant_id)`, `(hilo_id)`, `(remitente_id, destinatario_id)`

## 2. Repository

- [x] 2.1 Create `MensajeRepository` in `backend/app/repositories/mensaje.py` extending `BaseRepository[Mensaje]`
- [x] 2.2 Implement `list_inbox(usuario_id, limit, offset)` returning paginated thread summaries with unread count per thread
- [x] 2.3 Implement `get_thread(hilo_id, usuario_id)` returning all messages in a thread, filtered by per-user deletions
- [x] 2.4 Implement `get_or_create_hilo(tenant_id, remitente_id, destinatario_id, asunto)` for thread dedup
- [x] 2.5 Implement `mark_as_read(hilo_id, usuario_id)` to set leido=true for messages where destinatario_id matches
- [x] 2.6 Implement `count_no_leidos(usuario_id)` for unread count
- [x] 2.7 Implement `soft_delete_for_user(mensaje_id, usuario_id)` creating MensajeEliminado record
- [x] 2.8 Implement `find_or_create_hilo(tenant_id, participantes, asunto)` for thread lookup/reuse

## 3. Unit of Work

- [x] 3.1 Import `MensajeRepository` in `backend/app/core/unit_of_work.py`
- [x] 3.2 Add `mensaje` property to `UnitOfWork` class

## 4. Schemas

- [x] 4.1 Create `backend/app/schemas/mensaje.py` with Pydantic schemas:
  - `MensajeCreate` (destinatario_id, asunto, cuerpo) with `extra='forbid'`
  - `MensajeResponder` (cuerpo) with `extra='forbid'`
  - `MensajeResponse` (id, hilo_id, remitente_id, destinatario_id, asunto, cuerpo, leido, created_at)
  - `HiloResponse` (hilo_id, asunto, participantes, mensajes: list[MensajeResponse])
  - `InboxItemResponse` (hilo_id, asunto, ultimo_mensaje, ultima_fecha, remitente_nombre, no_leidos)
  - `InboxResponse` (data: list[InboxItemResponse], total, limit, offset)
  - `MensajeCreatedResponse` (id, hilo_id, asunto, created_at)
  - `NoLeidosResponse` (count: int)

## 5. Service

- [x] 5.1 Create `MensajeService` in `backend/app/services/mensajeria.py` accepting `uow: UnitOfWork` and `current_user: dict`
- [x] 5.2 Implement `enviar(data: MensajeCreate) -> MensajeCreatedResponse` with tenant validation, permission check, and thread creation/reuse
- [x] 5.3 Implement `responder(mensaje_id: str, data: MensajeResponder) -> MensajeCreatedResponse` with participant validation
- [x] 5.4 Implement `listar_inbox(limit: int, offset: int) -> InboxResponse`
- [x] 5.5 Implement `ver_hilo(mensaje_id: str) -> HiloResponse` with auto-mark-read logic
- [x] 5.6 Implement `contar_no_leidos() -> NoLeidosResponse`

## 6. Router

- [x] 6.1 Create `backend/app/api/v1/routers/mensajeria.py` with endpoints:
  - `GET /api/mensajes` — listar inbox (require auth)
  - `GET /api/mensajes/{id}` — ver hilo (require auth)
  - `POST /api/mensajes` — enviar mensaje (require permission `mensajeria:enviar`)
  - `POST /api/mensajes/{id}/responder` — responder (require auth)
  - `GET /api/mensajes/no-leidos` — contador (require auth)
- [x] 6.2 Register router in `backend/app/main.py`

## 7. Permissions

- [x] 7.1 Add `mensajeria:enviar` permission to the permission catalog in `backend/app/core/permissions.py`
- [x] 7.2 Assign `mensajeria:enviar` to roles TUTOR, PROFESOR, COORDINADOR, ADMIN in ROL_PERMISSIONS matrix

## 8. Tests

- [x] 8.1 Write tests for `POST /api/mensajes` — send message creates thread, reuses thread, rejects invalid user, rejects cross-tenant, rejects empty body
- [x] 8.2 Write tests for `POST /api/mensajes/{id}/responder` — reply as sender, reply as receiver, rejects non-participant, rejects empty body
- [x] 8.3 Write tests for `GET /api/mensajes` — returns inbox paginated, returns empty for new user, multi-tenant isolation
- [x] 8.4 Write tests for `GET /api/mensajes/{id}` — returns thread ordered, auto-marks-read, rejects non-participant
- [x] 8.5 Write tests for `GET /api/mensajes/no-leidos` — returns correct count, returns zero, multi-tenant isolation
