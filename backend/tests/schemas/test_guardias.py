"""Schema unit tests for Guardia Pydantic models (C-14).

Verifies extra='forbid', field validation, and serialization.
"""

import pytest
from pydantic import ValidationError

from app.schemas.guardias import GuardiaCreate, GuardiaResponse


class TestGuardiaCreate:
    """Task 5.2: GuardiaCreate schema validation."""

    def test_valid_guardia(self) -> None:
        """Happy path: valid guardia creation data."""
        data = GuardiaCreate(
            asignacion_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
            carrera_id="c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
            cohorte_id="d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a",
            dia="Lunes",
            horario="14:00-16:00",
        )
        assert data.dia == "Lunes"
        assert data.horario == "14:00-16:00"
        assert data.estado is None  # defaults server-side

    def test_valid_guardia_with_estado(self) -> None:
        """Guardia with explicit estado."""
        data = GuardiaCreate(
            asignacion_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
            carrera_id="c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
            cohorte_id="d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a",
            dia="Martes",
            horario="10:00-12:00",
            estado="Pendiente",
            comentarios="Atencion general",
        )
        assert data.estado == "Pendiente"
        assert data.comentarios == "Atencion general"

    def test_invalid_estado(self) -> None:
        """Invalid estado value is rejected."""
        with pytest.raises(ValidationError):
            GuardiaCreate(
                asignacion_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
                materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
                carrera_id="c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
                cohorte_id="d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a",
                dia="Lunes",
                horario="14:00",
                estado="Invalido",
            )

    def test_extra_forbid(self) -> None:
        """Unknown fields are rejected."""
        with pytest.raises(ValidationError):
            GuardiaCreate(
                asignacion_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
                materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
                carrera_id="c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
                cohorte_id="d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a",
                dia="Lunes",
                horario="14:00",
                extra_field="rejected",
            )


class TestGuardiaResponse:
    """Task 5.2: GuardiaResponse from_attributes."""

    def test_serialize_from_model(self) -> None:
        """GuardiaResponse can be created from model attributes."""
        data = GuardiaResponse(
            id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            tenant_id="t-001",
            asignacion_id="a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
            materia_id="b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e",
            carrera_id="c3d4e5f6-a7b8-4c9d-0e1f-2a3b4c5d6e7f",
            cohorte_id="d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a",
            dia="Lunes",
            horario="14:00-16:00",
            estado="Pendiente",
            creada_at="2026-03-01T00:00:00Z",
            created_at="2026-03-01T00:00:00Z",
            updated_at="2026-03-01T00:00:00Z",
        )
        assert data.estado == "Pendiente"
        assert data.dia == "Lunes"
