## Context

La grilla salarial (C-18) es el primer cambio de la Epica 10 (Liquidaciones y Honorarios, F10.4). Define los valores base por rol y los plus por categoria de materia que el modulo de liquidaciones (C-19) consumira para calcular honorarios docentes. Los datos son configurados por FINANZAS con permiso `liquidaciones:configurar-salarios`.

El proyecto ya tiene Clean Architecture activa con patron UoW, multi-tenancy por JWT, soft-delete en todas las entidades y mixins base (`AppModel`, `TimestampMixin`, `TenantMixin`). No hay modelos de grilla existentes.

Las reglas de negocio aplicadas son RN-31 (vigencia temporal abierta), RN-32 (base fija por rol) y RN-33 (plus por categoria x rol con acumulacion N veces).

## Goals / Non-Goals

**Goals:**
- Modelos SQLAlchemy para SalarioBase, SalarioPlus y GrupoMateria con multi-tenancy
- CRUD de salario base por rol con validacion de vigencia no superpuesta
- CRUD de plus salarial por (grupo, rol) con validacion similar
- CRUD de grupos de materia como catalogo configurable por tenant
- Fechas `desde` (obligatoria) y `hasta` (nullable = vigente sin limite)
- Endpoints protegidos con permiso `liquidaciones:configurar-salarios`
- Servicio de consulta que retorne valores vigentes para una fecha dada (insumo para C-19)

**Non-Goals:**
- Calculo de liquidaciones (C-19)
- Importacion masiva de grillas desde archivo
- Historial de cambios (el versionado por fechas cubre la trazabilidad)
- Cache de valores vigentes (el volumen es bajo, consulta directa a DB)

## Decisions

### 1. GrupoMateria como entidad separada (no JSONB en Materia)
- **Opciones**: (a) JSONB con clave/grupo en Materia, (b) tabla separada GrupoMateria + relacion N:N con Materia via tabla intermedia
- **Decision**: Tabla separada `GrupoMateria` con relacion N:N via `MateriaGrupo`
- **Razon**: Un grupo de materias (ej: "PROG") es configurable por tenant y una materia puede pertenecer a multiples grupos. JSONB en Materia complicaria las queries de "todas las materias del grupo X" necesarias para liquidacion.
- **Alternativa descartada**: JSONB `grupos` array en Materia -- no permite FK, no escala con joins de liquidacion.

### 2. Enum de roles hardcodeado (no dinamico)
- **Opciones**: (a) Enum Python `RolSalarial`, (b) texto libre, (c) FK a tabla roles
- **Decision**: Enum Python `RolSalarial` con valores COORDINADOR, NEXO, PROFESOR, TUTOR
- **Razon**: RN-32 define explicitamente estos 4 roles como los unicos con base salarial. Coincide con el enum de `Asignacion.rol`. Texto libre permitiria errores tipograficos; FK a roles agregaria complejidad innecesaria (los roles de dominio son fijos).
- **Alternativa descartada**: FK a tabla `roles` -- los roles liquidables son un subconjunto fijo, no un catalogo extensible.

### 3. Validacion de solapamiento de vigencias en servicio, no en DB
- **Opciones**: (a) Exclusion constraint en PostgreSQL, (b) validacion en servicio antes de insert/update
- **Decision**: Validacion en servicio + unique constraint en `(tenant_id, rol, desde)` para evitar duplicados exactos
- **Razon**: La regla "solo una entrada vigente por rol en un instante" requiere solapamiento de rangos, no igualdad exacta. Exclusion constraints en PG son especificas del motor. Unico servicio es mas portable y permite mensajes de error claros. La unique constraint cubre el caso de insercion exacta del mismo `(tenant, rol, desde)`.
- **Alternativa descartada**: Exclusion constraint `daterange` en PG -- acopla a PG, migraciones mas complejas.

### 4. GrupoMateria con clave textual configurable por tenant
- **Decision**: `grupo` es texto libre validado (longitud 1-20, alfanumerico + guiones). Cada tenant define sus propias claves. No hay catalogo global de grupos.
- **Razon**: Los grupos de materia son especificos de cada institucion. Un tenant puede tener "PROG", otro "MAT". No tendria sentido un catalogo compartido.

### 5. Soft-delete NO aplica a grilla salarial
- **Decision**: Las tablas de grilla NO usan `AuditMixin`. Solo tienen `created_at`/`updated_at` (TimestampMixin).
- **Razon**: El versionado por fechas (`desde`/`hasta`) ya cumple la funcion de trazabilidad. Si un valor dejo de estar vigente, se pone `hasta`. No tiene sentido soft-delete sobre una tabla que es historica por naturaleza. Un hard-delete accidental romperia liquidaciones pasadas (FK).
- **Alternativa descartada**: `AuditMixin` con soft-delete -- confunde `deleted_at` con `hasta`. Dos conceptos de "fin" en la misma entidad.

## Risks / Trade-offs

- [Validacion de overlap] La validacion en servicio tiene race condition si dos requests simultaneos intentan crear la misma entrada. Mitigacion: unique constraint + try/except en servicio con retry.
- [Performance] Las queries de "valor vigente en fecha X" requieren indice compuesto por `(tenant_id, rol, desde, hasta)`. Sin indice, full-scan en grillas grandes.
- [Rol enum] Si en el futuro se agregan nuevos roles liquidables, hay que actualizar el enum en Python y la migracion. Trade-off aceptable porque RN-32 es estable.
