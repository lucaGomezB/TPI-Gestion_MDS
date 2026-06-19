"""Unit tests for Tarea and ComentarioTarea SQLAlchemy models (C-16).

Verifies model instantiation, field types, table names, and relationships.
"""

from uuid import uuid4

import pytest

from app.models.tarea import ComentarioTarea, EstadoTarea, Tarea
from app.models.mixins import TimestampMixin, TenantMixin


class TestEstadoTareaEnum:
    """EstadoTarea enum values."""

    def test_enum_values(self) -> None:
        """EstadoTarea has the four expected states."""
        assert EstadoTarea.PENDIENTE.value == "Pendiente"
        assert EstadoTarea.EN_PROGRESO.value == "En progreso"
        assert EstadoTarea.RESUELTA.value == "Resuelta"
        assert EstadoTarea.CANCELADA.value == "Cancelada"

    def test_enum_is_str_enum(self) -> None:
        """EstadoTarea inherits from str, Enum."""
        assert issubclass(EstadoTarea, str)


class TestTareaModel:
    """Task 1.1: Tarea model definition."""

    def test_create_instance_minimal(self) -> None:
        """Tarea can be instantiated with minimum required fields."""
        tarea = Tarea(
            tenant_id=str(uuid4()),
            asignado_a=str(uuid4()),
            asignado_por=str(uuid4()),
            descripcion="Preparar informe de avance",
        )
        assert tarea.descripcion == "Preparar informe de avance"
        assert tarea.estado == EstadoTarea.PENDIENTE
        assert tarea.materia_id is None
        assert tarea.contexto_id is None
        assert tarea.id is not None

    def test_create_instance_with_all_fields(self) -> None:
        """Tarea can be instantiated with all fields."""
        materia_id = str(uuid4())
        asignado_a = str(uuid4())
        asignado_por = str(uuid4())
        contexto_id = str(uuid4())
        tarea = Tarea(
            tenant_id=str(uuid4()),
            materia_id=materia_id,
            asignado_a=asignado_a,
            asignado_por=asignado_por,
            estado=EstadoTarea.EN_PROGRESO,
            descripcion="Revisar planificacion",
            contexto_id=contexto_id,
        )
        assert tarea.materia_id == materia_id
        assert tarea.asignado_a == asignado_a
        assert tarea.asignado_por == asignado_por
        assert tarea.estado == EstadoTarea.EN_PROGRESO
        assert tarea.contexto_id == contexto_id

    def test_table_name(self) -> None:
        """Tarea uses correct table name."""
        assert Tarea.__tablename__ == "tareas"

    def test_has_timestamp_mixin(self) -> None:
        """Tarea includes TimestampMixin fields."""
        assert hasattr(Tarea, "created_at")
        assert hasattr(Tarea, "updated_at")

    def test_has_tenant_mixin(self) -> None:
        """Tarea includes TenantMixin fields."""
        assert hasattr(Tarea, "tenant_id")


class TestComentarioTareaModel:
    """Task 1.1: ComentarioTarea model definition."""

    def test_create_instance(self) -> None:
        """ComentarioTarea can be instantiated with minimum fields."""
        comentario = ComentarioTarea(
            tenant_id=str(uuid4()),
            tarea_id=str(uuid4()),
            autor_id=str(uuid4()),
            texto="Ya lo estoy revisando",
        )
        assert comentario.texto == "Ya lo estoy revisando"
        assert comentario.id is not None
        # created_at is server_default — populated only after DB flush

    def test_table_name(self) -> None:
        """ComentarioTarea uses correct table name."""
        assert ComentarioTarea.__tablename__ == "comentarios_tarea"

    def test_has_timestamp_mixin(self) -> None:
        """ComentarioTarea includes TimestampMixin fields."""
        assert hasattr(ComentarioTarea, "created_at")

    def test_has_tenant_mixin(self) -> None:
        """ComentarioTarea includes TenantMixin fields with tenant_id."""
        assert hasattr(ComentarioTarea, "tenant_id")


class TestTareaRelationships:
    """Tarea relationship attributes."""

    def test_has_tenant_relationship(self) -> None:
        """Tarea has tenant relationship."""
        assert hasattr(Tarea, "tenant")

    def test_has_materia_relationship(self) -> None:
        """Tarea has materia relationship."""
        assert hasattr(Tarea, "materia")

    def test_has_asignado_a_relationship(self) -> None:
        """Tarea has asignado_a relationship to Usuario."""
        assert hasattr(Tarea, "asignado_a_usuario")

    def test_has_asignado_por_relationship(self) -> None:
        """Tarea has asignado_por relationship to Usuario."""
        assert hasattr(Tarea, "asignado_por_usuario")

    def test_has_comentarios_relationship(self) -> None:
        """Tarea has comentarios relationship to ComentarioTarea."""
        assert hasattr(Tarea, "comentarios")


class TestComentarioTareaRelationships:
    """ComentarioTarea relationship attributes."""

    def test_has_tarea_relationship(self) -> None:
        """ComentarioTarea has tarea relationship."""
        assert hasattr(ComentarioTarea, "tarea")

    def test_has_autor_relationship(self) -> None:
        """ComentarioTarea has autor relationship to Usuario."""
        assert hasattr(ComentarioTarea, "autor")
