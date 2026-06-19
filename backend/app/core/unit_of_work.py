"""Unit of Work pattern — coordinates repository access and transaction scoping.

Provides:
- Lazy-loaded repository access via properties
- Automatic commit/rollback on context manager exit
- Single point of transaction control for service layers
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.academic_structure import (
    CarreraRepository,
    CohorteRepository,
    MateriaRepository,
    ProgramaMateriaRepository,
)
from app.repositories.acknowledgment_aviso import AcknowledgmentRepository
from app.repositories.admin_usuarios import AdminUsuariosRepository
from app.repositories.atrasados_ranking import AtrasadosRankingRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.auth_repository import AuthRepository
from app.repositories.aviso import AvisoRepository
from app.repositories.calificaciones import CalificacionesRepository
from app.repositories.coloquios import (
    ColoquioAdminRepository,
    EvaluacionColoquioRepository,
    ReservaColoquioRepository,
    ResultadoColoquioRepository,
)
from app.repositories.communication import ComunicacionRepository, LoteRepository
from app.repositories.encuentros import InstanciaEncuentroRepository, SlotEncuentroRepository
from app.repositories.evaluaciones import EvaluacionRepository
from app.repositories.factura import FacturaRepository
from app.repositories.grilla_salarial import (
    GrupoMateriaRepository,
    SalarioBaseRepository,
    SalarioPlusRepository,
)
from app.repositories.liquidacion import LiquidacionRepository
from app.repositories.guardias import GuardiaRepository
from app.repositories.import_repository import ImportRepository
from app.repositories.mensaje import MensajeRepository
from app.repositories.moodle_sync_repository import MoodleSyncRepository
from app.repositories.reportes_export import ReportesExportRepository
from app.repositories.reportes_monitor import ReportesMonitorRepository
from app.repositories.reportes_notas import ReportesNotasRepository
from app.repositories.padron import PadronRepository
from app.repositories.sync_log_repository import SyncLogRepository
from app.repositories.tarea import TareaRepository
from app.repositories.team_management import AsignacionRepository


class UnitOfWork:
    """Coordinates repository access and transaction boundaries.

    Usage::

        async with UnitOfWork(session, tenant_id) as uow:
            service = SomeService(uow)
            result = await service.do_something(data)
            # auto-commits on success, auto-rollbacks on exception
    """

    def __init__(self, session: AsyncSession, tenant_id: str | None = None):
        self._session = session
        self._tenant_id = tenant_id
        self._repos: dict[str, object] = {}

    def _get(self, key: str, factory: type, *, no_tenant: bool = False) -> object:
        """Lazy-load a repository by key, caching it for the UoW lifetime.

        Args:
            key: Unique cache key for the repository.
            factory: Repository class to instantiate.
            no_tenant: If True, pass only session (no tenant_id).

        Returns:
            The cached repository instance.
        """
        if key not in self._repos:
            if no_tenant:
                self._repos[key] = factory(self._session)
            else:
                self._repos[key] = factory(self._session, self._tenant_id)
        return self._repos[key]

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self._session.commit()
        else:
            await self._session.rollback()
        await self._session.close()

    @property
    def auth(self) -> AuthRepository:
        return self._get("auth", AuthRepository, no_tenant=True)  # type: ignore[return-value]

    @property
    def audit(self) -> AuditRepository:
        return self._get("audit", AuditRepository, no_tenant=True)  # type: ignore[return-value]

    @property
    def carrera(self) -> CarreraRepository:
        return self._get("carrera", CarreraRepository)  # type: ignore[return-value]

    @property
    def cohorte(self) -> CohorteRepository:
        return self._get("cohorte", CohorteRepository)  # type: ignore[return-value]

    @property
    def materia(self) -> MateriaRepository:
        return self._get("materia", MateriaRepository)  # type: ignore[return-value]

    @property
    def programa_materia(self) -> ProgramaMateriaRepository:
        return self._get("programa_materia", ProgramaMateriaRepository)  # type: ignore[return-value]

    @property
    def calificaciones(self) -> CalificacionesRepository:
        return self._get("calificaciones", CalificacionesRepository)  # type: ignore[return-value]

    @property
    def atrasados_ranking(self) -> AtrasadosRankingRepository:
        return self._get("atrasados_ranking", AtrasadosRankingRepository)  # type: ignore[return-value]

    @property
    def comunicacion(self) -> ComunicacionRepository:
        return self._get("comunicacion", ComunicacionRepository)  # type: ignore[return-value]

    @property
    def lote(self) -> LoteRepository:
        return self._get("lote", LoteRepository)  # type: ignore[return-value]

    @property
    def tarea(self) -> TareaRepository:
        return self._get("tarea", TareaRepository)  # type: ignore[return-value]

    @property
    def padron(self) -> PadronRepository:
        return self._get("padron", PadronRepository)  # type: ignore[return-value]

    @property
    def instancia_encuentro(self) -> InstanciaEncuentroRepository:
        return self._get("instancia_encuentro", InstanciaEncuentroRepository)  # type: ignore[return-value]

    @property
    def slot_encuentro(self) -> SlotEncuentroRepository:
        return self._get("slot_encuentro", SlotEncuentroRepository)  # type: ignore[return-value]

    @property
    def guardia(self) -> GuardiaRepository:
        return self._get("guardia", GuardiaRepository)  # type: ignore[return-value]

    @property
    def evaluacion(self) -> EvaluacionRepository:
        return self._get("evaluacion", EvaluacionRepository)  # type: ignore[return-value]

    @property
    def asignacion(self) -> AsignacionRepository:
        return self._get("asignacion", AsignacionRepository)  # type: ignore[return-value]

    @property
    def admin_usuarios(self) -> AdminUsuariosRepository:
        return self._get("admin_usuarios", AdminUsuariosRepository)  # type: ignore[return-value]

    @property
    def aviso(self) -> AvisoRepository:
        return self._get("aviso", AvisoRepository)  # type: ignore[return-value]

    @property
    def acknowledgment(self) -> AcknowledgmentRepository:
        return self._get("acknowledgment", AcknowledgmentRepository)  # type: ignore[return-value]

    @property
    def import_repo(self) -> ImportRepository:
        return self._get("import_repo", ImportRepository)  # type: ignore[return-value]

    @property
    def moodle_sync(self) -> MoodleSyncRepository:
        return self._get("moodle_sync", MoodleSyncRepository)  # type: ignore[return-value]

    @property
    def sync_log(self) -> SyncLogRepository:
        return self._get("sync_log", SyncLogRepository)  # type: ignore[return-value]

    @property
    def coloquio_evaluacion(self) -> EvaluacionColoquioRepository:
        return self._get("coloquio_evaluacion", EvaluacionColoquioRepository)  # type: ignore[return-value]

    @property
    def coloquio_reserva(self) -> ReservaColoquioRepository:
        return self._get("coloquio_reserva", ReservaColoquioRepository)  # type: ignore[return-value]

    @property
    def coloquio_resultado(self) -> ResultadoColoquioRepository:
        return self._get("coloquio_resultado", ResultadoColoquioRepository)  # type: ignore[return-value]

    @property
    def coloquio_admin(self) -> ColoquioAdminRepository:
        return self._get("coloquio_admin", ColoquioAdminRepository)  # type: ignore[return-value]

    @property
    def salario_base(self) -> SalarioBaseRepository:
        return self._get("salario_base", SalarioBaseRepository)  # type: ignore[return-value]

    @property
    def salario_plus(self) -> SalarioPlusRepository:
        return self._get("salario_plus", SalarioPlusRepository)  # type: ignore[return-value]

    @property
    def grupo_materia(self) -> GrupoMateriaRepository:
        return self._get("grupo_materia", GrupoMateriaRepository)  # type: ignore[return-value]

    @property
    def mensaje(self) -> MensajeRepository:
        return self._get("mensaje", MensajeRepository)  # type: ignore[return-value]

    @property
    def factura(self) -> FacturaRepository:
        return self._get("factura", FacturaRepository)  # type: ignore[return-value]

    @property
    def liquidacion(self) -> LiquidacionRepository:
        return self._get("liquidacion", LiquidacionRepository)  # type: ignore[return-value]

    @property
    def reportes_notas(self) -> ReportesNotasRepository:
        return self._get("reportes_notas", ReportesNotasRepository)  # type: ignore[return-value]

    @property
    def reportes_export(self) -> ReportesExportRepository:
        return self._get("reportes_export", ReportesExportRepository)  # type: ignore[return-value]

    @property
    def reportes_monitor(self) -> ReportesMonitorRepository:
        return self._get("reportes_monitor", ReportesMonitorRepository)  # type: ignore[return-value]
