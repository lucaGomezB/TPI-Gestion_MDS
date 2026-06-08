"""Simple template engine for email personalization (D-04).

Provides pure functions for rendering ``{{variable.path}}`` templates with
context values. The variable set is small and well-defined (RF-20):
- ``{{alumno.nombre}}`` -> EntradaPadron.alumno_nombre
- ``{{materia.nombre}}`` -> Materia.nombre

Unknown variables are preserved verbatim (no error).
"""

from typing import Any

import re

_VARIABLE_PATTERN = re.compile(r"\{\{(\w+(?:\.\w+)*)\}\}")


def render_template(template: str, context: dict[str, Any]) -> str:
    """Replace ``{{key}}`` patterns with context values.

    Unknown variables are preserved verbatim — they remain as ``{{key}}``
    in the output (D-04 design decision).

    Args:
        template: The template string containing ``{{variable.path}}`` markers.
        context: Dictionary mapping variable paths to values.
            E.g. ``{"alumno.nombre": "Juan", "materia.nombre": "Matematica"}``.

    Returns:
        The rendered string with known variables substituted.

    Examples:
        >>> render_template("Hola {{alumno.nombre}}", {"alumno.nombre": "Juan"})
        'Hola Juan'
        >>> render_template("{{unknown}} here", {})
        '{{unknown}} here'
    """
    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key in context:
            return str(context[key])
        return match.group(0)  # preserve verbatim

    return _VARIABLE_PATTERN.sub(_replace, template)


def build_preview_context(
    alumno_nombre: str,
    materia_nombre: str,
) -> dict[str, str]:
    """Build a flat context dict for template rendering.

    Flattens the nested variable references (``alumno.nombre``,
    ``materia.nombre``) into a flat dict suitable for ``render_template``.

    Args:
        alumno_nombre: The student's full name.
        materia_nombre: The subject name.

    Returns:
        A dict like ``{"alumno.nombre": "...", "materia.nombre": "..."}``.
    """
    return {
        "alumno.nombre": alumno_nombre,
        "materia.nombre": materia_nombre,
    }
