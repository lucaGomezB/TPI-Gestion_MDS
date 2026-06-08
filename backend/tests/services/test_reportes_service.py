"""Unit tests for reportes service pure functions.

These tests do NOT require a database connection.
They test the calculation, detection, monitoring, and CSV logic in isolation.
"""

import csv
import io

import pytest

from app.services.reportes_notas import (
    _build_csv_rows,
    _calcular_nota_final,
    _calcular_promedio_cumplimiento,
)
from app.services.reportes_export import (
    _detectar_sin_corregir,
)


class TestCalcularNotaFinal:
    """Test _calcular_nota_final — final grade calculation (F2.5)."""

    def test_numeric_grades_only_computes_average(self):
        """Numeric grades [80, 90, 70] yields nota_final=80.00."""
        calificaciones = [
            {"nota_numerica": 80.0, "nota_textual": None, "aprobado": True},
            {"nota_numerica": 90.0, "nota_textual": None, "aprobado": True},
            {"nota_numerica": 70.0, "nota_textual": None, "aprobado": True},
        ]
        result = _calcular_nota_final(calificaciones, umbral_pct=60)
        assert result["nota_final"] == 80.0
        assert result["estado"] == "aprobado"
        assert result["total_actividades"] == 3

    def test_below_threshold_is_reprobado(self):
        """Average below threshold yields estado=reprobado."""
        calificaciones = [
            {"nota_numerica": 50.0, "nota_textual": None, "aprobado": False},
            {"nota_numerica": 60.0, "nota_textual": None, "aprobado": False},
            {"nota_numerica": 55.0, "nota_textual": None, "aprobado": False},
        ]
        result = _calcular_nota_final(calificaciones, umbral_pct=60)
        assert result["nota_final"] == 55.0
        assert result["estado"] == "reprobado"

    def test_mixed_grade_types(self):
        """Textual grades do not affect numeric average but count in total."""
        calificaciones = [
            {"nota_numerica": 75.0, "nota_textual": None, "aprobado": True},
            {"nota_numerica": 85.0, "nota_textual": None, "aprobado": True},
            {"nota_numerica": None, "nota_textual": "Satisfactorio", "aprobado": True},
        ]
        result = _calcular_nota_final(calificaciones, umbral_pct=60)
        assert result["nota_final"] == 80.0
        assert result["total_actividades"] == 3

    def test_only_textual_grades(self):
        """Only textual grades — nota_final is 0.0 (no numeric grades to average)."""
        calificaciones = [
            {"nota_numerica": None, "nota_textual": "Satisfactorio", "aprobado": True},
            {"nota_numerica": None, "nota_textual": "Aprobado", "aprobado": True},
        ]
        result = _calcular_nota_final(calificaciones, umbral_pct=60)
        assert result["nota_final"] == 0.0
        assert result["total_actividades"] == 2
        assert result["estado"] == "reprobado"

    def test_empty_calificaciones(self):
        """No calificaciones returns zero values."""
        result = _calcular_nota_final([], umbral_pct=60)
        assert result["nota_final"] == 0.0
        assert result["estado"] == "reprobado"
        assert result["total_actividades"] == 0


class TestDetectarSinCorregir:
    """Test _detectar_sin_corregir — heuristic detection for RN-07/RN-08."""

    def test_textual_activities_detected(self):
        """Alumno_B without textual grade for TP 2 is detected as sin_corregir."""
        actividades_textuales = ["TP 1", "TP 2"]
        alumnos = [
            {
                "entrada_padron_id": "s1",
                "nombre": "Alumno_A",
                "apellidos": "Uno",
                "comision": "A",
                "calificaciones": [
                    {"actividad": "TP 1", "nota_textual": "Satisfactorio", "nota_numerica": None},
                    {"actividad": "TP 2", "nota_textual": "Satisfactorio", "nota_numerica": None},
                ],
            },
            {
                "entrada_padron_id": "s2",
                "nombre": "Alumno_B",
                "apellidos": "Dos",
                "comision": "A",
                "calificaciones": [
                    {"actividad": "TP 1", "nota_textual": "Satisfactorio", "nota_numerica": None},
                    # No record for TP 2
                ],
            },
        ]
        result = _detectar_sin_corregir(alumnos, actividades_textuales)
        assert len(result) == 1
        assert result[0]["nombre"] == "Alumno_B"
        assert result[0]["actividad"] == "TP 2"
        assert result[0]["estado"] == "sin_corregir"

    def test_all_graded_returns_empty(self):
        """All students have grades for all textual activities."""
        actividades_textuales = ["TP 1", "TP 2"]
        alumnos = [
            {
                "entrada_padron_id": "s1",
                "nombre": "A",
                "apellidos": "Uno",
                "comision": "A",
                "calificaciones": [
                    {"actividad": "TP 1", "nota_textual": "Satisfactorio", "nota_numerica": None},
                    {"actividad": "TP 2", "nota_textual": "Aprobado", "nota_numerica": None},
                ],
            },
        ]
        result = _detectar_sin_corregir(alumnos, actividades_textuales)
        assert result == []

    def test_no_textual_activities(self):
        """No textual activities returns empty (RN-08)."""
        result = _detectar_sin_corregir([], [])
        assert result == []

    def test_numeric_grades_excluded(self):
        """Numeric-only actividades are not included in textual activities list."""
        actividades_textuales = ["TP 1"]
        alumnos = [
            {
                "entrada_padron_id": "s1",
                "nombre": "A",
                "apellidos": "Uno",
                "comision": "A",
                "calificaciones": [],  # No textual grade for TP 1
            },
        ]
        result = _detectar_sin_corregir(alumnos, actividades_textuales)
        assert len(result) == 1
        assert result[0]["actividad"] == "TP 1"

    def test_filter_by_comision(self):
        """Only alumnos from especific comision are included."""
        actividades_textuales = ["TP 1"]
        alumnos = [
            {
                "entrada_padron_id": "s1",
                "nombre": "A",
                "apellidos": "Uno",
                "comision": "A",
                "calificaciones": [],
            },
            {
                "entrada_padron_id": "s2",
                "nombre": "B",
                "apellidos": "Dos",
                "comision": "B",
                "calificaciones": [],
            },
        ]
        # Filter only comision A
        filtered = [a for a in alumnos if a["comision"] == "A"]
        result = _detectar_sin_corregir(filtered, actividades_textuales)
        assert len(result) == 1
        assert result[0]["comision"] == "A"


class TestCalcularPromedioCumplimiento:
    """Test _calcular_promedio_cumplimiento helper."""

    def test_average_calculation(self):
        """(80 + 50 + 100) / 3 = 76.67."""
        items = [
            {"porcentaje_cumplimiento": 80.0},
            {"porcentaje_cumplimiento": 50.0},
            {"porcentaje_cumplimiento": 100.0},
        ]
        result = _calcular_promedio_cumplimiento(items)
        assert result == 76.67

    def test_empty_items_returns_zero(self):
        """Empty list returns 0.0."""
        assert _calcular_promedio_cumplimiento([]) == 0.0

    def test_single_item(self):
        """Single item returns its value."""
        items = [{"porcentaje_cumplimiento": 45.5}]
        assert _calcular_promedio_cumplimiento(items) == 45.5


class TestBuildCsvRows:
    """Test _build_csv_rows helper (reused from atrasados_ranking)."""

    def test_builds_csv_with_headers_and_data(self):
        """Builds CSV string with headers and data rows."""
        headers = ["nombre", "apellidos", "nota_final", "estado"]
        data = [
            {"nombre": "Juan", "apellidos": "Perez", "nota_final": "80.00", "estado": "aprobado"},
            {"nombre": "Maria", "apellidos": "Gomez", "nota_final": "55.00", "estado": "reprobado"},
        ]
        csv_content = _build_csv_rows(headers, data)
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=";")
        rows = list(reader)
        assert len(rows) == 2
        first_key = list(rows[0].keys())[0]
        assert rows[0][first_key] == "Juan"
        assert rows[1]["estado"] == "reprobado"

    def test_csv_with_empty_data(self):
        """Empty data returns only headers."""
        headers = ["nombre", "apellidos", "nota_final"]
        csv_content = _build_csv_rows(headers, [])
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=";")
        rows = list(reader)
        assert len(rows) == 0
        fieldnames = [
            fn.removeprefix("\ufeff") if fn.startswith("\ufeff") else fn
            for fn in (reader.fieldnames or [])
        ]
        assert fieldnames == ["nombre", "apellidos", "nota_final"]

    def test_csv_has_utf8_bom(self):
        """CSV output starts with UTF-8 BOM."""
        headers = ["nombre"]
        data = [{"nombre": "test"}]
        csv_content = _build_csv_rows(headers, data)
        assert csv_content.startswith("\ufeff")

    def test_csv_uses_semicolon_delimiter(self):
        """CSV uses semicolon as delimiter."""
        headers = ["nombre", "nota_final"]
        data = [{"nombre": "Juan", "nota_final": "80.00"}]
        csv_content = _build_csv_rows(headers, data)
        assert "Juan;80.00" in csv_content
