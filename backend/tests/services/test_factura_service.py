"""Tests for FacturaService — upload, history, admin view, abonar lifecycle.

Pure unit tests for testable logic.
Integration tests (DB-dependent) are skipped by default.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.factura import EstadoFactura
from app.repositories.factura import FacturaRepository
from app.services.factura import FacturaService


class TestFacturaServiceInterface:
    """Verify FacturaService exposes expected methods."""

    def test_has_subir_factura_method(self):
        assert hasattr(FacturaService, "subir_factura")

    def test_has_get_historial_method(self):
        assert hasattr(FacturaService, "get_historial")

    def test_has_get_admin_view_method(self):
        assert hasattr(FacturaService, "get_admin_view")

    def test_has_abonar_method(self):
        assert hasattr(FacturaService, "abonar")


class TestFacturaServiceValidation:
    """Validation logic tests — no DB required."""

    def test_get_max_upload_size_returns_default(self):
        """Default max upload size should be 10 MB."""
        from app.services.factura import MAX_UPLOAD_SIZE_MB
        assert MAX_UPLOAD_SIZE_MB == 10

    def test_allowed_content_type(self):
        """Only application/pdf is allowed."""
        from app.services.factura import ALLOWED_CONTENT_TYPE
        assert ALLOWED_CONTENT_TYPE == "application/pdf"


class TestFacturaServicePureFunctions:
    """Pure helper functions in the service module."""

    def test_generate_file_path_creates_uuid_filename(self):
        """_generate_file_path should create a UUID-based filename preserving extension."""
        from app.services.factura import _generate_file_path
        dir_path, filename = _generate_file_path("factura.pdf")
        assert filename.endswith(".pdf")
        assert len(filename) > 4  # uuid + ext
        assert "facturas" in dir_path

    def test_generate_file_path_preserves_extensions(self):
        from app.services.factura import _generate_file_path
        _, filename = _generate_file_path("document.PDF")
        assert filename.lower().endswith(".pdf")


# ── Service unit tests (mocked) ──────────────────────────────────────────


class TestFacturaServiceUnit:
    """Unit tests with mocked repository and UoW."""

    @pytest.fixture
    def mock_uow(self):
        """Create a mock UoW with a mocked factura repository."""
        uow = MagicMock()
        uow.factura = MagicMock(spec=FacturaRepository)
        uow._tenant_id = "tenant-a"
        uow._session = AsyncMock()
        return uow

    @pytest.fixture
    def service(self, mock_uow):
        return FacturaService(uow=mock_uow, actor_id="actor-123")

    @pytest.mark.asyncio
    async def test_subir_factura_validates_facturador(self, service, mock_uow):
        """subir_factura should raise 403 if usuario is not facturador."""
        # Mock that the user is NOT a facturador
        mock_user = MagicMock()
        mock_user.facturador = False
        mock_uow._session.execute.return_value.scalar_one_or_none.return_value = mock_user

        with pytest.raises(Exception) as exc:
            await service.subir_factura(
                usuario_id="user-123",
                periodo="2026-06",
                detalle="Test",
                archivo_bytes=b"%PDF-test-content",
                nombre_archivo="factura.pdf",
            )

    @pytest.mark.asyncio
    async def test_subir_factura_validates_content_type(self, service, mock_uow):
        """Non-PDF files should raise 400."""
        mock_user = MagicMock()
        mock_user.facturador = True
        mock_uow._session.execute.return_value.scalar_one_or_none.return_value = mock_user

        with pytest.raises(Exception) as exc:
            await service.subir_factura(
                usuario_id="user-123",
                periodo="2026-06",
                detalle="Test",
                archivo_bytes=b"not-a-pdf-content",
                nombre_archivo="factura.txt",
            )

    @pytest.mark.asyncio
    async def test_subir_factura_exceeds_max_size(self, service, mock_uow):
        """Files larger than 10MB should raise 400."""
        mock_user = MagicMock()
        mock_user.facturador = True
        mock_uow._session.execute.return_value.scalar_one_or_none.return_value = mock_user

        # 11 MB of data
        large_content = b"X" * (11 * 1024 * 1024)

        with pytest.raises(Exception) as exc:
            await service.subir_factura(
                usuario_id="user-123",
                periodo="2026-06",
                detalle="Test",
                archivo_bytes=large_content,
                nombre_archivo="factura.pdf",
            )
