from app.repositories.academic_structure import (
    CarreraRepository,
    CohorteRepository,
    MateriaRepository,
    ProgramaMateriaRepository,
)
from app.repositories.audit_repository import AuditRepository
from app.repositories.base import BaseRepository
from app.repositories.grilla_salarial import (
    GrupoMateriaRepository,
    SalarioBaseRepository,
    SalarioPlusRepository,
)
from app.repositories.coloquios import (
    ColoquioAdminRepository,
    EvaluacionColoquioRepository,
    ReservaColoquioRepository,
    ResultadoColoquioRepository,
)
from app.repositories.communication import ComunicacionRepository, LoteRepository
from app.repositories.tarea import TareaRepository
from app.repositories.encuentros import InstanciaEncuentroRepository, SlotEncuentroRepository
from app.repositories.factura import FacturaRepository
from app.repositories.guardias import GuardiaRepository
from app.repositories.import_repository import ImportRepository
from app.repositories.moodle_sync_repository import MoodleSyncRepository
from app.repositories.sync_log_repository import SyncLogRepository
from app.repositories.team_management import AsignacionRepository

__all__ = [
    "AsignacionRepository",
    "AuditRepository",
    "BaseRepository",
    "CarreraRepository",
    "CohorteRepository",
    "ColoquioAdminRepository",
    "ComunicacionRepository",
    "EvaluacionColoquioRepository",
    "FacturaRepository",
    "GrupoMateriaRepository",
    "GuardiaRepository",
    "ImportRepository",
    "InstanciaEncuentroRepository",
    "LoteRepository",
    "MateriaRepository",
    "MoodleSyncRepository",
    "ProgramaMateriaRepository",
    "ReservaColoquioRepository",
    "ResultadoColoquioRepository",
    "SalarioBaseRepository",
    "SalarioPlusRepository",
    "SlotEncuentroRepository",
    "SyncLogRepository",
    "TareaRepository",
]
