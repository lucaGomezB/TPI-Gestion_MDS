# activia-trace — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`.
>
> **IMPORTANTE**: SIEMPRE IR DIRECTO AL GRANO. Sin rodeos, sin explicaciones de más, sin preguntas retóricas.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Base de datos | PostgreSQL (JSONB para criterios configurables) |
| Frontend | React 18, TypeScript, Vite, TanStack Query, React Hook Form + Zod, Tailwind CSS |
| Autenticación | JWT (access 15 min + refresh rotation), Argon2id, 2FA TOTP |
| Cifrado en reposo | AES-256 para PII (CBU, DNI, email) |
| Infraestructura | Docker + docker-compose, Easypanel |
| Integraciones | Moodle Web Services, N8N (workflows) |
| Testing | pytest, coverage ≥80% líneas, ≥90% reglas de negocio |
| Observabilidad | Logs JSON estructurados + OpenTelemetry |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md) · [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito, alcance y fuera de alcance |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Auth, RBAC, matriz de permisos, roles del dominio |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades (E1–E21), ERD, migraciones, cifrado PII |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas (RN-01 a RN-40) por dominio |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Funcionalidades por épica (F1.1–F12.1) |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E: auth, importación calificaciones, setup cuatrimestre |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrón Clean Architecture, capas, principios rectores |
| [11_historias_de_usuario.md](knowledge-base/11_historias_de_usuario.md) | HUs con criterios de aceptación, cruzadas con RF y RN |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Inconsistencias de dominio a validar |
| [docs/PRD.md](docs/PRD.md) | Product Requirements Document completo (RF-01 a RF-63) |
| [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md) | Arquitectura detallada: ADRs, seguridad, multi-tenancy, integraciones |

---

## Skills Disponibles

Cargá la skill correspondiente al contexto ANTES de escribir código.
Ver detalle completo en [`.agents/SKILLS.md`](.agents/SKILLS.md) — rutas, triggers por skill y referencias compartidas.

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Backend Core** | FastAPI / SQLAlchemy / Alembic / modelos / repositorios | `fastapi-templates`, `test-driven-development`, `sdd-apply`, `systematic-debugging` |
| **Backend Aux** | Servicios, integraciones Moodle/N8N, workers, tests | `sdd-apply`, `test-driven-development`, `systematic-debugging` |
| **Frontend** | React / TypeScript / TanStack Query / Tailwind | `sdd-apply`, `test-driven-development`, `code-review-excellence` |
| **Orquestación** | OPSX / SDD / openspec / changes | `sdd-propose`, `sdd-design`, `sdd-spec`, `sdd-tasks`, `sdd-verify`, `sdd-archive`, `openspec-init`, `openspec-onboard` |

Las skills viven en `.agents/skills/` y estan versionadas en el repositorio.

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 27 changes en 10 fases.
- **Camino crítico** (12): `C-01 → C-02 → C-03 → C-04 → C-05 → C-06 → C-07 → C-09 → C-10 → C-11 → C-12 → C-19`.
- **Primer change**: `C-01 foundation-setup`.

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras (no negociables)

Estas reglas son **contrato**. Romperlas es un defecto, no una decisión de estilo.

1. **No buildear automático.** Nunca ejecutar build/compile/bundle sin pedido explícito del usuario.
2. **No commitear sin pedido explícito.** `git add`/`commit`/`push` SOLO cuando el usuario lo pide. Si estás en la rama default, ramificá antes.
3. **Conventional Commits sin `Co-Authored-By`.** Formato `tipo(scope): mensaje` (feat, fix, chore, refactor, test, docs). JAMÁS agregar atribución a IA ni `Co-Authored-By`.
4. **Tests sin mocks de DB.** Usar base real o contenedor de test (testcontainers / DB efímera). Mockear la base de datos invalida el test — no prueba nada.
5. **Pydantic schemas con `extra='forbid'`.** Todo schema rechaza campos no declarados (`model_config = ConfigDict(extra='forbid')`).
6. **snake_case en Python.** Funciones, variables, columnas de BD, módulos y paquetes.
7. **PascalCase en componentes React.** Nombre del componente y del archivo (`ProductCard.tsx`).

---

## Convenciones del proyecto

### Commits
```
<tipo>(<scope>): <descripción>
```
- **Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
- **Scopes**: `auth`, `tenancy`, `users`, `alumnos`, `materias`, `comisiones`, `entregas`, `comunicacion`, `equipos`, `encuentros`, `coloquios`, `liquidaciones`, `auditoria`, `moodle`, `api`, `ui`

### Clean Architecture (backend)
```
Routers → Services → Repositories → Models → PostgreSQL
```
- **Nunca** lógica de negocio en Routers.
- **Nunca** acceso directo a DB desde Services (siempre vía Repository).
- Todo Repository filtra por `tenant_id` por defecto — un query sin scope de tenant es bug.
- Soft delete siempre (audit). Nunca hard delete.
- Máximo 500 LOC por archivo backend.
- Secretos (API keys, tokens externos) **siempre** AES-256 — jamás en texto plano.
- Validar permisos por rol **en cada endpoint** vía `require_permission("modulo:accion")`.

### Frontend
- Feature-based modules: `features/{nombre}/{components,hooks,services,types,pages}`
- Componentes funcionales TypeScript, <200 LOC por archivo.
- Pages lazy-loaded. Loading + error + empty states **siempre** presentes.
- Todo fetch pasa por hooks de `services/` con React Query.
- Axios centralizado en `shared/services/api.ts` con interceptor JWT/refresh.

### Multi-tenancy
- Columna `tenant_id` en toda tabla.
- `tenant_id` se resuelve del JWT, nunca de un parámetro de request.
- Datos **jamás cruzan tenants** — test obligatorio de aislamiento.

### Manejo de errores (API)
| Situación | Respuesta |
|-----------|-----------|
| Validación | `400` |
| No autenticado | `401` |
| Sin permiso | `403` |
| No encontrado | `404` |
| Error integración externa | `502` + retry |
| Error interno | `500` + log detallado |

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks
4. Implementar las tasks (cargando skills)       → respetando las reglas duras
5. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
