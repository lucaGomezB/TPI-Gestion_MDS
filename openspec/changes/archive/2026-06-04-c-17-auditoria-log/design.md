## Context

El sistema no tiene registro de auditoría. C-03 (auth-rbac) estableció autenticación JWT + RBAC con roles y permisos, pero ninguna operación de escritura queda trazada. RN-23 exige que cada acción significativa genere un registro inmutable con actor, contexto (materia), IP, user agent y filas afectadas. RN-24 requiere un catálogo cerrado de códigos de acción estandarizados. F9.1 y F9.2 requieren vistas consultables del log con búsqueda full-text y panel por docente.

**Current state:** C-01 (foundation), C-02 (core-models), C-03 (auth-rbac) archivados. Existen modelos Tenant, Usuario, Rol, UsuarioRol, RefreshToken. El middleware de autenticación y `require_permission` están operativos. No existe tabla `audit_log`.

**Governance level:** CRITICO — la integridad del log de auditoría es absoluta. Cualquier violación al append-only compromete la trazabilidad del sistema.

---

## Goals / Non-Goals

**Goals:**
- Modelo `AuditLog` append-only en todas las capas (repositorio, servicio, base de datos)
- Middleware/interceptor que registre acciones significativas automáticamente
- `GET /api/admin/auditoria` con búsqueda full-text y filtros (accion, usuario, materia, fecha, IP)
- `GET /api/admin/auditoria/docentes/{id}/interacciones` — panel de interacciones por docente (F9.1)
- Catálogo cerrado de códigos de acción como `StrEnum` Python (RN-24)
- Protección de PII: datos cifrados (email, DNI, CUIL, CBU, CBU alias) NUNCA en `detalle`
- Exportación de resultados de búsqueda (CSV, JSON)
- Migration 013: tabla `audit_log` con índices para búsqueda y tenant isolation
- Soporte de impersonación: `actor_id` = quien ejecuta, `impersonado_id` = usuario impersonado
- Tests: registro, búsqueda, append-only, impersonación, protección PII, tenant isolation

**Non-Goals:**
- **Reglas de retención automática** — sin límite de retención para MVP. Se agregará purga/archivo basado en configuración en cambio futuro
- **UI de gestión** — solo API. La interfaz de administración es cambio futuro
- **Alertas/anomalías sobre el log** — fuera de scope. No hay detección de patrones sospechosos
- **Auditoría sobre consultas GET** — solo acciones de escritura. Lecturas no se registran salvo que tengan efecto significativo (ej: export)
- **Redis u otro backend externo** — PostgreSQL nativo para MVP. Full-text search via tsvector
- **Dashboard de métricas en tiempo real** — F9.1 incluye conteos agrupados, no streaming

---

## Decisions

### D-01: Append-only enforcement en TRES capas

| Capa | Mecanismo |
|------|-----------|
| **Repositorio** | `AuditRepository` solo expone `create()` y `search()`/`count()`. NO existen métodos `update()` ni `delete()` |
| **Base de datos** | Trigger PostgreSQL `REJECT_AUDIT_UPDATE_DELETE` que lanza EXCEPTION en UPDATE o DELETE sobre `audit_log` |
| **Modelo/SQLAlchemy** | `__table_args__` con `listen()` o event listener que previene updates a nivel ORM |

**Alternativa descartada:** Confiar solo en la omisión de métodos del repositorio — un developer futuro podría agregar un update sin saber la regla. La triple capa asegura que incluso un query SQL directo fracase.

### D-02: Full-text search via PostgreSQL tsvector

- Columna generada `search_vector TSVECTOR` mantenida por trigger o generated column (PostgreSQL 12+)
- `search_vector` combina: `accion || ' ' || COALESCE(detalle::text, '') || ' ' || COALESCE(ip, '')`
- GIN index sobre `search_vector` para búsqueda full-text
- Filtros adicionales con índices B-tree compuestos para consultas sin texto libre
- Uso de `plainto_tsquery('spanish', query)` para búsqueda por palabras clave (tokenización en español)

```sql
-- Generated column approach (PostgreSQL 12+)
ALTER TABLE audit_log ADD COLUMN search_vector TSVECTOR
    GENERATED ALWAYS AS (
        to_tsvector('spanish', coalesce(accion, '') || ' ' || coalesce(detalle::text, '') || ' ' || coalesce(ip, ''))
    ) STORED;

CREATE INDEX ix_audit_log_search_vector ON audit_log USING GIN(search_vector);
```

### D-03: Index strategy para filtros

| Query Pattern | Index |
|---------------|-------|
| Búsqueda por tenant + fecha descendente | `(tenant_id, fecha_hora DESC)` |
| Filtro por acción | `(tenant_id, accion)` |
| Filtro por actor (usuario) | `(tenant_id, actor_id, fecha_hora DESC)` |
| Filtro por materia | `(tenant_id, materia_id, fecha_hora DESC)` |
| Filtro por IP | `(tenant_id, ip)` |
| Full-text search | GIN en `search_vector` (ver D-02) |

Todos los incluyen `tenant_id` como prefijo para garantizar tenant isolation por índice.

### D-04: Action code catalog como StrEnum

```python
class AccionAuditoria(str, Enum):
    CALIFICACIONES_IMPORTAR = "CALIFICACIONES_IMPORTAR"
    PADRON_CARGAR = "PADRON_CARGAR"
    COMUNICACION_ENVIAR = "COMUNICACION_ENVIAR"
    ASIGNACION_MODIFICAR = "ASIGNACION_MODIFICAR"
    LIQUIDACION_CERRAR = "LIQUIDACION_CERRAR"
    IMPERSONACION_INICIAR = "IMPERSONACION_INICIAR"
    IMPERSONACION_FINALIZAR = "IMPERSONACION_FINALIZAR"
```

El StrEnum se guarda en `accion` como texto. Es cerrado (RN-24): el constructor acepta solo valores del enum. En futuros changes se agregarán nuevos valores al enum.

### D-05: Middleware de auditoría — interceptor por servicio

No se usa un middleware HTTP (WSGI) porque:
1. No toda request POST/PUT/PATCH debe generar un log (ej: login fallido no se registra)
2. El `detalle` requiere contexto de dominio que el middleware HTTP no tiene
3. Las acciones bajo impersonación necesitan el actor real del JWT

**Patrón:** Un `AuditInterceptor` que los servicios llaman explícitamente:

```python
# Uso en servicio:
class CalificacionesService:
    def __init__(self, audit: AuditService):
        self.audit = audit

    async def importar(self, materia_id, archivo, current_user):
        resultado = await self._procesar_archivo(materia_id, archivo)
        await self.audit.log_action(
            accion=AccionAuditoria.CALIFICACIONES_IMPORTAR,
            actor_id=current_user.id,
            materia_id=materia_id,
            detalle={"actividades": resultado.actividades, "alumnos": resultado.alumnos},
            filas_afectadas=resultado.total_filas,
            ip=current_user.ip,
            user_agent=current_user.user_agent,
            impersonado_id=current_user.impersonating_id,  # None si no hay impersonación
        )
        return resultado
```

Alternativamente, un decorador `@audit_log(accion, ...)` puede simplificar el uso para casos simples.

### D-06: PII sanitization en detalle JSON

El campo `detalle` acepta un `dict[str, Any]` que el servicio de auditoría **NUNCA** debe contener datos PII (email, DNI, CUIL, CBU, alias CBU).

**Regla explícita:** cualquier valor que corresponda a un campo `[cifrado]` en el modelo de datos está PROHIBIDO en `detalle`. Esto se enforce con:
1. **Documentación clara** en la firma del servicio
2. **Code review** obligatorio en cada sitio de `log_action()`
3. Test que verifica que ningún detalle contiene patrones de PII (emails, DNI)

No se implementa sanitización automática porque el servicio no puede saber qué datos del detalle son PII — depende del contexto. Es responsabilidad del llamante.

### D-07: Impersonación — dos IDs en el registro

Cuando un ADMIN impersona a otro usuario:
- `actor_id` = UUID del ADMIN real (quien ejecuta la acción)
- `impersonado_id` = UUID del usuario impersonado (bajo cuya identidad opera)
- Ambos campos son FK a `usuarios.id`

En sesión normal sin impersonación: `actor_id` = usuario, `impersonado_id` = NULL.

### D-08: Búsqueda y paginación

`GET /api/admin/auditoria` acepta:
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `q` | string | Búsqueda full-text (opcional) |
| `accion` | string | Filtrar por código de acción exacto |
| `actor_id` | UUID | Filtrar por usuario que ejecutó |
| `materia_id` | UUID | Filtrar por materia |
| `ip` | string | Filtrar por IP |
| `fecha_desde` | datetime | Rango inicio |
| `fecha_hasta` | datetime | Rango fin |
| `limit` | int | Page size (default 50, max 200) |
| `offset` | int | Pagination offset |

Respuesta: `{"items": [...], "total": N, "limit": 50, "offset": 0}`

`GET /api/admin/auditoria/docentes/{id}/interacciones` devuelve métricas agrupadas (F9.1):
```json
{
  "docente_id": "uuid",
  "total_acciones": 150,
  "por_accion": {
    "CALIFICACIONES_IMPORTAR": 45,
    "COMUNICACION_ENVIAR": 80,
    "PADRON_CARGAR": 25
  },
  "por_materia": [
    {"materia_id": "uuid", "nombre": "Programación I", "total": 60}
  ],
  "ultimas_acciones": [...]
}
```

### D-09: Exportación

`GET /api/admin/auditoria/exportar` acepta los mismos filtros que búsqueda + `formato` (`csv` | `json`). Para MVP: genera el archivo en memoria y lo devuelve como `StreamingResponse` con headers de descarga. Sin almacenamiento intermedio.

### D-10: AuditLog model

```python
class AuditLog(AppModel, TenantMixin):
    __tablename__ = "audit_log"

    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actor_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id"), nullable=False, index=True
    )
    impersonado_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    materia_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("materias.id"), nullable=True
    )
    accion: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    detalle: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    filas_afectadas: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
```

Note: `TenantMixin` adds `tenant_id`. `AuditLog` NO hereda `TimestampMixin` ni `AuditMixin` porque no tiene `updated_at` ni `deleted_at` (es inmutable).

---

## Migration 013: Audit log schema

```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    fecha_hora TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_id UUID NOT NULL REFERENCES usuarios(id),
    impersonado_id UUID REFERENCES usuarios(id),
    materia_id UUID REFERENCES materias(id),
    accion VARCHAR(50) NOT NULL,
    detalle JSONB,
    filas_afectadas INTEGER,
    ip VARCHAR(45),
    user_agent VARCHAR(500)
);

-- Full-text search support (generated column)
ALTER TABLE audit_log ADD COLUMN search_vector TSVECTOR
    GENERATED ALWAYS AS (
        to_tsvector('spanish',
            coalesce(accion, '') || ' ' ||
            coalesce(detalle::text, '') || ' ' ||
            coalesce(ip, '')
        )
    ) STORED;

-- Indexes for filtering and search
CREATE INDEX ix_audit_log_tenant_fecha ON audit_log(tenant_id, fecha_hora DESC);
CREATE INDEX ix_audit_log_tenant_accion ON audit_log(tenant_id, accion);
CREATE INDEX ix_audit_log_tenant_actor ON audit_log(tenant_id, actor_id, fecha_hora DESC);
CREATE INDEX ix_audit_log_tenant_materia ON audit_log(tenant_id, materia_id, fecha_hora DESC);
CREATE INDEX ix_audit_log_tenant_ip ON audit_log(tenant_id, ip);
CREATE INDEX ix_audit_log_search_vector ON audit_log USING GIN(search_vector);

-- Append-only trigger: reject UPDATE and DELETE
CREATE OR REPLACE FUNCTION reject_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE are forbidden';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reject_audit_update
    BEFORE UPDATE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION reject_audit_modification();

CREATE TRIGGER trg_reject_audit_delete
    BEFORE DELETE ON audit_log
    FOR EACH ROW EXECUTE FUNCTION reject_audit_modification();
```

---

## Risks / Trade-offs

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| **Crecimiento ilimitado del log** | Alta | Aceptado para MVP. Sin límite de retención. Futuro: job programado de purga/archivo |
| **Performance de full-text search en tablas grandes** | Media | GIN index + paginación obligatoria. Si >10M registros, evaluar particionado por fecha |
| **Trigger de append-only afecta rendimiento en inserts** | Baja | Trigger BEFORE es liviano. Impacto despreciable comparado con I/O del insert |
| **PII leak por error del desarrollador en detalle** | Media | Code review obligatorio + tests de integración que verifican que ningún log contiene PII conocida |
| **Migración falla en PostgreSQL < 12 (generated column)** | Baja | El proyecto usa PostgreSQL 16+ en producción. Versiones anteriores no soportadas |
| **Servicio de auditoría como bottleneck en writes** | Baja | `log_action()` es un insert sin locking. Si escala, futuro: cola asíncrona |

---

## Open Questions

1. La generated column `search_vector` se actualiza automáticamente al insertar. ¿Necesitamos actualizarla si se modificara `detalle`? No — el log es append-only, núnca se modifica, así que no hay problema.

2. ¿Debemos limitar el tamaño de `detalle` (JSONB)? JSONB no tiene límite de tamaño en PostgreSQL, pero el `detalle` debe ser acotado (máximo sugerido: 10KB por entrada). Esto se enforce a nivel de schema con validación Pydantic.

3. ¿Se necesita índices `DESC` o el planner de PostgreSQL usa index scan backward? PostgreSQL usa `Index Scan Backward` eficientemente, pero el índice `(tenant_id, fecha_hora DESC)` es explícito para claridad y consistencia entre versiones.

---

## Architecture Flow

```
POST /api/calificaciones/importar  (ejemplo)
  → require_permission("calificaciones:importar")
  → CalificacionesService.importar()
      → procesa archivo, guarda calificaciones
      → audit_service.log_action(
            accion="CALIFICACIONES_IMPORTAR",
            actor_id=current_user.id,
            materia_id=materia_id,
            detalle={"actividades": n, "alumnos": m},
            filas_afectadas=n*m,
            ip=request.client.host,
            user_agent=request.headers.get("user-agent"),
            impersonado_id=current_user.impersonating_user_id or None
        )
  → return 201

GET /api/admin/auditoria?q=importar&accion=CALIFICACIONES_IMPORTAR&fecha_desde=...
  → require_permission("auditoria:ver")
  → AuditService.search(
        tenant_id=current_user.tenant_id,
        q="importar",
        accion="CALIFICACIONES_IMPORTAR",
        fecha_desde=...,
        limit=50,
        offset=0
    )
  → AuditRepository.search()  # tsquery + B-tree filters + pagination
  → return {"items": [...], "total": N, "limit": 50, "offset": 0}

GET /api/admin/auditoria/docentes/{id}/interacciones
  → require_permission("auditoria:ver")
  → AuditService.get_docente_interacciones(docente_id=id, tenant_id=...)
  → AuditRepository.count_grouped_by_action(docente_id, tenant_id)
  → AuditRepository.count_grouped_by_materia(docente_id, tenant_id)
  → AuditRepository.get_last_actions(docente_id, tenant_id, limit=200)
  → return métricas agrupadas
```

```
Ruta con impersonación
  → current_user tiene impersonating_user_id seteado
  → audit_service.log_action(actor_id=current_user.id, impersonado_id=current_user.impersonating_user_id)
  → registro queda con ambos IDs
```
