from app.api.v1.routers.academic_structure import router as academic_structure_router
from app.api.v1.routers.admin_facturas import router as admin_facturas_router
from app.api.v1.routers.admin_auditoria import router as admin_auditoria_router
from app.api.v1.routers.admin_moodle import router as admin_moodle_router
from app.api.v1.routers.atrasados_ranking import router as atrasados_ranking_router
from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.avisos_admin import router as avisos_admin_router
from app.api.v1.routers.avisos_publico import router as avisos_publico_router
from app.api.v1.routers.calificaciones import router as calificaciones_router
from app.api.v1.routers.coloquios import (
    router_admin as coloquios_admin_router,
    router_coloquios as coloquios_router,
    router_materias as coloquios_materias_router,
)
from app.api.v1.routers.communication import router as communication_router
from app.api.v1.routers.docente_facturas import router as docente_facturas_router
from app.api.v1.routers.encuentros import router as encuentros_router
from app.api.v1.routers.grilla_salarial import router as grilla_salarial_router
from app.api.v1.routers.liquidaciones import router as liquidaciones_router
from app.api.v1.routers.mensajeria import router as mensajeria_router
from app.api.v1.routers.tareas import router as tareas_router
from app.api.v1.routers.guardias import router as guardias_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.manual_import import router as manual_import_router
from app.api.v1.routers.moodle_sync import router as moodle_sync_router
from app.api.v1.routers.admin_reportes import router as admin_reportes_router
from app.api.v1.routers.padron import router as padron_router
from app.api.v1.routers.reportes import router as reportes_router
from app.api.v1.routers.team_management import router as team_management_router

__all__ = [
    "academic_structure_router",
    "admin_facturas_router",
    "admin_auditoria_router",
    "docente_facturas_router",
    "admin_moodle_router",
    "admin_reportes_router",
    "auth_router",
    "avisos_admin_router",
    "avisos_publico_router",
    "calificaciones_router",
    "coloquios_admin_router",
    "coloquios_materias_router",
    "coloquios_router",
    "communication_router",
    "encuentros_router",
    "grilla_salarial_router",
    "guardias_router",
    "health_router",
    "liquidaciones_router",
    "mensajeria_router",
    "manual_import_router",
    "tareas_router",
    "moodle_sync_router",
    "padron_router",
    "reportes_router",
    "team_management_router",
]
