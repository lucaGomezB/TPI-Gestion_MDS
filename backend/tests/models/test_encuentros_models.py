"""Unit tests for encuentro and guardia SQLAlchemy models (C-14).

Verifies model instantiation, field types, and relationships.
"""

from datetime import date, time
from uuid import uuid4

import pytest

from app.models.guardia import Guardia
from app.models.instancia_encuentro import InstanciaEncuentro
from app.models.mixins import EstadoRegistro
from app.models.slot_encuentro import SlotEncuentro


class TestSlotEncuentroModel:
    """Task 1.1: SlotEncuentro model definition."""

    def test_create_instance(self) -> None:
        """SlotEncuentro can be instantiated with minimum fields."""
        instance = SlotEncuentro(
            tenant_id=str(uuid4()),
            asignacion_id=str(uuid4()),
            materia_id=str(uuid4()),
            titulo="Clase Semanal",
            hora=time(10, 0),
            dia_semana="Lunes",
            fecha_inicio=date(2026, 3, 2),
            cant_semanas=16,
            vig_desde=date(2026, 3, 1),
        )
        assert instance.titulo == "Clase Semanal"
        assert instance.cant_semanas == 16
        assert instance.dia_semana == "Lunes"
        assert instance.fecha_unica is None
        assert instance.meet_url is None
        assert instance.estado == EstadoRegistro.ACTIVO

    def test_fecha_unica_instance(self) -> None:
        """SlotEncuentro with fecha_unica has cant_semanas=0."""
        instance = SlotEncuentro(
            tenant_id=str(uuid4()),
            asignacion_id=str(uuid4()),
            materia_id=str(uuid4()),
            titulo="Extraordinaria",
            hora=time(14, 0),
            dia_semana="Miercoles",
            fecha_inicio=date(2026, 6, 1),
            cant_semanas=0,
            fecha_unica=date(2026, 6, 15),
            vig_desde=date(2026, 6, 1),
        )
        assert instance.cant_semanas == 0
        assert instance.fecha_unica == date(2026, 6, 15)

    def test_table_name(self) -> None:
        """SlotEncuentro uses correct table name."""
        assert SlotEncuentro.__tablename__ == "slots_encuentro"

    def test_has_audit_mixin(self) -> None:
        """SlotEncuentro includes AuditMixin fields."""
        assert hasattr(SlotEncuentro, "estado")
        assert hasattr(SlotEncuentro, "deleted_at")


class TestInstanciaEncuentroModel:
    """Task 1.2: InstanciaEncuentro model definition."""

    def test_create_instance(self) -> None:
        """InstanciaEncuentro can be instantiated with minimum fields."""
        instance = InstanciaEncuentro(
            tenant_id=str(uuid4()),
            materia_id=str(uuid4()),
            fecha=date(2026, 3, 9),
            hora=time(10, 0),
            titulo="Clase Semanal 1",
        )
        assert instance.titulo == "Clase Semanal 1"
        assert instance.estado == "Programado"
        assert instance.slot_id is None
        assert instance.meet_url is None
        assert instance.video_url is None
        assert instance.comentario is None

    def test_create_with_slot(self) -> None:
        """InstanciaEncuentro can reference a slot."""
        instance = InstanciaEncuentro(
            tenant_id=str(uuid4()),
            slot_id=str(uuid4()),
            materia_id=str(uuid4()),
            fecha=date(2026, 3, 9),
            hora=time(10, 0),
            titulo="Clase Semanal 1",
        )
        assert instance.slot_id is not None

    def test_table_name(self) -> None:
        """InstanciaEncuentro uses correct table name."""
        assert InstanciaEncuentro.__tablename__ == "instancias_encuentro"


class TestGuardiaModel:
    """Task 1.3: Guardia model definition."""

    def test_create_instance(self) -> None:
        """Guardia can be instantiated with minimum fields."""
        instance = Guardia(
            tenant_id=str(uuid4()),
            asignacion_id=str(uuid4()),
            materia_id=str(uuid4()),
            carrera_id=str(uuid4()),
            cohorte_id=str(uuid4()),
            dia="Lunes",
            horario="14:00-16:00",
        )
        assert instance.dia == "Lunes"
        assert instance.horario == "14:00-16:00"
        assert instance.estado == "Pendiente"
        assert instance.comentarios is None

    def test_table_name(self) -> None:
        """Guardia uses correct table name."""
        assert Guardia.__tablename__ == "guardias"

    def test_no_audit_mixin(self) -> None:
        """Guardia does NOT include AuditMixin (own estado field)."""
        assert not hasattr(Guardia, "deleted_at")
