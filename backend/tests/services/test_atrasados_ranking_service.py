"""Unit tests for atrasados-ranking service pure functions.

These tests do NOT require a database connection.
They test the classification, ranking, metrics, and CSV logic in isolation.
"""

import csv
import io

import pytest

from app.services.atrasados_ranking import (
    _build_csv_rows,
    _calculate_porcentaje,
    _clasificar_alumnos,
    _ordenar_ranking,
)


class TestClasificarAlumnos:
    """Test _clasificar_alumnos — RN-06 detection logic."""

    def test_empty_students_list_returns_empty(self):
        """No students returns empty atrasados list."""
        alumnos = _clasificar_alumnos([], umbral=60)
        assert alumnos == []

    def test_student_without_grades_is_faltante(self):
        """Student with no grades is atrasado = faltante."""
        students = [
            {
                "entrada_padron_id": "s1",
                "nombre": "Juan",
                "apellidos": "Perez",
                "email": "juan@test.com",
                "comision": "A",
                "calificaciones": [],
            },
        ]
        result = _clasificar_alumnos(students, umbral=60)
        assert len(result) == 1
        assert result[0]["razon"] == "faltante"
        assert result[0]["total_actividades"] == 0

    def test_student_with_nota_baja_is_atrasado(self):
        """Student with nota_numerica below threshold is atrasado = nota_baja."""
        students = [
            {
                "entrada_padron_id": "s1",
                "nombre": "Maria",
                "apellidos": "Gomez",
                "email": "maria@test.com",
                "comision": "A",
                "calificaciones": [
                    {"nota_numerica": 45.0, "aprobado": False},
                ],
            },
        ]
        result = _clasificar_alumnos(students, umbral=60)
        assert len(result) == 1
        assert result[0]["razon"] == "nota_baja"
        assert result[0]["nota_minima"] == 45.0
        assert result[0]["umbral"] == 60

    def test_student_above_threshold_no_atrasado(self):
        """Student with notas above threshold is NOT atrasado."""
        students = [
            {
                "entrada_padron_id": "s1",
                "nombre": "Carlos",
                "apellidos": "Lopez",
                "email": "carlos@test.com",
                "comision": "A",
                "calificaciones": [
                    {"nota_numerica": 85.0, "aprobado": True},
                    {"nota_numerica": 75.0, "aprobado": True},
                ],
            },
        ]
        result = _clasificar_alumnos(students, umbral=60)
        assert len(result) == 0

    def test_mixed_conditions(self):
        """Multiple students: faltante, nota_baja, and safe."""
        students = [
            {
                "entrada_padron_id": "s1",
                "nombre": "Ana",
                "apellidos": "Silva",
                "email": "ana@test.com",
                "comision": "A",
                "calificaciones": [],
            },
            {
                "entrada_padron_id": "s2",
                "nombre": "Luis",
                "apellidos": "Martinez",
                "email": "luis@test.com",
                "comision": "B",
                "calificaciones": [
                    {"nota_numerica": 30.0, "aprobado": False},
                ],
            },
            {
                "entrada_padron_id": "s3",
                "nombre": "Sofia",
                "apellidos": "Garcia",
                "email": "sofia@test.com",
                "comision": "A",
                "calificaciones": [
                    {"nota_numerica": 80.0, "aprobado": True},
                    {"nota_numerica": 90.0, "aprobado": True},
                ],
            },
        ]
        result = _clasificar_alumnos(students, umbral=60)
        assert len(result) == 2
        assert result[0]["razon"] == "faltante"
        assert result[1]["razon"] == "nota_baja"

    def test_nota_minima_selected_correctly(self):
        """nota_minima is the lowest numeric grade across all activities."""
        students = [
            {
                "entrada_padron_id": "s1",
                "nombre": "Pedro",
                "apellidos": "Ramirez",
                "email": "pedro@test.com",
                "comision": "C",
                "calificaciones": [
                    {"nota_numerica": 80.0, "aprobado": True},
                    {"nota_numerica": 55.0, "aprobado": False},
                    {"nota_numerica": 90.0, "aprobado": True},
                ],
            },
        ]
        result = _clasificar_alumnos(students, umbral=60)
        assert len(result) == 1
        assert result[0]["razon"] == "nota_baja"
        assert result[0]["nota_minima"] == 55.0

    def test_total_actividades_count(self):
        """total_actividades counts all grades for the student."""
        students = [
            {
                "entrada_padron_id": "s1",
                "nombre": "Lucia",
                "apellidos": "Diaz",
                "email": "lucia@test.com",
                "comision": "A",
                "calificaciones": [
                    {"nota_numerica": 50.0, "aprobado": False},
                    {"nota_numerica": 30.0, "aprobado": False},
                    {"nota_numerica": 70.0, "aprobado": True},
                ],
            },
        ]
        result = _clasificar_alumnos(students, umbral=60)
        assert result[0]["total_actividades"] == 3
        assert result[0]["nota_minima"] == 30.0


class TestOrdenarRanking:
    """Test _ordenar_ranking — RN-09 ordering logic."""

    def test_empty_ranking(self):
        """Empty data returns empty list."""
        assert _ordenar_ranking([]) == []

    def test_ordered_by_total_aprobadas_desc(self):
        """Ranking is sorted by total_aprobadas descending."""
        data = [
            {"entrada_padron_id": "s1", "nombre": "A", "apellidos": "X", "comision": "A",
             "total_aprobadas": 3, "total_actividades": 5, "porcentaje_aprobacion": 60.0},
            {"entrada_padron_id": "s2", "nombre": "B", "apellidos": "Y", "comision": "A",
             "total_aprobadas": 5, "total_actividades": 5, "porcentaje_aprobacion": 100.0},
            {"entrada_padron_id": "s3", "nombre": "C", "apellidos": "Z", "comision": "B",
             "total_aprobadas": 1, "total_actividades": 4, "porcentaje_aprobacion": 25.0},
        ]
        result = _ordenar_ranking(data)
        assert [r["entrada_padron_id"] for r in result] == ["s2", "s1", "s3"]

    def test_ties_preserve_order(self):
        """Ties in total_aprobadas preserve original order."""
        data = [
            {"entrada_padron_id": "s1", "nombre": "A", "total_aprobadas": 2},
            {"entrada_padron_id": "s2", "nombre": "B", "total_aprobadas": 2},
        ]
        result = _ordenar_ranking(data)
        assert result[0]["entrada_padron_id"] == "s1"
        assert result[1]["entrada_padron_id"] == "s2"

    def test_single_entry(self):
        """Single entry ranking works."""
        data = [
            {"entrada_padron_id": "s1", "nombre": "A", "total_aprobadas": 4},
        ]
        result = _ordenar_ranking(data)
        assert len(result) == 1
        assert result[0]["total_aprobadas"] == 4


class TestCalculatePorcentaje:
    """Test _calculate_porcentaje helper."""

    def test_basic_percentage(self):
        """3 out of 4 = 75.0%."""
        assert _calculate_porcentaje(3, 4) == 75.0

    def test_zero_total_returns_zero(self):
        """0 total returns 0.0 to avoid division by zero."""
        assert _calculate_porcentaje(0, 0) == 0.0

    def test_all_approved(self):
        """5 out of 5 = 100.0%."""
        assert _calculate_porcentaje(5, 5) == 100.0

    def test_none_approved(self):
        """0 out of 5 = 0.0%."""
        assert _calculate_porcentaje(0, 5) == 0.0

    def test_rounding_two_decimals(self):
        """Result is rounded to 2 decimal places."""
        assert _calculate_porcentaje(1, 3) == 33.33


class TestBuildCsvRows:
    """Test _build_csv_rows helper."""

    def test_builds_csv_with_headers_and_data(self):
        """Builds CSV string with headers and data rows."""
        headers = ["nombre", "apellidos", "razon"]
        data = [
            {"nombre": "Juan", "apellidos": "Perez", "razon": "faltante"},
            {"nombre": "Maria", "apellidos": "Gomez", "razon": "nota_baja"},
        ]
        csv_content = _build_csv_rows(headers, data)
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=";")
        rows = list(reader)
        assert len(rows) == 2
        # BOM is prepended to the first fieldname; access by key with BOM
        first_key = list(rows[0].keys())[0]
        assert rows[0][first_key] == "Juan"
        assert rows[1]["razon"] == "nota_baja"

    def test_csv_with_empty_data(self):
        """Empty data returns only headers."""
        headers = ["nombre", "apellidos"]
        csv_content = _build_csv_rows(headers, [])
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=";")
        rows = list(reader)
        assert len(rows) == 0
        # Strip BOM from first fieldname if present
        fieldnames = [
            fn.removeprefix("\ufeff") if fn.startswith("\ufeff") else fn
            for fn in (reader.fieldnames or [])
        ]
        assert fieldnames == ["nombre", "apellidos"]

    def test_csv_has_utf8_bom(self):
        """CSV output starts with UTF-8 BOM."""
        headers = ["nombre"]
        data = [{"nombre": "test"}]
        csv_content = _build_csv_rows(headers, data)
        assert csv_content.startswith("\ufeff")

    def test_csv_uses_semicolon_delimiter(self):
        """CSV uses semicolon as delimiter."""
        headers = ["nombre", "apellidos"]
        data = [{"nombre": "Juan", "apellidos": "Perez"}]
        csv_content = _build_csv_rows(headers, data)
        assert "Juan;Perez" in csv_content

    def test_missing_field_in_data_is_empty(self):
        """Missing field in data row becomes empty string."""
        headers = ["nombre", "apellidos", "email"]
        data = [{"nombre": "Juan", "apellidos": "Perez"}]
        csv_content = _build_csv_rows(headers, data)
        assert "Juan;Perez;" in csv_content
