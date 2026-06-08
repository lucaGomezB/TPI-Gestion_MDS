## Why

La liquidacion de honorarios docentes (C-19) requiere una grilla salarial configurable por tenant que defina los montos base por rol y los plus por categoria de materia, con vigencia temporal. Actualmente no existe ningun modulo que permita a FINANZAS administrar estos valores. Implementar la grilla salarial como tabla independiente con versionado por fechas (RN-31, RN-32, RN-33) desacopla la configuracion de valores del calculo de liquidaciones, permitiendo que FINANZAS ajuste montos sin tocar codigo ni afectar liquidaciones cerradas.

## What Changes

- **Nuevos modelos SQLAlchemy**: `SalarioBase` (E17) y `SalarioPlus` (E18) con tenant_id, rol, montos y vigencia temporal (desde/hasta nullable), mas `GrupoMateria` como entidad configurable por tenant que agrupa materias bajo una clave (ej: "PROG", "BD").
- **Nuevos endpoints REST** protegidos con permiso `liquidaciones:configurar-salarios`:
  - `POST/GET/PUT /api/admin/salarios/base` — ABM de salario base por rol
  - `POST/GET/PUT /api/admin/salarios/plus` — ABM de plus salarial por grupo y rol
  - `POST/GET/PUT /api/admin/salarios/grupos` — ABM de grupos de materia
- **Migracion Alembic** para las nuevas tablas.
- **Validacion de unicidad**: solo una entrada vigente por (rol, desde) en SalarioBase; solo una entrada vigente por (grupo, rol, desde) en SalarioPlus.

## Capabilities

### New Capabilities
- `grilla-salarial`: Administracion de salario base por rol y plus salarial por (grupo de materia x rol) con vigencia temporal, incluyendo grupos de materia configurables por tenant. Permiso `liquidaciones:configurar-salarios` para rol FINANZAS.

### Modified Capabilities
- `core-models`: UPDATE — se agregan E17 (SalarioBase), E18 (SalarioPlus) y entidad GrupoMateria como nuevas entidades del modelo de datos.

## Impact

- **Backend**: Nuevos modelos en `backend/app/models/grilla_salarial.py`, nuevos repositorios, servicios y routers en patron Clean Architecture con UoW.
- **Base de datos**: Nueva migracion Alembic con tablas `salarios_base`, `salarios_plus`, `grupos_materia`.
- **Auth**: Permiso `liquidaciones:configurar-salarios` en la matriz (rol FINANZAS).
- **Dependencias**: Requiere C-?? (core auth con RBAC funcional) — depende de que `require_permission` este activo. No depende de otros cambios de liquidaciones (los valores se consultan por servicio).
- **Auditoria**: Nuevas acciones `SALARIO_BASE_CREAR`, `SALARIO_BASE_MODIFICAR`, `SALARIO_PLUS_CREAR`, `SALARIO_PLUS_MODIFICAR`, `GRUPO_MATERIA_CREAR`, `GRUPO_MATERIA_MODIFICAR`.
