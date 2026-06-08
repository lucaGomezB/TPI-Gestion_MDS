"""Tests for Factura Pydantic schemas (C-20).

Tests extra='forbid', field types, and validation rules.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.factura import (
    EstadoFactura,
    FacturaCreate,
    FacturaDetailResponse,
    FacturaListResponse,
    FacturaResponse,
)


class TestEstadoFacturaEnum:
    """Verify EstadoFactura values in schemas match model enum."""

    def test_values_match_model(self):
        assert EstadoFactura.PENDIENTE.value == "Pendiente"
        assert EstadoFactura.ABONADA.value == "Abonada"

    def test_only_two_values(self):
        assert len(list(EstadoFactura)) == 2


class TestFacturaCreate:
    """FacturaCreate schema — used internally to create records."""

    def test_valid_create(self):
        data = FacturaCreate(
            usuario_id="usr-123",
            periodo="2026-06",
            detalle="Factura junio 2026 - Honorarios",
            referencia_archivo="uploads/facturas/abc-123.pdf",
            tamano_kb=1024.50,
        )
        assert data.usuario_id == "usr-123"
        assert data.periodo == "2026-06"
        assert data.tamano_kb == 1024.50

    def test_periodo_format_validation(self):
        """periodo must be exactly YYYY-MM (7 chars)."""
        with pytest.raises(ValidationError):
            FacturaCreate(
                usuario_id="usr-123",
                periodo="2026-006",  # wrong format
                detalle="Test",
                referencia_archivo="path/to/file.pdf",
                tamano_kb=100,
            )

    @pytest.mark.parametrize("periodo", ["2026-1", "2026-123", "abcdefg"])
    def test_invalid_periodo_formats(self, periodo):
        with pytest.raises(ValidationError):
            FacturaCreate(
                usuario_id="usr-123",
                periodo=periodo,
                detalle="Test",
                referencia_archivo="path/file.pdf",
                tamano_kb=100,
            )

    def test_extra_fields_forbidden(self):
        """All schemas must reject undeclared fields."""
        with pytest.raises(ValidationError):
            FacturaCreate(
                usuario_id="usr-123",
                periodo="2026-06",
                detalle="Test",
                referencia_archivo="path/file.pdf",
                tamano_kb=100,
                extra_field="should not be allowed",
            )

    def test_tamano_kb_negative(self):
        """tamano_kb should allow 0 or positive values."""
        with pytest.raises(ValidationError):
            FacturaCreate(
                usuario_id="usr-123",
                periodo="2026-06",
                detalle="Test",
                referencia_archivo="path/file.pdf",
                tamano_kb=-100,
            )


class TestFacturaResponse:
    """FacturaResponse schema — API output for list views."""

    def test_valid_response(self):
        data = FacturaResponse(
            id="fact-123",
            tenant_id="tenant-a",
            usuario_id="usr-123",
            periodo="2026-06",
            detalle="Factura junio",
            referencia_archivo="uploads/facturas/abc.pdf",
            tamano_kb=500.00,
            estado="Pendiente",
            cargada_at="2026-06-01T10:00:00Z",
            abonada_at=None,
        )
        assert data.id == "fact-123"
        assert data.estado == "Pendiente"
        assert data.abonada_at is None

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            FacturaResponse(
                id="fact-123",
                tenant_id="tenant-a",
                usuario_id="usr-123",
                periodo="2026-06",
                detalle="Test",
                referencia_archivo="path/file.pdf",
                tamano_kb=100,
                estado="Pendiente",
                cargada_at="2026-06-01T10:00:00Z",
                extra="not allowed",
            )

    def test_abonada_at_with_value(self):
        data = FacturaResponse(
            id="fact-123",
            tenant_id="tenant-a",
            usuario_id="usr-123",
            periodo="2026-06",
            detalle="Test",
            referencia_archivo="path/file.pdf",
            tamano_kb=100,
            estado="Abonada",
            cargada_at="2026-06-01T10:00:00Z",
            abonada_at="2026-06-15T14:30:00Z",
        )
        assert data.abonada_at == "2026-06-15T14:30:00Z"


class TestFacturaDetailResponse:
    """FacturaDetailResponse — includes file download URL."""

    def test_inherits_response_fields(self):
        data = FacturaDetailResponse(
            id="fact-123",
            tenant_id="tenant-a",
            usuario_id="usr-123",
            periodo="2026-06",
            detalle="Test",
            referencia_archivo="path/file.pdf",
            tamano_kb=100,
            estado="Pendiente",
            cargada_at="2026-06-01T10:00:00Z",
            descargar_url="/api/admin/facturas/fact-123/descargar",
        )
        assert data.descargar_url == "/api/admin/facturas/fact-123/descargar"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            FacturaDetailResponse(
                id="fact-123",
                tenant_id="tenant-a",
                usuario_id="usr-123",
                periodo="2026-06",
                detalle="Test",
                referencia_archivo="path/file.pdf",
                tamano_kb=100,
                estado="Pendiente",
                cargada_at="2026-06-01T10:00:00Z",
                descargar_url="/descargar",
                extra="not allowed",
            )


class TestFacturaListResponse:
    """FacturaListResponse — paginated list."""

    def test_valid_list_response(self):
        data = FacturaListResponse(
            items=[
                FacturaResponse(
                    id="f1",
                    tenant_id="tenant-a",
                    usuario_id="u1",
                    periodo="2026-06",
                    detalle="Factura 1",
                    referencia_archivo="path/1.pdf",
                    tamano_kb=100,
                    estado="Pendiente",
                    cargada_at="2026-06-01T10:00:00Z",
                )
            ],
            total=1,
            page=1,
            page_size=50,
        )
        assert len(data.items) == 1
        assert data.total == 1
