"""Unit tests for the template engine (C-11, Task 13.1).

Tests ``render_template`` and ``build_preview_context`` from
``app.services.template_engine``.
"""

from app.services.template_engine import build_preview_context, render_template


class TestRenderTemplate:
    """render_template — simple string substitution (D-04)."""

    def test_simple_substitution(self):
        """{{alumno.nombre}} should be replaced with the context value."""
        result = render_template("Hola {{alumno.nombre}}", {"alumno.nombre": "Juan"})
        assert result == "Hola Juan"

    def test_materia_nombre_substitution(self):
        """{{materia.nombre}} should be replaced."""
        result = render_template(
            "Bienvenido a {{materia.nombre}}",
            {"materia.nombre": "Matematica"},
        )
        assert result == "Bienvenido a Matematica"

    def test_multiple_variables(self):
        """Multiple {{variables}} should all be replaced."""
        result = render_template(
            "{{alumno.nombre}}, tu materia es {{materia.nombre}}",
            {"alumno.nombre": "Ana", "materia.nombre": "Fisica"},
        )
        assert result == "Ana, tu materia es Fisica"

    def test_unknown_variable_preserved(self):
        """Unknown {{variables}} should be preserved verbatim."""
        result = render_template(
            "Hola {{alumno.nombre}}, {{unknown}}",
            {"alumno.nombre": "Juan"},
        )
        assert result == "Hola Juan, {{unknown}}"

    def test_no_variables(self):
        """Templates without variables should return unchanged."""
        result = render_template("Hola mundo", {})
        assert result == "Hola mundo"

    def test_empty_template(self):
        """Empty template should return empty string."""
        result = render_template("", {"alumno.nombre": "Juan"})
        assert result == ""

    def test_variable_appears_multiple_times(self):
        """Same variable appearing multiple times should all be replaced."""
        result = render_template(
            "{{x}} + {{x}} = {{y}}",
            {"x": "1", "y": "2"},
        )
        assert result == "1 + 1 = 2"

    def test_numeric_values_converted(self):
        """Numeric context values should be converted to string."""
        result = render_template("Valor: {{puntaje}}", {"puntaje": 95})
        assert result == "Valor: 95"

    def test_dot_notation_in_variable_name(self):
        """Variable names with dots should be treated as flat keys."""
        result = render_template(
            "{{a.b.c}}",
            {"a.b.c": "value"},
        )
        assert result == "value"


class TestBuildPreviewContext:
    """build_preview_context — context dict creation."""

    def test_basic_context(self):
        """Should create context with alumno.nombre and materia.nombre."""
        ctx = build_preview_context(
            alumno_nombre="Juan Perez",
            materia_nombre="Matematica",
        )
        assert ctx == {
            "alumno.nombre": "Juan Perez",
            "materia.nombre": "Matematica",
        }

    def test_empty_names(self):
        """Empty strings should be handled."""
        ctx = build_preview_context(
            alumno_nombre="",
            materia_nombre="",
        )
        assert ctx == {
            "alumno.nombre": "",
            "materia.nombre": "",
        }
