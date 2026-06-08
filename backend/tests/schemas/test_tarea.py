"""Unit tests for Tarea and ComentarioTarea Pydantic schemas (C-16).

Verifies schema field types, extra='forbid' enforcement, and validations.
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.tarea import (
    ComentarioCreate,
    ComentarioRead,
    TareaCreate,
    TareaEstadoUpdate,
    TareaFilter,
    TareaRead,
    TareaReadAdmin,
)


class TestTareaCreate:
    """TareaCreate schema validation."""

    def test_valid_create(self) -> None:
        """Valid TareaCreate passes validation."""
        data = {
            "asignado_a": str(uuid4()),
            "descripcion": "Preparar informe de avance",
        }
        schema = TareaCreate(**data)
        assert schema.asignado_a == data["asignado_a"]
        assert schema.descripcion == data["descripcion"]
        assert schema.materia_id is None

    def test_valid_create_with_materia(self) -> None:
        """TareaCreate with optional materia_id."""
        materia_id = str(uuid4())
        data = {
            "asignado_a": str(uuid4()),
            "materia_id": materia_id,
            "descripcion": "Tarea vinculada a materia",
        }
        schema = TareaCreate(**data)
        assert schema.materia_id == materia_id

    def test_extra_fields_forbidden(self) -> None:
        """TareaCreate rejects undeclared fields."""
        with pytest.raises(ValidationError) as exc:
            TareaCreate(
                asignado_a=str(uuid4()),
                descripcion="Test",
                extra_field="should fail",
            )
        assert "extra_field" in str(exc.value)

    def test_descripcion_required(self) -> None:
        """TareaCreate requires descripcion."""
        with pytest.raises(ValidationError):
            TareaCreate(asignado_a=str(uuid4()))

    def test_asignado_a_required(self) -> None:
        """TareaCreate requires asignado_a."""
        with pytest.raises(ValidationError):
            TareaCreate(descripcion="Test")


class TestTareaRead:
    """TareaRead schema validation."""

    def test_valid_read(self) -> None:
        """TareaRead with all fields."""
        data = {
            "id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "materia_id": str(uuid4()),
            "asignado_a": str(uuid4()),
            "asignado_por": str(uuid4()),
            "estado": "Pendiente",
            "descripcion": "Test tarea",
            "contexto_id": None,
            "created_at": "2026-06-01T10:00:00Z",
            "updated_at": "2026-06-01T10:00:00Z",
        }
        schema = TareaRead(**data)
        assert schema.estado == "Pendiente"

    def test_extra_forbidden(self) -> None:
        """TareaRead rejects undeclared fields."""
        with pytest.raises(ValidationError):
            TareaRead(
                id=str(uuid4()),
                tenant_id=str(uuid4()),
                asignado_a=str(uuid4()),
                asignado_por=str(uuid4()),
                estado="Pendiente",
                descripcion="Test",
                created_at="2026-06-01T10:00:00Z",
                updated_at="2026-06-01T10:00:00Z",
                unknown="bad",
            )


class TestTareaEstadoUpdate:
    """TareaEstadoUpdate schema validation."""

    def test_valid_estado(self) -> None:
        """Valid estado values pass."""
        for estado in ("Pendiente", "En progreso", "Resuelta", "Cancelada"):
            schema = TareaEstadoUpdate(estado=estado)
            assert schema.estado == estado

    def test_invalid_estado_fails(self) -> None:
        """Invalid estado value raises error."""
        with pytest.raises(ValidationError):
            TareaEstadoUpdate(estado="InvalidState")

    def test_extra_forbidden(self) -> None:
        """TareaEstadoUpdate rejects undeclared fields."""
        with pytest.raises(ValidationError):
            TareaEstadoUpdate(estado="Pendiente", extra="bad")


class TestTareaFilter:
    """TareaFilter query params schema."""

    def test_empty_filter(self) -> None:
        """Empty TareaFilter is valid."""
        schema = TareaFilter()
        assert schema.estado is None
        assert schema.materia_id is None

    def test_with_filters(self) -> None:
        """TareaFilter with all optional fields."""
        data = {
            "estado": "Pendiente",
            "materia_id": str(uuid4()),
            "asignado_a": str(uuid4()),
            "asignado_por": str(uuid4()),
            "q": "informe",
        }
        schema = TareaFilter(**data)
        assert schema.estado == "Pendiente"
        assert schema.q == "informe"

    def test_extra_forbidden(self) -> None:
        """TareaFilter rejects undeclared fields."""
        with pytest.raises(ValidationError):
            TareaFilter(extra="bad")


class TestComentarioCreate:
    """ComentarioCreate schema validation."""

    def test_valid(self) -> None:
        """Valid ComentarioCreate passes."""
        schema = ComentarioCreate(texto="Esto es un comentario")
        assert schema.texto == "Esto es un comentario"

    def test_texto_required(self) -> None:
        """ComentarioCreate requires texto."""
        with pytest.raises(ValidationError):
            ComentarioCreate()

    def test_extra_forbidden(self) -> None:
        """ComentarioCreate rejects undeclared fields."""
        with pytest.raises(ValidationError):
            ComentarioCreate(texto="Hola", extra="bad")


class TestComentarioRead:
    """ComentarioRead schema validation."""

    def test_valid(self) -> None:
        """Valid ComentarioRead passes."""
        data = {
            "id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "tarea_id": str(uuid4()),
            "autor_id": str(uuid4()),
            "texto": "Comentario de prueba",
            "created_at": "2026-06-01T10:00:00Z",
        }
        schema = ComentarioRead(**data)
        assert schema.texto == "Comentario de prueba"

    def test_extra_forbidden(self) -> None:
        """ComentarioRead rejects undeclared fields."""
        with pytest.raises(ValidationError):
            ComentarioRead(
                id=str(uuid4()),
                tenant_id=str(uuid4()),
                tarea_id=str(uuid4()),
                autor_id=str(uuid4()),
                texto="Hola",
                creado_at="2026-06-01T10:00:00Z",
                extra="bad",
            )
