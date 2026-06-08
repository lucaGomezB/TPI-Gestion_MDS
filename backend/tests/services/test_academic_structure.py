"""Tests for academic structure services.

Uses mocked repositories to test business logic in isolation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.carrera import Carrera
from app.models.cohorte import Cohorte
from app.models.materia import Materia
from app.models.mixins import EstadoAcademico
from app.schemas.academic_structure import (
    CarreraCreate,
    CarreraUpdate,
    CohorteCreate,
    MateriaCreate,
    MateriaUpdate,
)
from app.services.academic_structure import (
    CarreraService,
    CohorteService,
    MateriaService,
)


@pytest.fixture
def mock_session():
    return MagicMock(spec=AsyncSession)


@pytest.fixture
def carrera_service(mock_session):
    return CarreraService(mock_session, tenant_id="tenant-a")


@pytest.fixture
def cohorte_service(mock_session):
    return CohorteService(mock_session, tenant_id="tenant-a")


@pytest.fixture
def materia_service(mock_session):
    return MateriaService(mock_session, tenant_id="tenant-a")


class TestCarreraServiceCreate:
    """Task 7.4: CarreraService create with duplicate codigo."""

    @pytest.mark.asyncio
    async def test_create_duplicate_codigo_raises_409(self, carrera_service):
        """Creating a carrera with an existing codigo should raise 409."""
        # Arrange: simulate existing carrera with same codigo
        from datetime import datetime
        now = datetime.now()
        existing = Carrera(
            id="existing-id",
            codigo="TUPAD",
            nombre="Existing",
            tenant_id="tenant-a",
            estado="Activa",
            created_at=now,
            updated_at=now,
        )
        carrera_service.repo.find_by_codigo = AsyncMock(return_value=existing)

        data = CarreraCreate(codigo="TUPAD", nombre="Test")

        # Act & Assert
        with pytest.raises(HTTPException) as exc:
            await carrera_service.create(data)
        assert exc.value.status_code == 409
        assert "already exists" in exc.value.detail

    @pytest.mark.asyncio
    async def test_create_duplicate_different_tenant_ok(
        self, mock_session
    ):
        """Same codigo in different tenant should work."""
        service_a = CarreraService(mock_session, tenant_id="tenant-a")
        service_b = CarreraService(mock_session, tenant_id="tenant-b")

        existing_a = Carrera()
        existing_a.id = "id-a"
        existing_a.codigo = "TUPAD"
        existing_a.tenant_id = "tenant-a"

        from datetime import datetime

        service_a.repo.find_by_codigo = AsyncMock(
            return_value=existing_a
        )
        service_a.repo.create = AsyncMock(return_value=existing_a)

        service_b.repo.find_by_codigo = AsyncMock(return_value=None)
        now = datetime.now()
        new_b = Carrera(
            id="id-b",
            codigo="TUPAD",
            nombre="Test B",
            tenant_id="tenant-b",
            estado="Activa",
            created_at=now,
            updated_at=now,
        )
        service_b.repo.create = AsyncMock(return_value=new_b)

        data = CarreraCreate(codigo="TUPAD", nombre="Test B")
        result = await service_b.create(data)
        assert result.codigo == "TUPAD"


class TestCarreraServiceDeactivate:
    """Task 7.8: CarreraService deactivate with active cohortes."""

    @pytest.mark.asyncio
    async def test_deactivate_with_active_cohortes_raises_422(
        self, carrera_service
    ):
        """Deactivating a carrera with active cohortes should raise 422."""
        from datetime import datetime
        now = datetime.now()
        existing = Carrera(
            id="carrera-1",
            codigo="TUPAD",
            nombre="Test",
            tenant_id="tenant-a",
            estado=EstadoAcademico.ACTIVA,
            created_at=now,
            updated_at=now,
        )

        carrera_service.repo.get_by_id = AsyncMock(return_value=existing)
        carrera_service.repo.count_active_cohortes = AsyncMock(return_value=3)

        data = CarreraUpdate(estado="Inactiva")

        with pytest.raises(HTTPException) as exc:
            await carrera_service.update("carrera-1", data)
        assert exc.value.status_code == 422
        assert "active cohortes" in exc.value.detail

    @pytest.mark.asyncio
    async def test_deactivate_without_cohortes_ok(self, carrera_service):
        """Deactivating a carrera with no active cohortes should work."""
        existing = Carrera()
        existing.id = "carrera-1"
        existing.codigo = "TUPAD"
        existing.tenant_id = "tenant-a"
        existing.estado = EstadoAcademico.ACTIVA

        carrera_service.repo.get_by_id = AsyncMock(return_value=existing)
        from datetime import datetime
        now = datetime.now()
        carrera_service.repo.count_active_cohortes = AsyncMock(return_value=0)
        updated = Carrera(
            id="carrera-1",
            codigo="TUPAD",
            nombre="Test",
            tenant_id="tenant-a",
            estado=EstadoAcademico.INACTIVA,
            created_at=now,
            updated_at=now,
        )
        carrera_service.repo.update = AsyncMock(return_value=updated)

        data = CarreraUpdate(estado="Inactiva")
        result = await carrera_service.update("carrera-1", data)
        assert result.estado == "Inactiva"


class TestMateriaServiceCreate:
    """Task 7.5: MateriaService create with duplicate codigo."""

    @pytest.mark.asyncio
    async def test_create_duplicate_codigo_raises_409(self, materia_service):
        """Creating a materia with an existing codigo should raise 409."""
        from datetime import datetime
        now = datetime.now()
        existing = Materia(
            id="existing-id",
            codigo="PROG_I",
            nombre="Existing",
            tenant_id="tenant-a",
            estado="Activa",
            created_at=now,
            updated_at=now,
        )
        materia_service.repo.find_by_codigo = AsyncMock(return_value=existing)

        data = MateriaCreate(codigo="PROG_I", nombre="Test")

        with pytest.raises(HTTPException) as exc:
            await materia_service.create(data)
        assert exc.value.status_code == 409
        assert "already exists" in exc.value.detail


class TestCohorteServiceCreate:
    """Tasks 7.6, 7.7: CohorteService create validations."""

    @pytest.fixture
    def mock_result(self):
        """Create a mock for session.execute() result."""
        result = MagicMock()
        result.scalar_one_or_none = MagicMock()
        return result

    @pytest.mark.asyncio
    async def test_create_duplicate_nombre_raises_409(
        self, cohorte_service, mock_result
    ):
        """Creating a cohorte with duplicate nombre in same carrera should raise 409."""
        # Mock the session to:
        # 1. Find carrera (success)
        # 2. Find duplicate cohorte (found)

        # First call = find carrera by id → return carrera
        mock_result.scalar_one_or_none = MagicMock()
        mock_result.scalar_one_or_none.side_effect = [
            MagicMock(id="carrera-1", tenant_id="tenant-a"),  # Carrera found
            MagicMock(  # Duplicate cohorte found
                id="existing-id",
                nombre="MAR-2025",
                carrera_id="carrera-1",
                tenant_id="tenant-a",
            ),
        ]
        cohorte_service.repo.session.execute = AsyncMock(return_value=mock_result)

        data = CohorteCreate(
            carrera_id="carrera-1",
            nombre="MAR-2025",
            anio=2025,
            vig_desde="2025-03-01",
        )

        with pytest.raises(HTTPException) as exc:
            await cohorte_service.create(data)
        assert exc.value.status_code == 409
        assert "already exists" in exc.value.detail

    @pytest.mark.asyncio
    async def test_create_cross_tenant_carrera_raises_404(
        self, cohorte_service, mock_result
    ):
        """Creating a cohorte with a carrera from another tenant should raise 404."""
        # Mock session.execute to return None for the carrera lookup
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        cohorte_service.repo.session.execute = AsyncMock(return_value=mock_result)

        data = CohorteCreate(
            carrera_id="other-tenant-carrera",
            nombre="MAR-2025",
            anio=2025,
            vig_desde="2025-03-01",
        )

        with pytest.raises(HTTPException) as exc:
            await cohorte_service.create(data)
        assert exc.value.status_code == 404
        assert "Carrera not found" in exc.value.detail
