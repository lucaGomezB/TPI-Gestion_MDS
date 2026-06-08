## Context

El PRD exige integración automática con Moodle vía Web Services (RF-06) con fallback de import manual (RF-07). El sistema actual tiene el modelo de datos core (C-02) y auth/RBAC (C-03) implementados, pero no existe ningún mecanismo de ingesta. La Épica 1 del catálogo de funcionalidades (F1.1–F1.4) depende enteramente de este cambio.

**Estado actual:** Migración 004 (core académico). Sin conexión a Moodle. Sin import de archivos. Sin configuración de tenant para integraciones.

**Restricciones conocidas:**
- Clean Architecture estricta: `integrations/` es capa de infraestructura, no toca lógica de negocio ni persistencia directa.
- Multi-tenant nativo: cada tenant tiene su propia URL y token de Moodle WS.
- Secretos siempre cifrados AES-256 (MOODLE_WS_TOKEN va cifrado en JSONB).
- Errores de integración externa mapean a HTTP 502.
- Governance: ALTO — afecta configuración de tenant y datos académicos.

---

## Goals / Non-Goals

**Goals:**

1. Cliente Moodle WS abstracto y testable en `integrations/moodle_ws.py` — soporta las funciones `core_grades_get_grades`, `core_enrol_get_enrolled_users`, `core_user_get_users`, `gradereport_user_get_grade_items`.
2. Sync engine orquestador: llama WS → mapea al modelo de dominio → persiste vía repositories (transaccional por dictado, con manejo de errores granular).
3. Sync nocturna automática: worker async programado (default 03:00 AM) que recorre todos los dictados activos del tenant y ejecuta sync.
4. Sync on-demand desde API: `POST /api/v1/materias/{dictado_id}/sync-moodle` — gatillado por el usuario (PROFESOR para sus dictados, COORDINADOR para cualquier dictado del tenant).
5. Configuración Moodle por tenant: `MOODLE_WS_URL`, `MOODLE_WS_TOKEN` almacenados en columna `config_moodle` JSONB con cifrado AES-256.
6. Fallback de import manual: parseo de `.xlsx`/`.csv` con preview y confirmación, para tenants sin WS o carga histórica.
7. Tests: mock de Moodle WS, test de sync on-demand, test de fallback import, test de tenant boundary.

**Non-Goals:**

- **SSO Moodle para alumnos** — diferido a Fase 2 (ADR-001). Auth propio para MVP.
- **Soporte OAuth2 Moodle** — el MVP usa token-based (Web Services Token). Si Moodle del tenant requiere OAuth2, se agrega en cambio futuro.
- **Sincronización bidireccional** — solo lectura desde Moodle hacia activia-trace. No se escribe en Moodle.
- **Cache de respuestas Moodle** — el sync es pull siempre. Cache se agregaría si hay problemas de performance, no en MVP.
- **Catálogo completo de WS functions** — solo las 4 funciones listadas. Otras (ej: `core_course_get_courses`) se agregan bajo demanda en cambios futuros.
- **UI de configuración Moodle** — la configuración se hará vía API o seed. UI se agrega cuando exista el módulo de administración de tenant.

---

## Decisions

### D-01: Async HTTP client con `aiohttp`

| Criterio | Decisión |
|----------|----------|
| Librería | `aiohttp` (async, madura, soporte nativo para conexiones persistentes y timeouts) |
| Alternativa descartada 1 | `httpx` — buena pero `aiohttp` tiene mejor performance en client HTTP-only (sin server), más ampliamente usada en integraciones async Python |
| Alternativa descartada 2 | `requests` (sync) — bloquearía el event loop de FastAPI. Inaceptable para un endpoint que debe responder rápido |

El cliente Moodle WS será una instancia reutilizable configurada con `connector` de `aiohttp.TCPConnector` (conexiones persistentes, límite de conexiones por host). Timeout global configurable via `Settings.MOODLE_REQUEST_TIMEOUT` (default 30s).

### D-02: Moodle WS Client — patrón Adapter con respuesta tipada

El cliente `MoodleWSClient` será un **adapter** que encapsula:
1. Armado de request XML-RPC o REST (según versión Moodle del tenant — se detecta en el handshake inicial).
2. Autenticación con `wstoken` en query param.
3. Parsing de respuesta y mapeo a `MoodleGradeResponse`, `MoodleEnrolledUser`, `MoodleUserProfile` Pydantic models.
4. Manejo de errores: errores HTTP → `MoodleConnectionError`, errores de API Moodle (códigos internos) según el "debug" de la respuesta.
5. Retry: 2 reintentos con backoff exponencial (1s, 3s) ante `5xx` o timeout de red. Sin retry en `4xx`.

**Funciones WS implementadas:**

| Función Moodle | Parámetros | Retorna | Uso en activia-trace |
|---|---|---|---|
| `core_grades_get_grades` | `courseid`, `userids` (opcional), `itemid` (opcional) | Grade items + grades por usuario | Importar calificaciones de un dictado (course = curso Moodle vinculado) |
| `core_enrol_get_enrolled_users` | `courseid` | Lista de usuarios enrolados con roles | Importar padrón de alumnos del dictado |
| `core_user_get_users` | `criteria` (field + value) | User profiles con campos estándar | Obtener datos de perfil de alumnos (nombre, email) |
| `gradereport_user_get_grade_items` | `courseid`, `userid` | Grade items del curso | Obtener catálogo de actividades del dictado |

### D-03: Sync Engine con paso a paso granular

El sync NO es una operación atómica gigante. Se divide en pasos independientes, cada uno con su propio manejo de errores:

1. **Fetch activities**: llama `gradereport_user_get_grade_items` → obtiene catálogo de actividades del curso Moodle.
2. **Fetch enrolled users**: llama `core_enrol_get_enrolled_users` → obtiene padrón actual.
3. **Match dictado → curso Moodle**: el `Dictado` tiene un campo `moodle_course_id` (Integer, nullable) que vincula con el courseid de Moodle.
4. **Fetch grades**: llama `core_grades_get_grades(courseid=moodle_course_id)` → obtiene calificaciones de todos los alumnos.
5. **Map & persist**: recorre grade items y grades, mapea a modelos internos (`Actividad`, `Calificacion`), persiste vía repositories con upsert.
6. **Update padrón**: sincroniza `AlumnoDictado` — upsert para alumnos existentes, soft-delete para los que ya no están (según RN-05 — upsert destructivo del padrón).

Cada paso tiene su propio bloque try/except. Si falla el fetch de notas pero el padrón se actualizó bien, el sync reporta éxito parcial. El estado del sync se registra en una tabla `sync_log` (ver D-05).

### D-04: Per-tenant Moodle config con cifrado

Se agrega columna `config_moodle` (JSONB, nullable) a la tabla `tenants`. Estructura:

```json
{
  "ws_url": "<AES-256 encrypted>",
  "ws_token": "<AES-256 encrypted>",
  "ws_enabled": true,
  "last_sync_at": "2026-06-04T03:00:00Z",
  "sync_frequency_hours": 24,
  "moodle_version": "4.1"
}
```

- `ws_url` y `ws_token` se cifran con AES-256 usando `ENCRYPTION_KEY` del sistema (misma que para PII).
- El acceso se hace via `settings_service.get_moodle_config(tenant_id)` que descifra y retorna un `MoodleConfig` Pydantic schema.
- `ws_enabled` permite deshabilitar WS por tenant (para los que usan solo import manual).
- El `tenant_id` se resuelve del JWT — nunca de parámetros de request.

### D-05: Sync Log (tabla nueva para trazabilidad)

Se crea tabla `sync_log` para registrar cada ejecución de sync:

```sql
CREATE TABLE sync_log (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    dictado_id UUID REFERENCES dictados(id),  -- nullable para sync global
    sync_type VARCHAR(20) NOT NULL,  -- 'nocturnal', 'ondemand', 'manual_import'
    status VARCHAR(20) NOT NULL,  -- 'running', 'completed', 'failed', 'partial'
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    details JSONB,  -- {steps: [{step, status, records_affected, error}], ...}
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Esto permite auditar cuándo se sincronizó cada dictado, con qué resultado, y facilita la detección de problemas de conectividad con Moodle.

### D-06: Scheduled nocturnal sync via async worker

La arquitectura ya contempla un worker async para cola de comunicaciones. Para el sync nocturno se usa el mismo patrón: un **background task** que se ejecuta con `asyncio` en un bucle separado, no bloquea el event loop de FastAPI.

Implementación MVP: `asyncio.create_task` en el startup de FastAPI con un loop `while True: await asyncio.sleep(segundos_hasta_proxima_ejecucion)`. Esto es suficientemente simple para MVP y evita dependencias externas (Celery, Redis).

En producción se migrará a un scheduler dedicado (APScheduler o similar) o a un job externo.

El worker:
1. Consulta tenants con `ws_enabled=true`.
2. Por cada tenant, consulta dictados activos con `moodle_course_id IS NOT NULL`.
3. Ejecuta sync engine para cada dictado.
4. Registra resultado en `sync_log`.

### D-07: Manual import — preview + confirm

El flujo de import manual replica la funcionalidad descrita en F1.1–F1.4:

1. **Upload**: usuario sube archivo `.xlsx`/`.csv` a `POST /api/v1/materias/{dictado_id}/import/preview`
2. **Parse & preview**: el sistema parsea el archivo, detecta columnas de nota (según RN-01: columnas que terminan en `(Real)`), identifica actividades y alumnos, y devuelve un preview con:
   - Actividades detectadas (nombre, tipo de escala: numérica o textual)
   - Alumnos detectados (cantidad, primeros 5 como muestra)
   - Posibles incidencias (columnas no reconocidas, filas sin dato de alumno)
3. **Confirm import**: usuario confirma con `POST /api/v1/materias/{dictado_id}/import/confirm` pasando los IDs de actividades a incluir.
4. **Persist**: el servicio persiste las actividades y calificaciones seleccionadas, respetando RN-02 (mapeo de escala textual a aprobado).

El parser soporta:
- Encabezados en primera fila.
- Detección automática de separador en CSV (coma, punto y coma, tab).
- Columnas de identificación: DNI, email, nombre+apellido (configurable por inferencia).
- Escala textual configurable vía catálogo del tenant (RN-02).

### D-08: Permission model

- `POST /api/v1/materias/{dictado_id}/sync-moodle` requiere `calificaciones:importar` (de la matriz RBAC existente).
- Scope: PROFESOR puede sync solo dictados donde tiene asignación activa. COORDINADOR puede sync cualquier dictado del tenant.
- `POST /api/v1/materias/{dictado_id}/import/*` requiere `calificaciones:importar` con el mismo scope.
- `GET /api/v1/materias/{dictado_id}/sync-log` requiere `calificaciones:importar` (para ver historial de sync).
- `PATCH /api/v1/admin/tenants/moodle-config` requiere `tenant:configurar` (solo ADMIN).

### D-09: Migration strategy

**Migration 005**: agregar `config_moodle` (JSONB, nullable) a `tenants`.
**Migration 006**: crear `sync_log` table.
Ambas son migraciones hacia adelante, sin breaking changes para el schema existente.

---

## Architecture Flow

### On-demand sync flow

```
POST /api/v1/materias/{dictado_id}/sync-moodle
  → get_current_user (JWT)
  → require_permission("calificaciones:importar")
  → scope check: PROFESOR → must be assigned to dictado
  → moodle_sync_service.sync_dictado(tenant_id, dictado_id)
      → load moodle config (decrypt WS URL + token)
      → moodle_ws_client.get_grade_items(moodle_course_id)
      → moodle_ws_client.get_enrolled_users(moodle_course_id)
      → moodle_ws_client.get_grades(moodle_course_id)
      → map WS responses to domain DTOs
      → persist via repositories (transactional)
      → create sync_log entry
  → return SyncResult {status, activities_synced, students_synced, errors}
```

### Nocturnal sync flow

```
Worker startup (asyncio.create_task)
  loop:
    → wait until next 03:00 AM
    → for each tenant with ws_enabled=true:
        → for each dictado with moodle_course_id not null:
            → sync_dictado(...)
            → log to sync_log
    → sleep 24 hours
```

### Manual import flow

```
POST /api/v1/materias/{dictado_id}/import/preview
  → get_current_user + require_permission("calificaciones:importar")
  → upload file (.xlsx/.csv)
  → manual_import_service.parse_and_preview(file, dictado_id)
      → detect header row, grade columns (RN-01)
      → extract activities, students, grades
      → return PreviewResult {activities, students_count, warnings}

POST /api/v1/materias/{dictado_id}/import/confirm
  → get_current_user + require_permission("calificaciones:importar")
  → body: {activity_ids: UUID[]}
  → manual_import_service.confirm_import(dictado_id, activity_ids, preview_session)
      → persist selected activities and grades
      → upsert student enrollment (RN-05)
      → log import to sync_log
  → return ImportResult {activities_imported, grades_imported}
```

---

## Risks / Trade-offs

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Moodle WS timeout o caída durante sync nocturna | Media | Retry con backoff (2 intentos). Sync parcial no bloquea otros dictados. Error queda registrado en sync_log |
| Token Moodle expirado o inválido silenciosamente | Baja | El cliente detecta error de autenticación Moodle (HTTP 403 con "Invalid token") y lo registra con mensaje claro. El admin recibe alerta vía sync_log |
| Archivo .xlsx malformado causa error de parseo | Media | Preview step valida el archivo antes de persistir. Errores de parseo devuelven 400 con detalle de la fila/columna problemática |
| Dos sync simultáneos sobre el mismo dictado (ondemand + nocturno) | Baja | Lock optimista: la tabla `sync_log` con status `running` impide iniciar un nuevo sync si ya hay uno en ejecución para ese dictado |
| Volumen grande de datos (100+ alumnos × 30+ actividades) supera timeout | Media | Timeout configurable. El sync engine procesa en batches. Para MVP no se espera escalar más allá de 1000 alumnos × 50 actividades |
| Clave de cifrado rotada invalida configuraciones Moodle existentes | Baja | El servicio descifra con la clave actual. Si rotó, se debe re-cifrar la config. En MVP esto es manual. Se automatizará cuando haya rotación programada |

---

## Open Questions

1. **Detección de versión Moodle**: ¿se fuerza REST o se negocia automáticamente en el handshake? — Decisión inicial: asumir REST (Moodle 3.1+). Si el tenant usa XML-RPC, se agrega negociación en cambio futuro.
2. **Mapeo dictado → curso Moodle**: ¿el `moodle_course_id` se configura manualmente o se detecta automáticamente? — Inicialmente manual (seed o API de admin). Detección automática (vía `core_course_get_courses`) se agrega en cambio futuro.
3. **¿Se importa el historial completo de calificaciones o solo desde la última sync?** — Inicialmente completo (full sync cada vez). Incremental se evaluará cuando el volumen lo justifique.
4. **Formato de archivo de import manual**: ¿se estandariza un template descargable? — No para MVP. Se parsea cualquier export de Moodle estándar. Si los usuarios reportan inconsistencias, se crea un template en cambio futuro.
