"""Unit tests for padron service utilities (column detection, parsing).

These tests do NOT require a database connection.
They test the column detection logic and file parsing in isolation.
"""

import pytest
from fastapi import HTTPException

from app.services.padron import _detect_columns, _normalize_header


class TestNormalizeHeader:
    """Test _normalize_header function."""

    def test_lowercases(self):
        """Normalize header: lowercases input."""
        assert _normalize_header("NOMBRE") == "nombre"
        assert _normalize_header("Email") == "email"

    def test_strips_whitespace(self):
        """Normalize header: strips surrounding whitespace."""
        assert _normalize_header("  nombre  ") == "nombre"
        assert _normalize_header("\temail\n") == "email"

    def test_handles_empty(self):
        """Normalize header: empty string returns empty."""
        assert _normalize_header("") == ""

    def test_handles_bom(self):
        """Normalize header: handles BOM-prefixed strings."""
        assert _normalize_header("\ufeffNombre") == "\ufeffnombre"


class TestDetectColumns:
    """Test _detect_columns function."""

    def test_all_required_present(self):
        """Detect columns: returns mapping when all required columns present."""
        headers = ["Nombre", "Apellidos", "Email", "Comision"]
        mapping = _detect_columns(headers)
        assert "nombre" in mapping
        assert "email" in mapping
        assert mapping["nombre"] == "nombre"
        assert mapping["email"] == "email"

    def test_case_insensitive_headers(self):
        """Detect columns: handles case-insensitive headers."""
        headers = ["NOMBRE", "APELLIDOS", "EMAIL"]
        mapping = _detect_columns(headers)
        assert "nombre" in mapping
        assert "email" in mapping

    def test_headers_with_spaces(self):
        """Detect columns: handles headers with extra spaces."""
        headers = ["  Nombre  ", "  Email  "]
        mapping = _detect_columns(headers)
        assert "nombre" in mapping
        assert "email" in mapping

    def test_missing_nombre_raises(self):
        """Detect columns: missing nombre raises 400."""
        headers = ["Email", "Apellidos"]
        with pytest.raises(HTTPException) as exc:
            _detect_columns(headers)
        assert exc.value.status_code == 400
        assert "nombre" in exc.value.detail

    def test_missing_email_raises(self):
        """Detect columns: missing email raises 400."""
        headers = ["Nombre", "Apellidos"]
        with pytest.raises(HTTPException) as exc:
            _detect_columns(headers)
        assert exc.value.status_code == 400
        assert "email" in exc.value.detail

    def test_both_missing_raises(self):
        """Detect columns: both missing raises 400 with both names."""
        headers = ["Apellidos", "Comision"]
        with pytest.raises(HTTPException) as exc:
            _detect_columns(headers)
        assert "nombre" in exc.value.detail
        assert "email" in exc.value.detail

    def test_optional_columns_detected(self):
        """Detect columns: optional columns like comision, regional are detected."""
        headers = ["Nombre", "Email", "Comision", "Regional"]
        mapping = _detect_columns(headers)
        assert "comision" in mapping
        assert "regional" in mapping

    def test_apellidos_or_apellido(self):
        """Detect columns: both 'apellidos' and 'apellido' map to 'apellidos'."""
        headers_map_apellidos = _detect_columns(["Nombre", "Email", "Apellidos"])
        assert "apellidos" in headers_map_apellidos

        headers_map_apellido = _detect_columns(["Nombre", "Email", "Apellido"])
        assert "apellidos" in headers_map_apellido

    def test_unknown_columns_ignored(self):
        """Detect columns: unknown columns are ignored without error."""
        headers = ["Nombre", "Email", "UnknownColumn", "OTRO"]
        # Should not raise
        mapping = _detect_columns(headers)
        assert "nombre" in mapping
        assert "email" in mapping
        # Unknown column should NOT be in mapping
        assert "unknowncolumn" not in mapping
