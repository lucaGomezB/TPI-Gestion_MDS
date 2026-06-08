"""Unit tests for calificaciones service utilities (column detection, grade derivation).

These tests do NOT require a database connection.
They test the parsing and derivation logic in isolation.
"""

import pytest
from fastapi import HTTPException

from app.services.calificaciones import (
    _derivar_aprobado,
    _detect_nota_columns,
    _normalize_header,
)


class TestNormalizeHeader:
    """Test _normalize_header function."""

    def test_lowercases(self):
        """Normalize: lowercases input."""
        assert _normalize_header("TP 1 (REAL)") == "tp 1 (real)"
        assert _normalize_header("Actividad") == "actividad"

    def test_strips_whitespace(self):
        """Normalize: strips surrounding whitespace."""
        assert _normalize_header("  TP 1  ") == "tp 1"
        assert _normalize_header("\tNota\n") == "nota"

    def test_handles_empty(self):
        """Normalize: empty string returns empty."""
        assert _normalize_header("") == ""


class TestDetectNotaColumns:
    """Test _detect_nota_columns function."""

    def test_detects_numeric_column_by_real_suffix(self):
        """Columns ending in (Real) are detected as numeric."""
        headers = ["Nombre", "Email", "TP 1 (Real)"]
        actividades, identifying = _detect_nota_columns(headers)
        assert len(actividades) == 1
        assert actividades[0]["nombre"] == "TP 1"
        assert actividades[0]["tipo"] == "numerica"
        assert actividades[0]["columna"] == "TP 1 (Real)"

    def test_detects_textual_column(self):
        """Columns without (Real) suffix are detected as textual."""
        headers = ["Nombre", "Email", "TP 1"]
        actividades, identifying = _detect_nota_columns(headers)
        assert len(actividades) == 1
        assert actividades[0]["nombre"] == "TP 1"
        assert actividades[0]["tipo"] == "textual"
        assert actividades[0]["columna"] == "TP 1"

    def test_detects_numeric_and_textual_columns(self):
        """Mixed numeric and textual columns are detected correctly."""
        headers = ["Nombre", "Email", "TP 1 (Real)", "TP 2"]
        actividades, identifying = _detect_nota_columns(headers)
        assert len(actividades) == 2
        # Numeric column detected
        numeric = [a for a in actividades if a["tipo"] == "numerica"]
        textual = [a for a in actividades if a["tipo"] == "textual"]
        assert len(numeric) == 1
        assert len(textual) == 1
        assert numeric[0]["nombre"] == "TP 1"
        assert textual[0]["nombre"] == "TP 2"

    def test_case_insensitive_real_suffix(self):
        """Real suffix detection is case-insensitive."""
        headers = ["Nombre", "Email", "tp 1 (real)", "TP 2 (REAL)"]
        actividades, identifying = _detect_nota_columns(headers)
        assert len(actividades) == 2
        for act in actividades:
            assert act["tipo"] == "numerica"

    def test_numeric_takes_priority_over_textual(self):
        """If same activity name appears as numeric and textual, numeric wins."""
        headers = ["Nombre", "Email", "TP 1", "TP 1 (Real)"]
        actividades, identifying = _detect_nota_columns(headers)
        # Only one entry for "TP 1", and it's numeric
        assert len(actividades) == 1
        assert actividades[0]["tipo"] == "numerica"
        assert actividades[0]["columna"] == "TP 1 (Real)"

    def test_identifying_columns_are_separated(self):
        """Identifying columns (nombre, email, apellidos) are returned separately."""
        headers = ["Nombre", "Apellidos", "Email", "TP 1 (Real)"]
        actividades, identifying = _detect_nota_columns(headers)
        assert "nombre" in identifying
        assert "email" in identifying
        assert len(actividades) == 1

    def test_apellido_maps_to_required(self):
        """'apellido' (singular) is treated as required identifying column."""
        headers = ["Nombre", "Apellido", "Email", "TP 1"]
        _, identifying = _detect_nota_columns(headers)
        assert "apellido" in identifying

    def test_no_grade_columns_raises(self):
        """File with no grade columns raises 400."""
        headers = ["Nombre", "Email"]
        with pytest.raises(HTTPException) as exc:
            _detect_nota_columns(headers)
        assert exc.value.status_code == 400
        assert "calificaciones" in exc.value.detail.lower() or "columna" in exc.value.detail.lower()

    def test_empty_headers_raises(self):
        """Empty headers list raises 400."""
        with pytest.raises(HTTPException) as exc:
            _detect_nota_columns([])
        assert exc.value.status_code == 400


class TestDerivarAprobado:
    """Test _derivar_aprobado function."""

    APPROVED_VALUES = ["Satisfactorio", "Supera lo esperado"]

    def test_numeric_above_threshold_true(self):
        """Numeric grade >= threshold returns True."""
        assert _derivar_aprobado(75.0, None, 60, self.APPROVED_VALUES) is True

    def test_numeric_at_threshold_true(self):
        """Numeric grade == threshold returns True."""
        assert _derivar_aprobado(60.0, None, 60, self.APPROVED_VALUES) is True

    def test_numeric_below_threshold_false(self):
        """Numeric grade < threshold returns False."""
        assert _derivar_aprobado(45.0, None, 60, self.APPROVED_VALUES) is False

    def test_textual_in_approved_values_true(self):
        """Textual grade in approved values returns True."""
        assert _derivar_aprobado(None, "Satisfactorio", 60, self.APPROVED_VALUES) is True
        assert _derivar_aprobado(None, "Supera lo esperado", 60, self.APPROVED_VALUES) is True

    def test_textual_not_in_approved_values_false(self):
        """Textual grade not in approved values returns False."""
        assert _derivar_aprobado(None, "No satisfactorio", 60, self.APPROVED_VALUES) is False
        assert _derivar_aprobado(None, "Regular", 60, self.APPROVED_VALUES) is False

    def test_textual_case_insensitive(self):
        """Textual comparison is case-insensitive."""
        assert _derivar_aprobado(None, "satisfactorio", 60, self.APPROVED_VALUES) is True
        assert _derivar_aprobado(None, "SATISFACTORIO", 60, self.APPROVED_VALUES) is True

    def test_none_grades_false(self):
        """Both grades None returns False."""
        assert _derivar_aprobado(None, None, 60, self.APPROVED_VALUES) is False

    def test_custom_threshold(self):
        """Custom threshold values work correctly."""
        custom_values = ["Aprobado", "Promocionado"]
        assert _derivar_aprobado(None, "Promocionado", 70, custom_values) is True
        assert _derivar_aprobado(None, "Satisfactorio", 70, custom_values) is False
        assert _derivar_aprobado(80.0, None, 70, custom_values) is True
        assert _derivar_aprobado(60.0, None, 70, custom_values) is False

    def test_numeric_precedes_textual(self):
        """If both numeric and textual are present, numeric is used."""
        assert _derivar_aprobado(80.0, "No satisfactorio", 60, self.APPROVED_VALUES) is True
        assert _derivar_aprobado(40.0, "Satisfactorio", 60, self.APPROVED_VALUES) is False
