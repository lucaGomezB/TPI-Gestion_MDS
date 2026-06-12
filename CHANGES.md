# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **activia-trace**.
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificar el change a implementar (verificar que sus dependencias están archivadas).
2. Leer los docs de la knowledge-base indicados en "Leer antes".
3. Ejecutar `/opsx:propose <nombre-del-change>`.
4. Al terminar el change, archivarlo con `/opsx:archive <nombre-del-change>`.
5. Marcar el checkbox `[x]` en este archivo.

---

## Árbol de dependencias

```
C-01 foundation-setup
  └── C-02 core-models
        └── C-03 auth-rbac
              │
              ├── C-04 carrera-cohorte-materia
              │     └── C-05 roles-asignaciones
              │           │
              │           ├── C-06 padron-alumnos
              │           │     └── C-07 calificaciones
              │           │           │
              │           │           ├── C-09 atrasados-ranking
              │           │           └── C-10 reportes-calificaciones
              │           │
              │           ├── C-11 cola-comunicaciones
              │           │     ├── C-12 avisos-tablon
              │           │     └── C-13 mensajeria-interna
              │           │
              │           ├── C-14 encuentros-guardias
              │           │
              │           ├── C-15 coloquios
              │           │
              │           └── C-16 tareas-internas
              │
              ├── C-08 moodle-integration             ← paralelo con C-04
              │
              └── C-17 auditoria-log                   ← paralelo con C-04
                    │
                    └── C-18 grilla-salarial
                          ├── C-19 liquidaciones
                          └── C-20 facturacion-docentes
```

### Paralelismo por fase

> Cada "gate" es un punto de sincronización. Los changes dentro de un grupo pueden ejecutarse en paralelo.

```
GATE 0: ~~ninguna~~ ✅
  → C-01 foundation-setup ✅

GATE 1: C-01 ✅
  → C-02 core-models (solo)

GATE 2: C-02 ✓
  → C-03 auth-rbac (solo)

GATE 3: C-03 ✅
  → C-04 carrera-cohorte-materia        [Agente A — Backend Core] ✅
  → C-08 moodle-integration             [Agente B — Backend Aux] ✅
  → C-17 auditoria-log                  [Agente C — Cross-cutting] ✅

GATE 4: C-04 ✓
  → C-05 roles-asignaciones             [Agente A]

GATE 5: C-05 ✓                          ← SEGUNDO GRAN FORK (5 paralelos)
  → C-06 padron-alumnos                 [Agente A]
  → C-11 cola-comunicaciones            [Agente B]
  → C-14 encuentros-guardias            [Agente C]
  → C-16 tareas-internas                [Agente C — si C-14 ✓]
  → C-18 grilla-salarial                [Agente B — si C-11 ✓]

GATE 6: C-06 ✓
  → C-07 calificaciones                 [Agente A]

GATE 7: C-07 ✓
  → C-09 atrasados-ranking              [Agente A]
  → C-10 reportes-calificaciones        [Agente A — si C-09 ✓]

GATE 8: C-11 + C-06 ✓
  → C-12 avisos-tablon                  [Agente B]
  → C-13 mensajeria-interna             [Agente B — si C-12 ✓]

GATE 9: C-14 ✅
  → C-15 coloquios                      [Agente C] ✅

GATE 10: C-18 ✓
  → C-19 liquidaciones                  [Agente B]
  → C-20 facturacion-docentes           [Agente B — si C-19 ✓]
```

### Camino crítico (12 changes — mínimo irreducible)

```
~~C-01~~ → C-02 → C-03 → C-04 → C-05 → C-06 → C-07 → C-09 → C-10 → C-11 → C-12 → C-19
```

### Plan óptimo con 3 agentes

```
Paso │ Agente A (Backend Core)        │ Agente B (Backend Aux)      │ Agente C (Frontend+Cross)
─────┼────────────────────────────────┼─────────────────────────────┼────────────────────────────
  1  │ C-01 foundation-setup ✅       │         —                   │         —
  2  │ C-02 core-models               │         —                   │         —
  3  │ C-03 auth-rbac                 │         —                   │         —
  4  │ C-04 carrera-cohorte-materia   │ C-08 moodle-integration     │ C-17 auditoria-log
  5  │ C-05 roles-asignaciones        │         —                   │         —
  6  │ C-06 padron-alumnos            │ C-11 cola-comunicaciones    │ C-14 encuentros-guardias
  7  │ C-07 calificaciones            │ C-18 grilla-salarial        │ C-16 tareas-internas
  8  │ C-09 atrasados-ranking         │ C-12 avisos-tablon          │ C-15 coloquios ✅
  9  │ C-10 reportes-calificaciones   │ C-13 mensajeria-interna     │         —
 10  │         —                      │ C-19 liquidaciones          │         —
  11  │         —                      │ C-20 facturacion-docentes ✅│         —
```

---

## FASE 0 — Cimientos

### [C-01] `foundation-setup`
- **Estado**: `[x]` archivado
- **Scope**: Scaffolding completo del proyecto + infraestructura base
  - Estructura de directorios: `backend/`, `frontend/`, siguiendo lo definido en `docs/ARQUITECTURA.md`
  - `backend/`: FastAPI app mínima con health check `/api/health`, settings (pydantic-settings), logger estructurado, db session async, estructura de capas vacía
  - `frontend/`: Vite + React 18 + TypeScript + Tailwind scaffolding, Axios configurado, estructura feature-based
  - Dockerfile + docker-compose.yml (app + db + n8n placeholder)
  - `.env.example` con todas las variables de entorno documentadas
  - `SECRET_KEY` y `ENCRYPTION_KEY` generadas en `.env.example` con placeholders
  - GitHub Actions CI: lint + test + build paralelos
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `docs/ARQUITECTURA.md` §2 Stack, §4 Estructura de directorios
  - `knowledge-base/02_descripcion_general.md` §Stack
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios

---

### [C-02] `core-models`
- **Estado**: `[x]` archivado
- **Scope**: Modelos base del sistema + migraciones + seed mínimo
  - Modelos SQLAlchemy: `Tenant`, `Usuario` (con PII cifrada: email, dni, cuil, cbu, alias_cbu)
  - `BaseMixin` con `id` (UUID), `tenant_id`, `created_at`, `updated_at`
  - `AuditMixin` con `estado` (Activo/Inactivo), soft delete
  - `BaseRepository[T]` genérico con scope de tenant automático
  - Migración 001: tablas `tenants`, `usuarios`
  - Seed mínimo: 1 tenant (TUPAD), 1 usuario ADMIN
  - Cifrado AES-256 para campos PII en reposo (core/security.py)
- **Dependencias**: C-01
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E1–E4 (Tenant, Carrera, Materia, Usuario)
  - `knowledge-base/08_arquitectura_propuesta.md` §2 Patrón arquitectónico
  - `docs/ARQUITECTURA.md` §5 Seguridad, §8 Persistencia

---

### [C-03] `auth-rbac`
- **Estado**: `[x]` archivado
- **Scope**: Sistema completo de autenticación + autorización RBAC
  - `POST /api/auth/login` — email + password, 2FA TOTP opcional, JWT access (15 min) + refresh rotation
  - `POST /api/auth/refresh` — refresh con rotación, invalida token anterior
  - `POST /api/auth/logout` — revoca refresh token
  - `POST /api/auth/forgot-password` — token de un solo uso por email
  - `POST /api/auth/reset-password` — cambio de contraseña con token
  - `GET /api/auth/me` — perfil del usuario autenticado
  - Password hashing con Argon2id
  - Matriz RBAC en `core/permissions.py`: roles ALUMNO, TUTOR, PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS
  - Dependency `require_permission("modulo:accion")` para cada endpoint
  - Principio de identidad desde la sesión (JWT): `sub`, `tenant_id`, `roles`, `exp` — sin permisos en el token
  - Migración 002: tablas `roles`, `usuario_roles`, `refresh_tokens`
  - Rate limiting por IP+email en login (5/60s)
  - Tests: login correcto, token expirado, refresh rotation, rate limit, 2FA
- **Dependencias**: C-02
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §2 Roles, §4 Matriz de permisos
  - `knowledge-base/07_flujos_principales.md` FL-01 (Autenticación)
  - `docs/ARQUITECTURA.md` §5 Modelo de seguridad

---

## FASE 1 — Estructura Académica

### [C-04] `carrera-cohorte-materia`
- **Estado**: `[x]` archivado
- **Scope**: Estructura académica base del tenant
  - Modelos: `Carrera`, `Cohorte`, `Materia`, `ProgramaMateria`
  - `POST/GET/PUT /api/admin/carreras` — CRUD de carreras
  - `POST/GET/PUT /api/admin/cohortes` — CRUD de cohortes (con FK a carrera)
  - `POST/GET/PUT /api/admin/materias` — CRUD de materias (catálogo único por tenant)
  - Validez única: `(tenant_id, codigo)` para Carrera y Materia
  - Cohorte: estados Activa/Inactiva, vig_desde/vig_hasta
  - ProgramaMateria: subida de PDF con referencia a almacenamiento
  - Migración 003: tablas `carreras`, `cohortes`, `materias`, `programas_materia`
  - Tests: CRUD, unicidad, aislamiento multi-tenant
- **Dependencias**: C-03
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E1–E3 (Carrera, Cohorte, Materia), E16 (ProgramaMateria)
  - `knowledge-base/06_funcionalidades.md` Épica 5 — Estructura Académica
  - `knowledge-base/05_reglas_de_negocio.md` §Equipos Docentes

---

### [C-05] `roles-asignaciones`
- **Estado**: `[x]` archivado
- **Scope**: Asignación de roles docentes con contexto académico y vigencia
  - Modelo: `Asignacion` (Usuario × Rol × Materia × Cohorte × Carrera × Comisiones × Vigencia)
  - Jerarquía: `responsable_id` (FK → Usuario, coordinador que supervisa)
  - `POST/GET/PUT /api/admin/asignaciones` — CRUD individual
  - `POST /api/admin/asignaciones/masiva` — asignación masiva de docentes
  - `POST /api/admin/asignaciones/clonar` — clonado de equipo entre cohortes (RN-12)
  - `PUT /api/admin/asignaciones/vigencia` — modificar vigencia general en bloque
  - `GET /api/admin/equipos/export` — exportar equipo docente
  - Vigencia: `vig_desde`/`vig_hasta`, estado derivado Vigente/Vencida por fechas (RN-10)
  - Migración 004: tablas `asignaciones` + índices compuestos
  - Tests: CRUD, clonado, vigencia, scope multi-tenant, export
- **Dependencias**: C-04
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E5 (Asignacion)
  - `knowledge-base/06_funcionalidades.md` Épica 4 — Gestión de Equipos Docentes
  - `knowledge-base/05_reglas_de_negocio.md` RN-10, RN-11, RN-12, RN-30

---

## FASE 2 — Ingesta de Datos

### [C-06] `padron-alumnos`
- **Estado**: `[x]` archivado
- **Scope**: Padrón versionado de alumnos por materia
  - Modelos: `VersionPadron`, `EntradaPadron`
  - Import de `.xlsx`/`.csv`: procesamiento con detección de columnas
  - Versionado: nueva versión desactiva la anterior (histórico preservado)
  - `POST /api/materias/{id}/padron/importar` — importar padrón
  - `GET /api/materias/{id}/padron` — listar entradas activas
  - `GET /api/materias/{id}/padron/versiones` — historial de versiones
  - Cifrado de email del alumno en EntradaPadron
  - Migración 005: tablas `versiones_padron`, `entradas_padron`
  - Tests: import exitoso, versionado, rollback en error, multi-tenant
- **Dependencias**: C-05
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E6 (Padrón)
  - `knowledge-base/06_funcionalidades.md` F1.3 (Import padrón)
  - `knowledge-base/05_reglas_de_negocio.md` RN-05

---

### [C-07] `calificaciones`
- **Estado**: `[x]` archivado
- **Scope**: Importación de calificaciones con detección de actividades
  - Modelos: `Calificacion`, `UmbralMateria`
  - Import de `.xlsx`/`.csv`: detección de columnas `(Real)` para nota numérica (RN-01)
  - Mapeo de escala textual configurable por tenant (RN-02)
  - Vista previa de actividades detectadas antes de confirmar importación
  - Umbral configurable por asignación × materia (default 60%, RN-03)
  - `POST /api/materias/{id}/calificaciones/importar` — importar calificaciones
  - `GET /api/materias/{id}/calificaciones` — listar calificaciones
  - `DELETE /api/materias/{id}/calificaciones` — vaciar datos scope-isolated (RN-04)
  - Derivación de campo `aprobado` según umbral numérico o conjunto textual aprobatorio
  - Migración 006: tablas `calificaciones`, `umbrales_materia`
  - Tests: import, detección de columnas, umbral, vaciado scope-isolated
- **Dependencias**: C-06
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E7 (Calificacion), E8 (UmbralMateria)
  - `knowledge-base/06_funcionalidades.md` F1.1, F1.5
  - `knowledge-base/05_reglas_de_negocio.md` RN-01, RN-02, RN-03, RN-04

---

## FASE 3 — Análisis y Reportes

### [C-09] `atrasados-ranking`
- **Estado**: `[x]` archivado
- **Scope**: Detección de alumnos atrasados + ranking de aprobadas
  - `GET /api/materias/{id}/atrasados` — listar atrasados (faltantes o nota < umbral, RN-06)
  - `GET /api/materias/{id}/ranking` — ranking de aprobadas (RN-09)
  - `GET /api/materias/{id}/reportes` — reportes rápidos con métricas clave
  - Filtros: materia, comisión, rango de fechas, búsqueda por alumno
  - Export: atrasados y ranking a formato descargable
  - Tests: detección correcta, ranking excluye sin aprobadas, scope multi-tenant
- **Dependencias**: C-07
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` Épica 2 — Análisis y Reportes (F2.1–F2.6)
  - `knowledge-base/05_reglas_de_negocio.md` RN-06, RN-07, RN-08, RN-09
  - `knowledge-base/07_flujos_principales.md` FL-02 (profesor detecta atrasados)

---

### [C-10] `reportes-calificaciones`
- **Estado**: `[ ]` pendiente
- **Scope**: Reportes avanzados + exportación de notas finales
  - `GET /api/materias/{id}/notas-finales` — notas finales agrupadas por alumno
  - `GET /api/materias/{id}/export/atrasados` — exportar TP sin corregir (RN-07, RN-08)
  - `GET /api/admin/monitor/actividades` — monitor general de actividades (COORDINADOR, ADMIN)
  - `GET /api/materias/{id}/seguimiento` — monitor de seguimiento por alumno
  - Filtros avanzados: rango de fechas, regional, comisión, estado de actividad
  - Tests: cálculo de nota final, export, filtros multi-tenant
- **Dependencias**: C-09
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` F2.4–F2.9
  - `knowledge-base/05_reglas_de_negocio.md` RN-07, RN-08

---

## FASE 4 — Comunicaciones

### [C-11] `cola-comunicaciones` (archivado)
- **Estado**: `[x]` archivado
- **Scope**: Cola de comunicaciones con estados, template engine y worker async
  - Modelo: `Comunicacion` con estados Pend → Send → OK/Fail y Pend → Canc (RN-15)
  - Template engine: variables `{{alumno.nombre}}`, `{{materia.nombre}}` (RF-20)
  - `POST /api/materias/{id}/comunicaciones/preview` — preview obligatorio antes de enviar (RN-16)
  - `POST /api/materias/{id}/comunicaciones/enviar` — encolar envío masivo
  - `GET /api/materias/{id}/comunicaciones` — tracking de estado en tiempo real
  - Worker async: procesa cola Pend → OK/Fail, con reintentos
  - Aprobación humana opcional por tenant (RN-17): si activa, envíos masivos requieren aprobación
  - `PUT /api/admin/comunicaciones/{id}/aprobar` — aprobar/rechazar envío
  - Migración 007: tablas `comunicaciones`, `lotes_comunicaciones`
  - Tests: ciclo de vida completo, preview, template rendering, aprobación
- **Dependencias**: C-05
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E21 (Cola de comunicaciones)
  - `knowledge-base/06_funcionalidades.md` Épica 3 — Comunicación (F3.1–F3.3)
  - `knowledge-base/05_reglas_de_negocio.md` RN-15, RN-16, RN-17

---

### [C-12] `avisos-tablon`
- **Estado**: `[x]` archivado
- **Scope**: Tablón de avisos del sistema con scope, vigencia y acknowledgment
  - Modelos: `Aviso`, `AcknowledgmentAviso`
  - `POST/GET/PUT/DELETE /api/admin/avisos` — CRUD de avisos
  - Alcances: Global, PorMateria, PorCohorte, PorRol
  - Severidad: Info, Advertencia, Crítico
  - Vigencia: `inicio_en`/`fin_en`, orden de presentación
  - `require_ack`: flag que obliga al usuario a confirmar lectura
  - `GET /api/avisos` — avisos visibles para el usuario autenticado
  - `POST /api/avisos/{id}/ack` — confirmar lectura
  - Migración 008: tablas `avisos`, `acknowledgments_avisos`
  - Tests: CRUD, scope filtering, vigencia, multi-tenant
- **Dependencias**: C-11
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E13 (Aviso)
  - `knowledge-base/06_funcionalidades.md` F3.5
  - `knowledge-base/05_reglas_de_negocio.md` RN-18, RN-19, RN-20

---

### [C-13] `mensajeria-interna`
- **Estado**: `[x]` archivado
- **Scope**: Bandeja de mensajes internos docente ↔ coordinación
  - Modelo de mensajes con threads (hilos + respuestas)
  - `GET /api/mensajes` — bandeja de entrada del usuario autenticado
  - `GET /api/mensajes/{id}` — ver hilo completo
  - `POST /api/mensajes` — enviar mensaje a otro usuario del mismo tenant
  - `POST /api/mensajes/{id}/responder` — responder dentro del hilo
  - Notificaciones internas (contador de no leídos)
  - Migración 009: tablas `mensajes`, `hilos_mensajes`
  - Tests: envío, recepción, threads, multi-tenant (no cruzar)
- **Dependencias**: C-12
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` F3.4 (Mensajería interna), F11.2 (Bandeja)
  - `knowledge-base/03_actores_y_roles.md` §4 Matriz de permisos

---

## FASE 5 — Encuentros y Guardias

### [C-14] `encuentros-guardias`
- **Estado**: `[x]` archivado
- **Scope**: Gestión de slots de encuentro, instancias y guardias
  - Modelos: `SlotEncuentro`, `InstanciaEncuentro`, `Guardia`
  - `POST /api/materias/{id}/encuentros/slot` — crear slot recurrente (F6.1)
  - `POST /api/materias/{id}/encuentros/unico` — crear encuentro único (F6.2)
  - Generación automática de N instancias desde slot recurrente
  - `PUT /api/encuentros/{id}` — editar instancia individual (estado, meet, video, comentario — RN-14)
  - `POST /api/materias/{id}/encuentros/embed` — generar snippet HTML para Moodle
  - `GET /api/admin/encuentros` — vista transversal de todos los encuentros
  - `POST /api/materias/{id}/guardias` — registro de guardias (F6.6)
  - `GET /api/materias/{id}/guardias` — consulta de guardias
  - Migración 010: tablas `slots_encuentro`, `instancias_encuentro`, `guardias`
  - Tests: slots recurrentes, edición de instancia, guardias, multi-tenant
- **Dependencias**: C-05
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E9 (SlotEncuentro), E10 (InstanciaEncuentro), E11 (Guardia)
  - `knowledge-base/06_funcionalidades.md` Épica 6 — Encuentros y Disponibilidad
  - `knowledge-base/05_reglas_de_negocio.md` RN-13, RN-14

---

### [C-15] `coloquios`
- **Estado**: `[x]` archivado
- **Scope**: Convocatorias de coloquio con reservas y resultados
  - Modelos: `Evaluacion` (tipo coloquio), `ReservaEvaluacion`, `ResultadoEvaluacion`
  - `POST /api/materias/{id}/coloquios` — crear convocatoria con días y cupos (F7.3)
  - `POST /api/materias/{id}/coloquios/importar-alumnos` — importar padrón de convocados
  - `POST /api/coloquios/{id}/reservar` — reserva de alumno (cupos auto-decrecientes)
  - `GET /api/coloquios/{id}/agenda` — agenda consolidada de reservas
  - `POST /api/coloquios/{id}/resultados` — registrar resultados
  - `GET /api/admin/coloquios/metricas` — panel de métricas (convocados, reservas, notas)
  - Migración 011: tablas `evaluaciones`, `reservas_evaluacion`, `resultados_evaluacion`
  - Tests: convocatoria, reserva con cupos, resultados, multi-tenant
- **Dependencias**: C-14
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E14 (Evaluación)
  - `knowledge-base/06_funcionalidades.md` Épica 7 — Coloquios
  - `knowledge-base/07_flujos_principales.md` §Journey 3 (alumno consulta estado)

---

## FASE 6 — Tareas Internas

### [C-16] `tareas-internas`
- **Estado**: `[x]` archivado
- **Scope**: Workflow de tareas internas con asignación y comentarios
  - Modelos: `Tarea`, `ComentarioTarea`
  - `GET /api/tareas` — vista de mis tareas asignadas (F8.1)
  - `POST /api/tareas` — asignar tarea a otro docente (F8.2)
  - `PUT /api/tareas/{id}/estado` — cambiar estado (Pendiente → En progreso → Resuelta)
  - `POST /api/tareas/{id}/comentarios` — agregar comentario al hilo
  - `GET /api/admin/tareas` — administración global de tareas con filtros (F8.3)
  - Migración 012: tablas `tareas`, `comentarios_tarea`
  - Tests: CRUD, cambio de estado, comentarios, multi-tenant
- **Dependencias**: C-05
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E12 (Tarea)
  - `knowledge-base/06_funcionalidades.md` Épica 8 — Workflow de Tareas Internas

---

## FASE 7 — Multi-tenancy y Auditoría

### [C-08] `moodle-integration`
- **Estado**: `[x]` archivado
- **Scope**: Integración con Moodle Web Services + sync programada
  - Cliente Moodle WS en `integrations/moodle_ws.py` (abstracto del core)
  - Funciones: `core_grades_get_grades`, `core_enrol_get_enrolled_users`, `core_user_get_users`
  - Sync nocturna automática (schedule via worker async)
  - Sync on-demand desde interfaz (`POST /api/materias/{id}/sync-moodle`)
  - Fallback: import manual `.xlsx`/`.csv` para tenants sin acceso WS (RF-07)
  - Configuración por tenant: `MOODLE_WS_URL`, `MOODLE_WS_TOKEN`
  - Error handling: errores mapean a HTTP 502 + retry
  - Variables de entorno por tenant en configuración
  - Tests: mock de Moodle WS, fallback, sync on-demand
- **Dependencias**: C-03
- **Governance**: ALTO
- **Leer antes**:
  - `docs/ARQUITECTURA.md` §7.1 Moodle Web Services
  - `knowledge-base/06_funcionalidades.md` Épica 1 — Ingesta (F1.1–F1.4)
  - `knowledge-base/05_reglas_de_negocio.md` RN-01, RN-02

---

### [C-17] `auditoria-log`
- **Estado**: `[x]` archivado
- **Scope**: Audit log append-only con búsqueda full-text
  - Modelo: `AuditLog` (append-only, sin límite de retención)
  - Middleware de auditoría: intercepta acciones significativas y registra automáticamente
  - `GET /api/admin/auditoria` — búsqueda full-text con filtros (acción, usuario, materia, fecha, IP)
  - `GET /api/admin/auditoria/docentes/{id}/interacciones` — panel de interacciones por docente (F9.1)
  - Campos registrados: actor_id, impersonado_id, materia_id, accion, detalle (JSON), filas_afectadas, IP, user_agent
  - Códigos de acción estandarizados: `CALIFICACIONES_IMPORTAR`, `PADRON_CARGAR`, `COMUNICACION_ENVIAR`, etc.
  - Exportación de resultados de búsqueda
  - Migración 013: tabla `audit_log` con índices para búsqueda
  - Tests: registro, búsqueda, append-only, impersonación
- **Dependencias**: C-03
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E-AUD (Log de auditoría)
  - `knowledge-base/06_funcionalidades.md` Épica 9 — Auditoría y Métricas
  - `knowledge-base/05_reglas_de_negocio.md` RN-23, RN-24

---

## Infraestructura — Cross-cutting

### [UoW] `uow-refactor`
- **Estado**: `[x]` archivado
- **Scope**: Unit of Work pattern — transaction management centralizado.
- **Dependencias**: C-17
- **Governance**: ALTO

---

## FASE 8 — Liquidaciones y Facturación

### [C-18] `grilla-salarial`
- **Estado**: `[x]` archivado
- **Scope**: Configuración de salario base y plus con vigencia temporal
  - Modelos: `SalarioBase` (rol × monto × vigencia), `SalarioPlus` (grupo × rol × monto × vigencia)
  - `POST/GET/PUT /api/admin/salarios/base` — ABM de salario base (RN-31)
  - `POST/GET/PUT /api/admin/salarios/plus` — ABM de plus salarial (RN-32, RN-33)
  - Validación: solo una entrada vigente por rol en un instante dado
  - Claves de grupo de materias configurables por tenant (PA-22)
  - Migración 014: tablas `salarios_base`, `salarios_plus`
  - Tests: CRUD, solapamiento de vigencia, multi-tenant
- **Dependencias**: C-17
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E17 (SalarioBase), E18 (SalarioPlus)
  - `knowledge-base/06_funcionalidades.md` F10.4 (Administración de grilla salarial)
  - `knowledge-base/05_reglas_de_negocio.md` RN-31, RN-32, RN-33

---

### [C-19] `liquidaciones`
- **Estado**: `[x]` archivado
- **Scope**: Cálculo, cierre e historial de liquidaciones de honorarios
  - Modelo: `Liquidacion` con desglose: base, plus, total, es_nexo, excluido_por_factura
  - Cálculo = SalarioBase vigente + Suma de SalarioPlus aplicables por grupo de materias
  - `GET /api/admin/liquidaciones?periodo=YYYY-MM` — vista de liquidaciones del período (F10.1)
  - `GET /api/admin/liquidaciones/{id}` — detalle individual con desglose
  - `POST /api/admin/liquidaciones/{id}/cerrar` — cierre = inmutabilizar (RN-22)
  - `GET /api/admin/liquidaciones/historial` — historial de liquidaciones cerradas (F10.3)
  - Tratamiento diferenciado: NEXO suma al total pero se muestra aparte (RN-36, RN-37)
  - Docentes facturadores excluidos del total (RN-35)
  - Vista con KPIs: "Total sin factura", "Total con factura" (F10.6)
  - Migración 015: tabla `liquidaciones` con índices por periodo
  - Tests: cálculo, cierre, inmutabilidad, exclusión facturadores
- **Dependencias**: C-18
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E19 (Liquidacion)
  - `knowledge-base/06_funcionalidades.md` F10.1–F10.3, F10.6
  - `knowledge-base/05_reglas_de_negocio.md` RN-22, RN-35, RN-36, RN-37, RN-38

---

### [C-20] `facturacion-docentes`
- **Estado**: `[x]` archivado
- **Scope**: Gestión de facturas de docentes monotributistas
  - Modelo: `Factura` (usuario_id, periodo, detalle, PDF, estado Pendiente/Abonada)
  - `POST /api/docentes/facturas` — subir factura mensual en PDF (RF-61)
  - `GET /api/docentes/facturas` — historial del propio docente
  - `GET /api/admin/facturas` — gestión admin con filtros (docente, estado, fechas, F10.5)
  - `PUT /api/admin/facturas/{id}/abonar` — marcar como abonada + descarga PDF
  - Validación: solo usuarios con `facturador=true` pueden subir facturas
  - Regla: facturadores NO se incluyen en liquidación general (RN-35)
  - Migración 016: tabla `facturas`
  - Tests: subida, validación facturador, ABONADA, multi-tenant
- **Dependencias**: C-19
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` E20 (Factura)
  - `knowledge-base/06_funcionalidades.md` F10.5
  - `knowledge-base/05_reglas_de_negocio.md` RN-35

---

## FASE 9 — Frontend

> Los cambios de frontend se proponen DESPUÉS de que sus respectivos endpoints backend existen.
> Verificar que el change backend correspondiente esté archivado antes de proponer el frontend.

### [C-21] `frontend-foundation`
- **Estado**: `[ ]` pendiente
- **Scope**: Foundation del frontend + flujo de autenticación completo
  - Vite + React 18 + TypeScript + Tailwind CSS configurados
  - Cliente Axios centralizado en `shared/services/api.ts` con interceptor JWT/refresh
  - React Query (TanStack Query) configurado para server state
  - React Hook Form + Zod para formularios
  - Feature-based modules: `features/{auth,dashboard,...}/{components,hooks,services,types,pages}`
  - Página de login + 2FA + recuperación de contraseña
  - Auth context/provider con manejo de JWT y refresh automático
  - Protected routes con redirect a login
  - Layout principal: sidebar con navegación sensible a permisos
  - Lazy loading de páginas
  - Estados: loading, error, empty para cada vista
- **Dependencias**: C-03
- **Governance**: MEDIO
- **Leer antes**:
  - `docs/ARQUITECTURA.md` §4 Estructura de directorios (frontend/)
  - `knowledge-base/03_actores_y_roles.md` (para entender qué ve cada rol)
  - `knowledge-base/07_flujos_principales.md` FL-01 (login flow)

---

### [C-22] `frontend-materias`
- **Estado**: `[ ]` propuesto
- **Scope**: Dashboard del profesor con vista de materias, calificaciones, atrasados y ranking
  - Página "Mi Semana": KPIs por materia (atrasados, sin corregir, próximos parciales)
  - Vista detallada de materia: importar calificaciones, umbral configurable
  - Lista de atrasados con filtros (F2.2)
  - Ranking de aprobadas (F2.3)
  - Reportes rápidos y notas finales agrupadas (F2.4, F2.5)
  - Exportación de TP sin corregir (F2.6)
  - Monitor de seguimiento de alumnos (F2.8)
  - Estados: loading, error, empty (sin datos importados aún)
- **Dependencias**: C-07, C-09, C-10, C-21
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` Épica 2 — Análisis y Reportes
  - `knowledge-base/07_flujos_principales.md` FL-02

---

### [C-23] `frontend-equipos`
- **Estado**: `[ ]` pendiente
- **Scope**: Gestión de equipos docentes y estructura académica
  - ABM de carreras, cohortes, materias (F5.1, F5.2, F5.3)
  - ABM de usuarios docentes (F4.1)
  - Asignaciones individuales y masivas (F4.3, F4.4)
  - Clonado de equipo entre cohortes (F4.5)
  - Modificar vigencia general (F4.6)
  - Exportar equipo (F4.7)
  - Vista "Mis equipos" para el docente (F4.2)
  - Subida de programas PDF (F5.3)
  - Calendario de fechas académicas (F5.4)
- **Dependencias**: C-04, C-05, C-21
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` Épica 4 — Equipos, Épica 5 — Estructura
  - `knowledge-base/03_actores_y_roles.md` §Matriz de permisos

---

### [C-24] `frontend-comunicaciones`
- **Estado**: `[x]` archivado
- **Scope**: Cola de comunicaciones, avisos y mensajería interna
  - Vista previa de mail antes de envío (F3.1)
  - Envío masivo con tracking de estado (F3.2)
  - Aprobación de envíos (F3.3)
  - Tablón de avisos: lista, crear, editar, ACK (F3.5)
  - Bandeja de mensajes internos con threads (F3.4, F11.2)
  - Estados: loading, error, empty
- **Dependencias**: C-11, C-12, C-13, C-21
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` Épica 3 — Comunicación
  - `knowledge-base/05_reglas_de_negocio.md` RN-15–RN-20

---

### [C-25] `frontend-encuentros`
- **Estado**: `[x]` archivado
- **Scope**: Encuentros, guardias y coloquios
  - Crear slot recurrente / encuentro único (F6.1, F6.2)
  - Editar instancia de encuentro (F6.3)
  - Generar snippet embed para Moodle (F6.4)
  - Vista transversal de encuentros (F6.5)
  - Registro y consulta de guardias (F6.6)
  - Convocatorias de coloquio con reservas (F7.1–F7.5)
  - Estados: loading, error, empty
- **Dependencias**: C-14, C-15, C-21
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` Épica 6 — Encuentros, Épica 7 — Coloquios
  - `knowledge-base/04_modelo_de_datos.md` E9, E10, E11, E14

---

### [C-26] `frontend-liquidaciones`
- **Estado**: `[ ]` pending
- **Scope**: Grilla salarial, liquidaciones y facturación
  - Administración de grilla salarial (Base + Plus) (F10.4)
  - Vista de liquidaciones del período con desglose (F10.1)
  - Cerrar liquidación (F10.2)
  - Historial de liquidaciones (F10.3)
  - Separación contable: NEXO + facturadores (F10.6)
  - Subida y gestión de facturas de monotributistas (F10.5)
  - Estados: loading, error, empty
- **Dependencies**: C-18, C-19, C-20, C-21
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` Épica 10 — Liquidaciones
  - `knowledge-base/05_reglas_de_negocio.md` RN-31–RN-38

---

### [C-28] `frontend-calendario-evaluaciones`
- **Estado**: `[ ]` propuesto
- **Scope**: Gestion de fechas de evaluaciones
  - ABM de fechas de parciales, TPs y coloquios por materia y cohorte (F5.4, HU-24)
  - Vista tabular de evaluaciones con filtros
  - Vista calendario visual de evaluaciones
  - Generacion de snippet embebible para LMS (Moodle)
  - Estados: loading, error, empty
- **Dependencies**: C-04, C-21, C-23
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` \u00a7F5.4
  - `knowledge-base/11_historias_de_usuario.md` HU-24

---

### [C-27] `frontend-auditoria`
- **Estado**: `[x]` archivado
- **Scope**: Panel de auditoría y monitoreo
  - Panel de interacciones con gráficos (acciones/día, F9.1)
  - Log de auditoría con búsqueda full-text (F9.2)
  - Filtros: fecha, usuario, materia, acción, IP
  - Panel de interacciones por docente
  - Estados: loading, error, empty
  - Paginación y exportación de resultados
- **Dependencies**: C-17, C-21
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` Épica 9 — Auditoría
  - `knowledge-base/04_modelo_de_datos.md` E-AUD

---

## CHANGES.md generado

✅ `CHANGES.md` creado en la raíz con **27 changes** organizados en **10 fases**.

**Camino crítico**: 12 changes (C-01 → C-02 → C-03 → C-04 → C-05 → C-06 → C-07 → C-09 → C-10 → C-11 → C-12 → C-19)

**Gates de paralelismo**: 11 gates, máximo 5 changes en paralelo (GATE 5)

**Primer change recomendado**: `/opsx:propose C-01-foundation-setup`
