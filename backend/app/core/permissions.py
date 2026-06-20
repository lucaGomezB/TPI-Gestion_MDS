"""RBAC permissions matrix and ``require_permission`` factory.

Defines the full permissions matrix for all 7 roles (ALUMNO, TUTOR,
PROFESOR, COORDINADOR, NEXO, ADMIN, FINANZAS).

Permissions are expressed as ``modulo:accion`` strings. The matrix is
hardcoded for MVP — it will become data-driven in a future change.

Usage::

    from app.core.permissions import require_permission

    @router.get("/calificaciones")
    async def list_calificaciones(
        _: Annotated[None, Depends(require_permission("calificaciones:importar"))],
    ):
        ...
"""

from collections import defaultdict
from collections.abc import Callable

# ── Permissions matrix (7 roles × permissions) ──────────────────────────────
# Based on knowledge-base/03_actores_y_roles.md §3.3

ROL_PERMISSIONS: dict[str, set[str]] = {
    "ALUMNO": {
        "coloquios:reservar",
        "estado_academico:ver_propio",
        "evaluacion:reservar",
        "aviso:confirmar",
        "avisos:ver",
        "avisos:ack",
    },
    "TUTOR": {
        "aviso:confirmar",
        "avisos:ver",
        "avisos:ack",
        "atrasados:ver",
        "facturas:subir",
        "reportes:seguimiento",
        "entrega:detectar_pendiente",
        "encuentro:gestionar",
        "guardia:registrar",
        "guardias:registrar",
        "mensajeria:enviar",
        "tareas:ver",
    },
    "PROFESOR": {
        "aviso:confirmar",
        "avisos:ver",
        "avisos:ack",
        "calificaciones:importar",
        "calificaciones:ver",
        "calificaciones:vaciar",
        "calificaciones:configurar-umbral",
        "calificaciones:exportar",
        "atrasados:ver",
        "facturas:subir",
        "coloquios:ver_agenda",
        "coloquios:resultados",
        "reportes:ver",
        "reportes:notas_finales",
        "reportes:exportar_atrasados",
        "reportes:seguimiento",
        "entrega:detectar_pendiente",
        "comunicacion:enviar",
        "encuentro:gestionar",
        "encuentros:crear",
        "encuentros:editar",
        "guardia:registrar",
        "guardias:registrar",
        "mensajeria:enviar",
        "tareas:ver",
        "tareas:asignar",
        "padron:importar",
        "padron:ver",
    },
    "COORDINADOR": {
        "aviso:confirmar",
        "calificaciones:importar",
        "calificaciones:ver",
        "calificaciones:vaciar",
        "calificaciones:configurar-umbral",
        "calificaciones:exportar",
        "atrasados:ver",
        "coloquios:crear",
        "coloquios:importar",
        "coloquios:ver_agenda",
        "coloquios:resultados",
        "coloquios:metricas",
        "reportes:ver",
        "reportes:notas_finales",
        "reportes:exportar_atrasados",
        "reportes:monitor_general",
        "reportes:seguimiento",
        "entrega:detectar_pendiente",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "encuentro:gestionar",
        "encuentros:crear",
        "encuentros:editar",
        "encuentros:ver_todas",
        "guardia:registrar",
        "guardias:registrar",
        "guardias:ver_todas",
        "mensajeria:enviar",
        "tareas:ver",
        "tareas:asignar",
        "tareas:admin",
        "aviso:publicar",
        "avisos:publicar",
        "avisos:ver",
        "avisos:ack",
        "equipo_docente:asignar",
        "equipo_docente:ver",
        "auditoria:ver",
        "padron:importar",
        "padron:ver",
    },
    "NEXO": {
        "aviso:confirmar",
        "avisos:ver",
        "avisos:ack",
    },
    "ADMIN": {
        "aviso:confirmar",
        "calificaciones:importar",
        "calificaciones:ver",
        "calificaciones:vaciar",
        "calificaciones:configurar-umbral",
        "atrasados:ver",
        "coloquios:crear",
        "coloquios:importar",
        "coloquios:ver_agenda",
        "coloquios:resultados",
        "coloquios:metricas",
        "reportes:ver",
        "reportes:monitor_general",
        "reportes:seguimiento",
        "entrega:detectar_pendiente",
        "comunicacion:enviar",
        "comunicacion:aprobar",
        "encuentro:gestionar",
        "encuentros:crear",
        "encuentros:editar",
        "encuentros:ver_todas",
        "guardia:registrar",
        "guardias:registrar",
        "guardias:ver_todas",
        "mensajeria:enviar",
        "tareas:ver",
        "tareas:asignar",
        "tareas:admin",
        "aviso:publicar",
        "avisos:publicar",
        "avisos:ver",
        "avisos:ack",
        "equipo_docente:asignar",
        "equipo_docente:ver",
        "estructura_academica:gestionar",
        "usuario:gestionar",
        "auditoria:ver",
        "facturas:gestionar",
        "facturas:subir",
        "liquidaciones:configurar-salarios",
        "grilla_salarial:operar",
        "liquidaciones:ver",
        "liquidaciones:calcular",
        "liquidaciones:cerrar",
        "tenant:configurar",
    },
    "FINANZAS": {
        "aviso:confirmar",
        "avisos:ver",
        "avisos:ack",
        "auditoria:ver",
        "grilla_salarial:operar",
        "liquidaciones:ver",
        "liquidaciones:calcular",
        "liquidaciones:cerrar",
        "liquidaciones:configurar-salarios",
        "facturas:gestionar",
    },
}


# ── Flat set of all permissions ─────────────────────────────────────────────

ALL_PERMISSIONS: set[str] = set()
for _perms in ROL_PERMISSIONS.values():
    ALL_PERMISSIONS.update(_perms)

# ── Permissions grouped by module for UI rendering ──────────────────────────

PERMISSIONS_BY_MODULE: dict[str, list[str]] = defaultdict(list)
for _perm in sorted(ALL_PERMISSIONS):
    _modulo, _accion = _perm.split(":", 1)
    PERMISSIONS_BY_MODULE[_modulo].append(_perm)

# ── Permission check dependency factory ─────────────────────────────────────


def require_permission(permission: str) -> Callable[[list[str]], bool]:
    """Factory that returns a callable to check if a user has a permission.

    The returned callable accepts a list of role names and returns ``True``
    if ANY of the user's roles grants the requested permission.

    Args:
        permission: The permission string to check (e.g. ``"calificaciones:importar"``).

    Returns:
        A function that takes ``roles: list[str]`` and returns ``bool``.
    """

    def _check(roles: list[str]) -> bool:
        """Check if any of the given roles has the required permission.

        Args:
            roles: List of role name strings from the JWT.

        Returns:
            ``True`` if at least one role grants the permission.
        """
        for role in roles:
            role_perms = ROL_PERMISSIONS.get(role, set())
            if permission in role_perms:
                return True
        return False

    return _check
