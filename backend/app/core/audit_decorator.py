"""Audit log decorator for simple service methods.

Provides ``@audit_log(accion)`` decorator that automatically creates an
audit log entry after the decorated method completes successfully. Suitable
for services that can derive ``materia_id``, ``detalle``, and
``filas_afectadas`` from the return value.

Usage::

    from app.core.audit_decorator import audit_log
    from app.core.action_codes import AccionAuditoria

    class CalificacionesService:
        @audit_log(accion=AccionAuditoria.CALIFICACIONES_IMPORTAR)
        async def importar(self, materia_id: str, ...) -> ImportResult:
            ...


For complex cases where the metadata depends on runtime context, use
the explicit ``audit_service.log_action()`` pattern instead.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from app.core.action_codes import AccionAuditoria

P = ParamSpec("P")
R = TypeVar("R")


def audit_log(
    accion: AccionAuditoria,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that logs an audit entry after the decorated method succeeds.

    The decorated method MUST have an ``audit_service`` attribute (an
    ``AuditService`` instance) and MUST have access to ``current_user``
    (a dict with ``id`` and ``tenant_id`` keys).

    Args:
        accion: The ``AccionAuditoria`` action code to log.

    Returns:
        The decorated function.

    Raises:
        AttributeError: If the instance lacks ``audit_service``.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        async def wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> R:  # noqa: ANN401
            result = await func(self, *args, **kwargs)

            # Check for audit_service on the instance
            audit_svc = getattr(self, "audit_service", None)
            current_user = getattr(self, "current_user", None)

            if audit_svc is not None and current_user is not None:
                materia_id = kwargs.get("materia_id")
                detalle = None
                filas_afectadas = None

                # Try to derive metadata from the return value
                if hasattr(result, "model_dump"):
                    result_dict = result.model_dump()
                elif isinstance(result, dict):
                    result_dict = result
                else:
                    result_dict = {}

                if "filas_afectadas" in result_dict:
                    filas_afectadas = result_dict["filas_afectadas"]
                if "detalle" in result_dict:
                    detalle = result_dict["detalle"]

                await audit_svc.log_action(
                    accion=accion,
                    actor_id=current_user["id"],
                    tenant_id=current_user["tenant_id"],
                    materia_id=materia_id,
                    detalle=detalle,
                    filas_afectadas=filas_afectadas,
                )

            return result

        return wrapper

    return decorator
