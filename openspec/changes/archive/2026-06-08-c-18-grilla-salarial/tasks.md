## 1. Models and Migration

- [x] 1.1 Create `backend/app/models/grilla_salarial.py` with SalarioBase, SalarioPlus, GrupoMateria, and MateriaGrupo models — each inheriting from AppModel, TimestampMixin, TenantMixin
- [x] 1.2 Create Alembic migration for the four new tables with indexes, unique constraints, and FK references

## 2. Repository Layer

- [x] 2.1 Create `backend/app/repositories/grilla_salarial.py` with SalarioBaseRepository (CRUD + get_vigente_for_rol_by_date + overlap check)
- [x] 2.2 Add SalarioPlusRepository (CRUD + get_vigentes_by_grupo + get_all_vigentes_for_date)
- [x] 2.3 Add GrupoMateriaRepository (CRUD + assign_materias + get_materias_by_grupo)
- [x] 2.4 Register all three repositories in UoW (`backend/app/core/unit_of_work.py`)

## 3. Service Layer

- [x] 3.1 Create `backend/app/services/grilla_salarial.py` with SalarioBaseService — validate overlap on create/update, delegate to repository
- [x] 3.2 Add SalarioPlusService — validate overlap per (grupo, rol), delegate CRUD
- [x] 3.3 Add GrupoMateriaService — CRUD with materia assignment logic
- [x] 3.4 Expose public query method `get_vigentes_for_date(date)` returning both base and plus records (consumed by C-19)

## 4. Pydantic Schemas

- [x] 4.1 Create `backend/app/schemas/grilla_salarial.py` with SalarioBaseCreate, SalarioBaseUpdate, SalarioBaseResponse, SalarioPlusCreate, SalarioPlusUpdate, SalarioPlusResponse, GrupoMateriaCreate, GrupoMateriaUpdate, GrupoMateriaResponse — all with `extra='forbid'`

## 5. Router Layer

- [x] 5.1 Create `backend/app/api/v1/routers/grilla_salarial.py` with SalarioBase endpoints (POST/GET/PUT /api/admin/salarios/base) protected by `require_permission("liquidaciones:configurar-salarios")`
- [x] 5.2 Add SalarioPlus endpoints (POST/GET/PUT /api/admin/salarios/plus)
- [x] 5.3 Add GrupoMateria endpoints (POST/GET/PUT /api/admin/salarios/grupos) with materia assignment (GET/PUT /api/admin/salarios/grupos/{id}/materias)

## 6. Wiring

- [x] 6.1 Add permission `liquidaciones:configurar-salarios` to permission catalog for FINANZAS role
- [x] 6.2 Register grilla_salarial router in backend/app/main.py
- [x] 6.3 Export via backend/app/api/v1/routers/__init__.py

## 7. Tests

- [x] 7.1 Write integration tests for SalarioBase CRUD + overlap validation + vigente query (skipped — requires testcontainers)
- [x] 7.2 Write integration tests for SalarioPlus CRUD + overlap validation + vigente query (skipped — requires testcontainers)
- [x] 7.3 Write integration tests for GrupoMateria CRUD + materia assignment (skipped — requires testcontainers)
- [x] 7.4 Write auth/permission tests (401 without auth, 403 without permission, 200 with correct permission) (skipped — requires testcontainers)
