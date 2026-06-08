"""Schema unit tests for encuentro Pydantic models (C-14).

Verifies extra='forbid', field validation, and serialization.
"""

import pytest
from pydantic import ValidationError

from app.schemas.encuentros import (
    EmbedResponse,
    InstanciaEncuentroCreate,
    InstanciaEncuentroResponse,
    InstanciaEncuentroUpdate,
    SlotEncuentroCreate,
    SlotEncuentroResponse,
)


class TestSlotEncuentroCreate:
    """Task 5.1: SlotEncuentroCreate schema validation."""

    def test_valid_slot(self) -> None:
        """Happy path: minimal valid slot creation data."""
        data = SlotEncuentroCreate(
            asignacion_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
            titulo="Clase 1",
            hora="10:00",
            dia_semana="Lunes",
            fecha_inicio="2026-03-02",
            cant_semanas=16,
            vig_desde="2026-03-01",
        )
        assert data.titulo == "Clase 1"
        assert data.cant_semanas == 16
        assert data.fecha_unica is None

    def test_fecha_unica_slot(self) -> None:
        """Slot with fecha_unica and cant_semanas=0."""
        data = SlotEncuentroCreate(
            asignacion_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
            titulo="Clase Extraordinaria",
            hora="14:00",
            dia_semana="Miercoles",
            fecha_inicio="2026-06-01",
            cant_semanas=0,
            fecha_unica="2026-06-15",
            vig_desde="2026-06-01",
        )
        assert data.cant_semanas == 0
        assert data.fecha_unica.isoformat() == "2026-06-15"

    def test_extra_forbid(self) -> None:
        """Unknown fields are rejected."""
        with pytest.raises(ValidationError):
            SlotEncuentroCreate(
                asignacion_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
                materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
                titulo="Test",
                hora="10:00",
                dia_semana="Lunes",
                fecha_inicio="2026-03-02",
                vig_desde="2026-03-01",
                unknown_field="should_not_exist",
            )


class TestInstanciaEncuentroCreate:
    """Task 5.1: InstanciaEncuentroCreate schema validation."""

    def test_valid_instance(self) -> None:
        """Happy path: minimal valid instance creation data."""
        data = InstanciaEncuentroCreate(
            materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
            fecha="2026-03-09",
            hora="10:00",
            titulo="Clase Semanal 1",
        )
        data_dict = data.model_dump()
        assert data_dict["titulo"] == "Clase Semanal 1"
        assert "materia_id" in data_dict
        assert "meet_url" not in data_dict or data_dict["meet_url"] is None


class TestInstanciaEncuentroUpdate:
    """Task 5.1: InstanciaEncuentroUpdate schema validation."""

    def test_update_estado(self) -> None:
        """Update estado to Realizado."""
        data = InstanciaEncuentroUpdate(estado="Realizado")
        assert data.estado == "Realizado"

    def test_update_video_url(self) -> None:
        """Update video_url."""
        data = InstanciaEncuentroUpdate(video_url="https://vimeo.com/123456")
        assert data.video_url == "https://vimeo.com/123456"

    def test_update_invalid_estado(self) -> None:
        """Invalid estado value is rejected."""
        with pytest.raises(ValidationError):
            InstanciaEncuentroUpdate(estado="Invalido")

    def test_extra_forbid(self) -> None:
        """Unknown fields are rejected."""
        with pytest.raises(ValidationError):
            InstanciaEncuentroUpdate(estado="Realizado", unknown="x")


class TestEmbedResponse:
    """Task 5.1: EmbedResponse schema."""

    def test_valid_embed(self) -> None:
        """Happy path: embed response with data."""
        data = EmbedResponse(
            html="<table>...</table>",
            markdown="### Encuentros\n- Clase 1",
            total=1,
        )
        assert data.total == 1
        assert "<table>" in data.html

    def test_empty_embed(self) -> None:
        """Empty embed response."""
        data = EmbedResponse(
            html="<p>No hay encuentros</p>",
            markdown="_No hay encuentros_",
            total=0,
        )
        assert data.total == 0


class TestSlotEncuentroResponse:
    """Task 5.1: SlotEncuentroResponse from_attributes."""

    def test_serialize_from_model(self) -> None:
        """SlotEncuentroResponse can be created from model attributes."""
        data = SlotEncuentroResponse(
            id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            tenant_id="t-001",
            asignacion_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
            titulo="Clase 1",
            hora="10:00",
            dia_semana="Lunes",
            fecha_inicio="2026-03-02",
            cant_semanas=16,
            vig_desde="2026-03-01",
            estado="Activo",
            created_at="2026-03-01T00:00:00Z",
            updated_at="2026-03-01T00:00:00Z",
        )
        assert data.id == "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
        assert data.estado == "Activo"
