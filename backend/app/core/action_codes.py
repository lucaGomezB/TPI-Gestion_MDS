"""Closed catalog of standardized audit action codes (RN-24).

All significant actions in the system use codes from this StrEnum.
The catalog is extensible by adding new members in future changes.

Usage::

    from app.core.action_codes import AccionAuditoria

    audit_service.log_action(
        accion=AccionAuditoria.CALIFICACIONES_IMPORTAR,
        ...
    )
"""

from enum import StrEnum


class AccionAuditoria(StrEnum):
    """Closed catalog of standardized audit action codes.

    Each member's value matches its name (e.g., ``AccionAuditoria.PADRON_CARGAR.value
    == "PADRON_CARGAR"``). Values are stored as VARCHAR(50) in the database.
    """

    CALIFICACIONES_IMPORTAR = "CALIFICACIONES_IMPORTAR"
    PADRON_CARGAR = "PADRON_CARGAR"
    COMUNICACION_ENVIAR = "COMUNICACION_ENVIAR"
    ASIGNACION_MODIFICAR = "ASIGNACION_MODIFICAR"
    LIQUIDACION_CALCULAR = "LIQUIDACION_CALCULAR"
    LIQUIDACION_CERRAR = "LIQUIDACION_CERRAR"
    COLOQUIO_CREAR = "COLOQUIO_CREAR"
    COLOQUIO_RESERVAR = "COLOQUIO_RESERVAR"
    COLOQUIO_RESULTADO = "COLOQUIO_RESULTADO"
    IMPERSONACION_INICIAR = "IMPERSONACION_INICIAR"
    IMPERSONACION_FINALIZAR = "IMPERSONACION_FINALIZAR"
    ATRASADOS_CONSULTAR = "ATRASADOS_CONSULTAR"
    RANKING_CONSULTAR = "RANKING_CONSULTAR"
    NOTAS_FINALES_CONSULTAR = "NOTAS_FINALES_CONSULTAR"
    EXPORT_ATRASADOS_CONSULTAR = "EXPORT_ATRASADOS_CONSULTAR"
    MONITOR_GENERAL_CONSULTAR = "MONITOR_GENERAL_CONSULTAR"
    SEGUIMIENTO_CONSULTAR = "SEGUIMIENTO_CONSULTAR"
