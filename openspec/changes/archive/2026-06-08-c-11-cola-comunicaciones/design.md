## Context

The system has core identity models (C-02), RBAC authentication (C-03), academic structure (C-04), and role assignments (C-05, archived). The permissions matrix in `core/permissions.py` does not yet include `comunicacion:enviar` or `comunicacion:aprobar`. There is no model for tracking email communications, no async worker for processing outbound email queues, and no template engine for personalizing messages with student/subject data.

The KB defines Comunicacion in [04_modelo_de_datos.md](../../knowledge-base/04_modelo_de_datos.md) (E21), the functional capabilities in [06_funcionalidades.md](../../knowledge-base/06_funcionalidades.md) (Epica 3 — Comunicacion con Alumnos, F3.1-F3.3), and the business rules in [05_reglas_de_negocio.md](../../knowledge-base/05_reglas_de_negocio.md) (RN-15, RN-16, RN-17).

**Current state (C-05):** Migration 004 is the latest. The `app` module has models for Carrera, Cohorte, Materia, Asignacion. No Comunicacion or LoteComunicacion model exists. No async worker infrastructure exists.
**Governance level:** ALTO — this change introduces async processing infrastructure and deals with PII (recipient emails must be encrypted). Approval flows and mandatory previews are safety-critical.

---

## Goals / Non-Goals

**Goals:**
- Create `Comunicacion` SQLAlchemy model with lifecycle states: Pendiente > Enviando > Enviado/Error/Cancelado (RN-15)
- Create `LoteComunicacion` SQLAlchemy model for grouping bulk sends with aggregated status (total, enviados, fallidos, estado)
- Create template engine supporting `{{alumno.nombre}}` and `{{materia.nombre}}` substitution (RF-20)
- Create `POST /api/materias/{id}/comunicaciones/preview` — mandatory preview before sending (RN-16)
- Create `POST /api/materias/{id}/comunicaciones/enviar` — enqueue bulk communication with optional approval flow (RN-17)
- Create `GET /api/materias/{id}/comunicaciones` — real-time status tracking per lote or individual
- Create `PUT /api/admin/comunicaciones/{id}/aprobar` — approve/reject pending bulk communications for COORDINADOR/ADMIN
- Create async worker that processes the queue: reads Pendiente items, sends via SMTP, marks Enviado/Error with configurable retries
- Encrypt `destinatario` field (PII) using existing AES-256 infrastructure from `core/security.py`
- Permission guards: `comunicacion:enviar` for PROFESOR/COORDINADOR/ADMIN, `comunicacion:aprobar` for COORDINADOR/ADMIN
- Migration 007: tables `comunicaciones`, `lotes_comunicaciones` with composite indexes
- Audit logging for all mutating operations (preview, send, approve, reject, cancel)
- Tests: lifecycle transitions, preview rendering, template substitution, approval flow, multi-tenant isolation

**Non-Goals:**
- **UI/Frontend** — API-only change. Frontend comes in a future change (likely C-24 or similar)
- **Moodle integration for sending** — Communications are sent via SMTP/Mailgun provider, not through Moodle's messaging system
- **Attachment support** — MVP sends plain text and HTML body only. File attachments are a future enhancement
- **Scheduled sending** — No delayed/scheduled send. Items go to queue immediately
- **Email provider abstraction** — MVP uses SMTP directly (configured via env vars). Mailgun/Sendgrid adapters are future enhancements
- **Delivery confirmation (bounce tracking)** — MVP marks as Enviado after SMTP acceptance. Bounce/read tracking via webhooks is future work
- **Template management UI** — Templates are code-level for MVP. A template management UI is future work
- **Comision filtering for destination** — MVP sends to all EntradaPadron entries for the materia. Per-comision filtering is future work
- **Batch cancellation** — MVP supports single-item cancellation only. Bulk cancel-all is future work

---

## Decisions

### D-01: Model structure — Comunicacion and LoteComunicacion as separate entities

Following E21 from the KB:

**Comunicacion** represents a single message to one recipient:

| Mixin | Comunicacion |
|-------|-------------|
| `AppModel` | UUID id |
| `TimestampMixin` | created_at, updated_at |
| `TenantMixin` | tenant_id (NOT NULL) |

Fields: `enviado_por` (FK Usuario, NOT NULL), `materia_id` (FK Materia, NOT NULL), `destinatario` (encrypted string), `asunto`, `cuerpo`, `estado` (enum: Pendiente, Enviando, Enviado, Error, Cancelado), `lote_id` (FK LoteComunicacion, nullable), `error_msg` (nullable, stores failure reason), `enviado_at` (nullable timestamp).

**LoteComunicacion** represents a bulk send batch:

| Mixin | LoteComunicacion |
|-------|------------------|
| `AppModel` | UUID id |
| `TimestampMixin` | created_at, updated_at |
| `TenantMixin` | tenant_id (NOT NULL) |

Fields: `materia_id` (FK Materia, NOT NULL), `enviado_por` (FK Usuario, NOT NULL), `asunto` (the shared subject), `total`, `enviados`, `fallidos`, `estado` (enum: Pendiente, AprobacionPendiente, Enviando, Completado, Parcial, Cancelado), `aprobado_por` (FK Usuario, nullable), `aprobado_at` (nullable timestamp), `requiere_aprobacion` (boolean, computed from tenant config), `preview_confirmado` (boolean, true after preview is confirmed — RN-16 enforcement).

The `LoteComunicacion.estado` is NOT the same as `Comunicacion.estado`:
- `LoteComunicacion` state tracks the batch: Pendiente → AprobacionPendiente (if needed) → Enviando → Completado/Parcial/Cancelado
- `Comunicacion` state tracks individual messages: Pendiente → Enviando → Enviado/Error/Cancelado

Neither model inherits `AuditMixin` (no `estado` column meaning soft-delete). Communication records are immutable history — once created, they are never deleted.

### D-02: Estado enum — separate enums for Comunicacion and LoteComunicacion

Two distinct enums:

```python
class EstadoComunicacion(str, Enum):
    pendiente = "Pendiente"
    enviando = "Enviando"
    enviado = "Enviado"
    error = "Error"
    cancelado = "Cancelado"

class EstadoLote(str, Enum):
    pendiente = "Pendiente"
    aprobacion_pendiente = "AprobacionPendiente"
    enviando = "Enviando"
    completado = "Completado"
    parcial = "Parcial"       # some sent, some failed
    cancelado = "Cancelado"
```

Separate enums keep semantics clear: individual messages have different terminal states than batches.

**Alternative considered:** Single `EstadoComunicacion` reused for both. Rejected because Lote needs `AprobacionPendiente`, `Completado`, and `Parcial` which are meaningless for individual messages.

### D-03: Destinatario as encrypted string

Per the KB's PII rules, `destinatario` (email address) is stored encrypted using the existing `core/security.py` AES-256 infrastructure from C-02:

```python
from core.security import encrypt_value, decrypt_value

# On write:
comunicacion.destinatario = encrypt_value(raw_email, tenant_id)

# On read:
raw_email = decrypt_value(comunicacion.destinatario, tenant_id)
```

The encryption uses the tenant-scoped key as established in C-02. The service layer handles encryption/decryption transparently — repositories store and retrieve encrypted strings.

### D-04: Template engine — simple string substitution

The template engine is a pure function that replaces `{{variable.path}}` patterns with actual values:

```python
def render_template(template: str, context: dict[str, Any]) -> str:
    """Replace {{key}} patterns with context values.
    
    Supported variables from RF-20:
      {{alumno.nombre}}    -> EntradaPadron.alumno_nombre
      {{materia.nombre}}   -> Materia.nombre
    """
    result = template
    for key, value in context.items():
        result = result.replace("{{" + key + "}}", str(value))
    return result
```

**Alternative considered:** Jinja2 templates. Rejected because:
- The variable set is small and well-defined (RF-20 specifies only `alumno.nombre` and `materia.nombre`)
- A full template engine introduces security concerns (server-side template injection)
- Simple substitution is testable, predictable, and sufficient for MVP
- Extensible to add more variables by simply adding them to the context dict

The service layer constructs the context dict by querying the relevant Alumno and Materia data.

### D-05: Preview flow (RN-16 enforcement)

Before any send operation, the system requires a preview step:

1. Client calls `POST /api/materias/{id}/comunicaciones/preview` with `asunto` (template), `cuerpo` (template), and optional `alumno_ids` (to preview for specific students)
2. Service renders the templates against actual data (random sample or specific students)
3. Returns `PreviewResponse` with rendered `asunto` and `cuerpo` for each previewed student
4. Client must call `POST /api/materias/{id}/comunicaciones/enviar` with `preview_confirmado: true` (RN-16)
5. If `preview_confirmado` is false or missing, the service rejects the request with 400

The `LoteComunicacion` record stores `preview_confirmado = True` at creation time. There is no "send without preview" path.

### D-06: Approval flow (RN-17) — per-tenant configuration

The approval requirement is controlled by a tenant-level configuration flag stored in the `Tenant` model (or a JSONB config field):

```python
# In Tenant model or related config
tenant.config.get("comunicaciones", {}).get("requiere_aprobacion_masiva", False)
```

When `requiere_aprobacion_masiva` is True:
1. `POST /api/materias/{id}/comunicaciones/enviar` creates the Lote with estado `AprobacionPendiente` and all Comunicaciones in `Pendiente`
2. `PUT /api/admin/comunicaciones/{id}/aprobar` accepts `{ "accion": "aprobar" | "rechazar" }` and `"motivo"` (optional)
3. On approve: Lote transitions to `Enviando`, worker picks it up
4. On reject: Lote transitions to `Cancelado`, all associated Comunicaciones go to `Cancelado`, reason stored in `error_msg`

When `requiere_aprobacion_masiva` is False (default):
- The send endpoint immediately sets Lote to `Pendiente` and the worker starts processing

The threshold for "masivo" is defined as > 1 recipient (any bulk send) for MVP. Future changes could make the threshold configurable per tenant.

### D-07: Async worker — polling loop with configurable interval

The worker is a standalone async loop that runs in a separate process:

```
Worker loop (every N seconds, default 30):
  1. Query Lote where estado = Pendiente (or AprobacionPendiente -> skipped)
  2. For each ready Lote:
     a. Set Lote.estado = Enviando
     b. Query all Comunicaciones with estado = Pendiente for this lote
     c. For each Comunicacion:
        - Decrypt destinatario
        - Render template with context
        - Send via SMTP
        - On success: set estado = Enviado, enviado_at = now()
        - On failure: set estado = Error, error_msg = str(exception), increment retry_count
        - Retry policy: up to 3 retries (retry_count < 3 and estado == Error → reset to Pendiente)
     d. After processing all items:
        - If all Enviado -> Lote.estado = Completado
        - If all Error/Cancelado -> Lote.estado = Cancelado
        - If mixed -> Lote.estado = Parcial
        - Update Lote.enviados, Lote.fallidos counters
```

**Alternative considered:** Celery/RQ/APScheduler. Rejected because:
- The system only has one queue (communications) — a full job queue system is overkill
- A simple asyncio loop with configurable interval is minimal, testable, and requires no external dependencies
- The worker runs as a separate process (docker container) that can be scaled independently
- If the system grows to need multiple queues, Celery can be introduced later

Worker startup:
```python
# In workers/communication_worker.py
async def run_worker(interval: int = 30):
    while True:
        try:
            await process_queue()
        except Exception as e:
            logger.error("Worker error", exc_info=e)
        await asyncio.sleep(interval)
```

The worker accesses the same database and application code (models, repositories, services). It reuses the existing SMTP configuration from `core/config.py`.

### D-08: SMTP configuration

SMTP settings are added to `core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # SMTP / Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_FROM_EMAIL: str = "noreply@activia-trace.com"
    SMTP_FROM_NAME: str = "activia-trace"
    
    # Worker
    WORKER_POLL_INTERVAL: int = 30  # seconds
    WORKER_MAX_RETRIES: int = 3
```

The email sending logic is encapsulated in a `services/email_sender.py` module:

```python
async def send_email(to: str, subject: str, body_html: str) -> None:
    """Send email via SMTP. Async wrapper around aiosmtplib or sync smtplib in executor."""
```

**Alternative considered:** aiosmtplib for fully async SMTP. Decision deferred to implementation — the service can use `asyncio.to_thread(smtplib.SMTP.sendmail)` if aiosmtplib adds dependency overhead.

### D-09: Alembic migration 007

New file at `alembic/versions/XXXX_add_comunicaciones.py`. Migration depends on revision 004 (asignaciones schema) since it references `usuarios` and `materias` tables.

```sql
CREATE TABLE lotes_comunicaciones (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    materia_id UUID NOT NULL REFERENCES materias(id) ON DELETE CASCADE,
    enviado_por UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    asunto VARCHAR(500) NOT NULL,
    total INTEGER NOT NULL DEFAULT 0,
    enviados INTEGER NOT NULL DEFAULT 0,
    fallidos INTEGER NOT NULL DEFAULT 0,
    estado VARCHAR(30) NOT NULL DEFAULT 'Pendiente',
    requiere_aprobacion BOOLEAN NOT NULL DEFAULT FALSE,
    aprobado_por UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    aprobado_at TIMESTAMPTZ,
    preview_confirmado BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE comunicaciones (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lote_id UUID REFERENCES lotes_comunicaciones(id) ON DELETE SET NULL,
    materia_id UUID NOT NULL REFERENCES materias(id) ON DELETE CASCADE,
    enviado_por UUID NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    destinatario TEXT NOT NULL,  -- encrypted
    asunto VARCHAR(500) NOT NULL,
    cuerpo TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'Pendiente',
    error_msg TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0,
    enviado_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX ix_comunicaciones_tenant_estado ON comunicaciones(tenant_id, estado);
CREATE INDEX ix_comunicaciones_lote_id ON comunicaciones(lote_id);
CREATE INDEX ix_comunicaciones_materia_id ON comunicaciones(materia_id);
CREATE INDEX ix_lotes_tenant_estado ON lotes_comunicaciones(tenant_id, estado);
CREATE INDEX ix_lotes_materia_id ON lotes_comunicaciones(materia_id);
```

Indexes cover:
- Worker query: find all Pendiente communications by tenant (or all tenants) — `ix_comunicaciones_tenant_estado`
- Status tracking by lote — `ix_comunicaciones_lote_id`
- Status tracking by materia — `ix_comunicaciones_materia_id`
- Worker query for ready lotes — `ix_lotes_tenant_estado`
- Admin view by materia — `ix_lotes_materia_id`

### D-10: Permission guards — `comunicacion:enviar` and `comunicacion:aprobar`

Two new permissions added to `core/permissions.py`:

| Permission | PROFESOR | COORDINADOR | ADMIN |
|------------|----------|-------------|-------|
| `comunicacion:enviar` | ✅ (own materias) | ✅ | ✅ |
| `comunicacion:aprobar` | ❌ | ✅ | ✅ |

Mutating endpoints:
- `POST /preview` — `comunicacion:enviar` + verify sender has assignment to the materia (for PROFESOR)
- `POST /enviar` — `comunicacion:enviar` + verify materia assignment
- `PUT /aprobar` — `comunicacion:aprobar`
- `GET /comunicaciones` — `comunicacion:enviar` (read own sends) or `comunicacion:aprobar` (read all for admin)

For PROFESOR scope enforcement: the service validates that `enviado_por` (from JWT) has an active assignment (`Asignacion`) for the target `materia_id` before allowing any operation.

### D-11: Repository pattern — ComunicacionRepository and LoteRepository

Following Clean Architecture:
- `ComunicacionRepository` — CRUD + find_by_lote, find_by_materia, find_pendientes_for_worker, bulk_update_status
- `LoteRepository` — CRUD + find_ready_for_worker (Pendiente lotes without required approval or with approval), update_counters
- Both inherit from `BaseRepository` and scope all queries by `tenant_id`

Worker-specific queries:
```python
async def find_pendientes_for_worker(self, batch_size: int = 50) -> list[Comunicacion]:
    """Find communications ready for processing (Pendiente, attached to an Enviando lote)."""
    stmt = (
        select(Comunicacion)
        .join(LoteComunicacion, Comunicacion.lote_id == LoteComunicacion.id)
        .where(
            Comunicacion.estado == EstadoComunicacion.pendiente,
            LoteComunicacion.estado.in_([EstadoLote.enviando, EstadoLote.pendiente]),
            Comunicacion.retry_count < 3,
        )
        .limit(batch_size)
    )
    result = await self.session.execute(stmt)
    return list(result.scalars().all())
```

### D-12: Pydantic schemas with `extra='forbid'`

Following the project convention:

- `PreviewRequest`: asunto (str), cuerpo (str), alumno_ids (list[str], optional, max 5 for preview sample)
- `PreviewResponse`: previews (list of {alumno_nombre, email_preview, asunto_renderizado, cuerpo_renderizado})
- `EnviarRequest`: asunto (str), cuerpo (str), preview_confirmado (bool, required True), alumno_ids (list[str], optional — if omitted, send to all padron entries)
- `ComunicacionResponse`: id, materia_id, destinatario (masked), asunto, estado, enviado_at, error_msg
- `LoteResponse`: id, materia_id, total, enviados, fallidos, estado, requiere_aprobacion, created_at
- `AprobarRequest`: accion (enum: aprobar, rechazar), motivo (optional string)
- All with `model_config = ConfigDict(extra='forbid')`

### D-13: Destinatario masked in API responses

When returning `ComunicacionResponse`, the `destinatario` field is masked for privacy:

```python
def mask_email(email: str) -> str:
    """Mask email for display: j***@example.com"""
    local, domain = email.split("@", 1)
    return local[0] + "***@" + domain
```

The unmasked email is never returned via API. The worker decrypts it only for sending.

---

## Risks / Trade-offs

| Risk | Probability | Mitigation |
|------|-------------|------------|
| SMTP credentials exposed in env vars | Low | Stored in `.env`/environment, never in code. Use existing secret management from C-01 |
| Worker dies without processing queue | Medium | Worker runs as separate container with restart policy. On restart, it re-processes Pendiente items (idempotent — items already sent won't be re-queried because estado changes to Enviando) |
| Race condition: worker picks same item twice | Low | Atomic update of estado to Enviando before processing. Use `UPDATE ... WHERE estado = 'Pendiente' RETURNING *` pattern |
| Email send is slow (SMTP latency per recipient) | Medium | Worker processes in batches with configurable concurrency. Start with sequential sends, add asyncio.gather with semaphore for concurrent sends if needed |
| Tenant-level approval config not yet modeled | Low | Store `requiere_aprobacion_masiva` in `Tenant.config` JSONB field. If Tenant model lacks `config`, add it in this change |
| Template variables don't match EntradaPadron field names | Low | Clear mapping: `alumno.nombre` maps to `EntradaPadron.alumno_nombre`, `materia.nombre` maps to `Materia.nombre`. Document in template_engine.py |
| Retry loop could keep failing on permanent errors (invalid email) | Low | Distinguish transient vs permanent errors. Invalid email → mark as Error (no retry). SMTP timeout → retry (increment retry_count) |
| PII encryption key management | Low | Reuse existing `ENCRYPTION_KEY` from C-02. Document that destinatario follows same encryption pattern as other PII fields |
| Mass email could trigger spam filters | Low | Responsibility of the SMTP provider configuration. System sends from configured SMTP_FROM_EMAIL |
| Worker needs to scale beyond single process | Low | For MVP, single worker is sufficient. Future: add queue-based architecture (Redis + RQ/Celery) for horizontal scaling |

---

## Migration Plan

1. Create migration 007 with `depends_on='004_...'` (roles-asignaciones revision)
2. Upgrade runs: 2 CREATE TABLE + 6 indexes
3. Downgrade drops both tables
4. Rollforward is safe (additive, no data loss)
5. No data migration needed (new tables, no existing data to transform)
6. Post-migration: add `comunicacion:enviar` and `comunicacion:aprobar` permissions to seed data
7. Worker container added to docker-compose.yml as a separate service
