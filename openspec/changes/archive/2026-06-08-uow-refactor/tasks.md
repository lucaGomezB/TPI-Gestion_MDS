## 1. UnitOfWork Core Class

- [x] 1.1 Create `backend/app/core/unit_of_work.py` with `UnitOfWork` async context manager class — `__init__(session, tenant_id)`, `__aenter__`, `__aexit__` (commit / rollback / close pattern)
- [x] 1.2 Add lazy `@property` declarations for ALL repository types listed in `repositories/__init__.py` plus CalificacionesRepository, AvisoRepository, AcknowledgmentAvisoRepository, PadronRepository, AuthRepository (20 total)
- [x] 1.3 Verify UnitOfWork with a simple script: imports resolve, context manager enters/exits, commit is called on success, rollback on exception

## 2. Academic Structure Services + Router

- [x] 2.1 Refactor `CarreraService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.carreras` instead of `self.repo`
- [x] 2.2 Refactor `CohorteService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.cohortes` instead of `self.repo`
- [x] 2.3 Refactor `MateriaService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.materias` instead of `self.repo`
- [x] 2.4 Refactor `ProgramaMateriaService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.programas_materia` instead of `self.repo`
- [x] 2.5 Refactor `academic_structure.py` router: wrap every endpoint service call in `async with UnitOfWork(db, tenant_id) as uow:`

## 3. Calificaciones Service + Router (special: inline SQL queries)

- [x] 3.1 Refactor `CalificacionesService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.calificaciones` instead of `self.repo`
- [x] 3.2 Refactor `calificaciones.py` router: wrap service calls in UoW context; extract `_check_materia_access` inline `select(Asignacion)` query to use `self.uow.asignaciones.get()` or a dedicated method on CalificacionesRepository

## 4. Padron Service (special: uses `async with self.session.begin()`)

- [x] 4.1 Refactor `PadronService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.padron` instead of `self.repo`
- [x] 4.2 Replace `async with self.session.begin()` with internal `begin_nested()` or remove entirely (UoW owns the outer transaction)
- [x] 4.3 Refactor AuditService instantiation inside PadronService to use `self.uow.audit_repo` instead of creating `AuditRepository(self.session)` directly
- [x] 4.4 Refactor `padron.py` router: wrap service calls in UoW context

## 5. Communication Service + Router

- [x] 5.1 Refactor `CommunicationService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.comunicaciones` / `self.uow.lotes` instead of `self.repo`
- [x] 5.2 Refactor `communication.py` router: wrap service calls in UoW context

## 6. Encuentro Service + Router

- [x] 6.1 Refactor `EncuentroService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.instancias_encuentro` / `self.uow.slots_encuentro` instead of `self.repo`
- [x] 6.2 Refactor `encuentros.py` router: wrap service calls in UoW context

## 7. Guardia Service + Router

- [x] 7.1 Refactor `GuardiaService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.guardias` instead of `self.repo`
- [x] 7.2 Refactor `guardias.py` router: wrap service calls in UoW context

## 8. Aviso Service + Routers (avisos_admin + avisos_publico)

- [x] 8.1 Refactor `AvisoService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.avisos` / `self.uow.acknowledgment_avisos` instead of `self.repo`
- [x] 8.2 Refactor `avisos_admin.py` and `avisos_publico.py` routers: wrap service calls in UoW context

## 9. Tarea Service + Router

- [x] 9.1 Refactor `TareaService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.tareas` instead of `self.repo`
- [x] 9.2 Refactor `tareas.py` router: wrap service calls in UoW context

## 10. Team Management Service + Router

- [x] 10.1 Refactor `TeamManagementService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.asignaciones` instead of `self.repo`
- [x] 10.2 Refactor `team_management.py` router: wrap service calls in UoW context

## 11. Manual Import Service + Router

- [x] 11.1 Refactor `ManualImportService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.imports` / `self.uow.audit_repo` instead of `self.repo`
- [x] 11.2 Refactor `manual_import.py` router: wrap service calls in UoW context

## 12. Moodle Sync Service + Routers (moodle_sync + admin_moodle)

- [x] 12.1 Refactor `MoodleSyncService` constructor: replace `(session, tenant_id)` with `(uow)`, use `self.uow.moodle_sync` / `self.uow.sync_log` instead of `self.repo`
- [x] 12.2 Refactor `moodle_sync.py` and `admin_moodle.py` routers: wrap service calls in UoW context

## 13. Auth Service + Router (special: receives `AuthRepository` directly)

- [x] 13.1 Refactor `AuthService` constructor: replace `(repo: AuthRepository)` with `(uow: UnitOfWork)`, use `self.uow.auth_repo` instead of `self.repo`
- [x] 13.2 Refactor `auth.py` router: replace `repo = AuthRepository(db); service = AuthService(repo)` with `async with UnitOfWork(db, tenant_id) as uow: service = AuthService(uow)` — resolve tenant_id from the queried Tenant, propagate tenant_id to UoW

## 14. Audit Service (special: receives `AuditRepository` directly) + admin_auditoria Router

- [x] 14.1 Refactor `AuditService` constructor: replace `(repo: AuditRepository)` with `(uow: UnitOfWork)`, use `self.uow.audit_repo` instead of `self.repo`
- [x] 14.2 Refactor `admin_auditoria.py` router: wrap service calls in UoW context
- [x] 14.3 Update ALL callers of `AuditService` across the codebase (including PadronService, ManualImportService, MoodleSyncService, etc.) to pass `self.uow` instead of creating `AuditRepository(session)` inline

## 15. Health Router

- [x] 15.1 Verify `health.py` router — if it uses service pattern, refactor; if it uses direct session query, keep as-is or extract

## 16. Verification

- [x] 16.1 Run full test suite — confirm all existing tests pass with the refactored constructor signatures
- [x] 16.2 Verify no remaining `session, tenant_id` constructor patterns exist in service files (grep for patterns that should be replaced)
- [x] 16.3 Verify no remaining `AuthRepository(db)` or `AuditRepository(session)` patterns exist in router files
