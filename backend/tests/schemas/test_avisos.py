"""Unit tests for avisos Pydantic schemas (C-12, Task 5.1).

Tests extra='forbid', alcance-contexto validation, vigencia validation.
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.schemas.aviso import (
    AckResponse,
    AlcanceAviso,
    AvisoCreate,
    AvisoListResponse,
    AvisoResponse,
    AvisoUpdate,
    SeveridadAviso,
)


class TestAvisoCreate:
    """AvisoCreate schema — admin creates a new aviso."""

    def test_valid_minimal(self):
        data = AvisoCreate(
            titulo="Aviso importante",
            cuerpo="Contenido del aviso",
            alcance=AlcanceAviso.GLOBAL,
            severidad=SeveridadAviso.MEDIA,
            inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
            orden=1,
        )
        assert data.titulo == "Aviso importante"
        assert data.alcance == AlcanceAviso.GLOBAL
        assert data.activo is True

    def test_valid_with_requiere_ack(self):
        data = AvisoCreate(
            titulo="Aviso con ack",
            cuerpo="Requiere confirmacion",
            alcance=AlcanceAviso.GLOBAL,
            severidad=SeveridadAviso.ALTA,
            inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
            orden=2,
            requiere_ack=True,
        )
        assert data.requiere_ack is True

    def test_por_materia_requires_materia_id(self):
        with pytest.raises(ValidationError) as exc:
            AvisoCreate(
                titulo="Test",
                cuerpo="Test",
                alcance=AlcanceAviso.POR_MATERIA,
                severidad=SeveridadAviso.MEDIA,
                inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
                fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
                orden=1,
            )
        err = str(exc.value)
        assert "materia_id" in err and "requerido" in err.lower()

    def test_por_cohorte_requires_cohorte_id(self):
        with pytest.raises(ValidationError) as exc:
            AvisoCreate(
                titulo="Test",
                cuerpo="Test",
                alcance=AlcanceAviso.POR_COHORTE,
                severidad=SeveridadAviso.MEDIA,
                inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
                fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
                orden=1,
            )
        err = str(exc.value)
        assert "cohorte_id" in err and "requerido" in err.lower()

    def test_por_rol_requires_rol_destino(self):
        with pytest.raises(ValidationError) as exc:
            AvisoCreate(
                titulo="Test",
                cuerpo="Test",
                alcance=AlcanceAviso.POR_ROL,
                severidad=SeveridadAviso.MEDIA,
                inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
                fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
                orden=1,
            )
        err = str(exc.value)
        assert "rol_destino" in err and "requerido" in err.lower()

    def test_vigencia_inicio_before_fin(self):
        with pytest.raises(ValidationError) as exc:
            AvisoCreate(
                titulo="Test",
                cuerpo="Test",
                alcance=AlcanceAviso.GLOBAL,
                severidad=SeveridadAviso.MEDIA,
                inicio_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
                fin_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
                orden=1,
            )
        err = str(exc.value)
        assert "inicio_en" in err.lower() and "fin_en" in err.lower()

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            AvisoCreate(
                titulo="Test",
                cuerpo="Test",
                alcance=AlcanceAviso.GLOBAL,
                severidad=SeveridadAviso.MEDIA,
                inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
                fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
                orden=1,
                extra="x",
            )

    def test_global_ignores_context_fields(self):
        """Global alcance should accept null context fields."""
        data = AvisoCreate(
            titulo="Global",
            cuerpo="Test",
            alcance=AlcanceAviso.GLOBAL,
            severidad=SeveridadAviso.MEDIA,
            inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
            orden=1,
            materia_id=None,
            cohorte_id=None,
            rol_destino=None,
        )
        assert data.alcance == AlcanceAviso.GLOBAL

    def test_valid_por_materia_with_context(self):
        data = AvisoCreate(
            titulo="Por materia",
            cuerpo="Test",
            alcance=AlcanceAviso.POR_MATERIA,
            severidad=SeveridadAviso.MEDIA,
            inicio_en=datetime(2026, 1, 1, tzinfo=timezone.utc),
            fin_en=datetime(2026, 12, 31, tzinfo=timezone.utc),
            orden=1,
            materia_id="mat-uuid",
        )
        assert data.materia_id == "mat-uuid"


class TestAvisoUpdate:
    """AvisoUpdate schema — partial update fields."""

    def test_empty_update(self):
        data = AvisoUpdate()
        assert data.model_dump(exclude_unset=True) == {}

    def test_partial_update(self):
        data = AvisoUpdate(titulo="Nuevo titulo")
        assert data.titulo == "Nuevo titulo"
        assert data.cuerpo is None

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            AvisoUpdate(titulo="Test", extra="x")

    def test_update_activo(self):
        data = AvisoUpdate(activo=False)
        assert data.activo is False


class TestAvisoResponse:
    """AvisoResponse schema — response model with from_attributes."""

    def test_minimal_response(self):
        now = datetime.now(timezone.utc)
        data = AvisoResponse(
            id="uuid-1",
            tenant_id="tenant-a",
            titulo="Test",
            cuerpo="Body",
            alcance=AlcanceAviso.GLOBAL,
            severidad=SeveridadAviso.MEDIA,
            inicio_en=now,
            fin_en=now + timedelta(days=30),
            orden=1,
            activo=True,
            requiere_ack=False,
            created_at=now,
            updated_at=now,
        )
        assert data.id == "uuid-1"
        assert data.activo is True

    def test_extra_field_forbidden(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            AvisoResponse(
                id="uuid-1",
                tenant_id="tenant-a",
                titulo="Test",
                cuerpo="Body",
                alcance=AlcanceAviso.GLOBAL,
                severidad=SeveridadAviso.MEDIA,
                inicio_en=now,
                fin_en=now + timedelta(days=30),
                orden=1,
                activo=True,
                requiere_ack=False,
                created_at=now,
                updated_at=now,
                extra="x",
            )


class TestAvisoListResponse:
    """AvisoListResponse — paginated list response."""

    def test_empty_list(self):
        data = AvisoListResponse(items=[], total=0)
        assert data.items == []
        assert data.total == 0

    def test_with_items(self):
        now = datetime.now(timezone.utc)
        item = AvisoResponse(
            id="uuid-1",
            tenant_id="tenant-a",
            titulo="Test",
            cuerpo="Body",
            alcance=AlcanceAviso.GLOBAL,
            severidad=SeveridadAviso.MEDIA,
            inicio_en=now,
            fin_en=now + timedelta(days=30),
            orden=1,
            activo=True,
            requiere_ack=False,
            created_at=now,
            updated_at=now,
        )
        data = AvisoListResponse(items=[item], total=1)
        assert len(data.items) == 1
        assert data.total == 1


class TestAckResponse:
    """AckResponse schema — acknowledgment confirmation."""

    def test_valid_response(self):
        now = datetime.now(timezone.utc)
        data = AckResponse(acknowledged=True, leido_en=now)
        assert data.acknowledged is True
        assert data.leido_en == now

    def test_extra_field_forbidden(self):
        now = datetime.now(timezone.utc)
        with pytest.raises(ValidationError):
            AckResponse(acknowledged=True, leido_en=now, extra="x")


class TestEnums:
    """AlcanceAviso and SeveridadAviso enums."""

    def test_alcance_values(self):
        assert AlcanceAviso.GLOBAL == "Global"
        assert AlcanceAviso.POR_MATERIA == "PorMateria"
        assert AlcanceAviso.POR_COHORTE == "PorCohorte"
        assert AlcanceAviso.POR_ROL == "PorRol"

    def test_severidad_values(self):
        assert SeveridadAviso.BAJA == "Baja"
        assert SeveridadAviso.MEDIA == "Media"
        assert SeveridadAviso.ALTA == "Alta"
        assert SeveridadAviso.CRITICO == "Critico"
