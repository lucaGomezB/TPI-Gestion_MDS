"""Unit tests for communication Pydantic schemas (C-11, Task 13.4).

Tests extra='forbid', field validation, and schema constraints.
"""

import pytest
from pydantic import ValidationError

from app.schemas.communication import (
    AccionAprobacion,
    AprobarRequest,
    AprobarResponse,
    ComunicacionResponse,
    EnviarRequest,
    LoteResponse,
    PreviewItem,
    PreviewRequest,
    PreviewResponse,
)


class TestPreviewRequest:
    """PreviewRequest schema — template preview validation."""

    def test_valid_request(self):
        data = PreviewRequest(asunto="Hola {{nombre}}", cuerpo="Cuerpo")
        assert data.asunto == "Hola {{nombre}}"
        assert data.cuerpo == "Cuerpo"
        assert data.alumno_ids is None

    def test_with_alumno_ids(self):
        data = PreviewRequest(
            asunto="Hola",
            cuerpo="Cuerpo",
            alumno_ids=["id1", "id2"],
        )
        assert data.alumno_ids == ["id1", "id2"]

    def test_more_than_5_alumno_ids_raises(self):
        with pytest.raises(ValidationError) as exc:
            PreviewRequest(
                asunto="Hola",
                cuerpo="Cuerpo",
                alumno_ids=["id1", "id2", "id3", "id4", "id5", "id6"],
            )
        assert "alumno_ids" in str(exc.value)

    def test_empty_asunto_raises(self):
        with pytest.raises(ValidationError):
            PreviewRequest(asunto="", cuerpo="Cuerpo")

    def test_empty_cuerpo_raises(self):
        with pytest.raises(ValidationError):
            PreviewRequest(asunto="Hola", cuerpo="")

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            PreviewRequest(asunto="Hola", cuerpo="Cuerpo", extra="x")


class TestEnviarRequest:
    """EnviarRequest — enqueue validation (RN-16)."""

    def test_valid_request(self):
        data = EnviarRequest(
            asunto="Hola",
            cuerpo="Cuerpo",
            preview_confirmado=True,
        )
        assert data.preview_confirmado is True

    def test_preview_confirmado_false(self):
        """Setting preview_confirmado=false should be allowed at schema level
        (service layer will reject it per RN-16)."""
        data = EnviarRequest(
            asunto="Hola",
            cuerpo="Cuerpo",
            preview_confirmado=False,
        )
        assert data.preview_confirmado is False

    def test_with_alumno_ids(self):
        data = EnviarRequest(
            asunto="Hola",
            cuerpo="Cuerpo",
            preview_confirmado=True,
            alumno_ids=["id1", "id2"],
        )
        assert data.alumno_ids == ["id1", "id2"]

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            EnviarRequest(
                asunto="Hola",
                cuerpo="Cuerpo",
                preview_confirmado=True,
                extra="x",
            )


class TestAprobarRequest:
    """AprobarRequest — approval decision validation."""

    def test_aprobar_valid(self):
        data = AprobarRequest(accion=AccionAprobacion.aprobar)
        assert data.accion == AccionAprobacion.aprobar
        assert data.motivo is None

    def test_rechazar_with_motivo(self):
        data = AprobarRequest(
            accion=AccionAprobacion.rechazar,
            motivo="Contenido inapropiado",
        )
        assert data.accion == AccionAprobacion.rechazar
        assert data.motivo == "Contenido inapropiado"

    def test_invalid_accion_raises(self):
        with pytest.raises(ValidationError):
            AprobarRequest(accion="invalid")

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            AprobarRequest(accion=AccionAprobacion.aprobar, extra="x")


class TestComunicacionResponse:
    """ComunicacionResponse schema."""

    def test_minimal_response(self):
        data = ComunicacionResponse(
            id="uuid",
            materia_id="mat-uuid",
            destinatario="j***@example.com",
            asunto="Hola",
            estado="Pendiente",
        )
        assert data.estado == "Pendiente"
        assert data.error_msg is None
        assert data.enviado_at is None

    def test_full_response(self):
        data = ComunicacionResponse(
            id="uuid",
            materia_id="mat-uuid",
            destinatario="j***@example.com",
            asunto="Hola",
            estado="Enviado",
            enviado_at="2026-06-08T10:00:00Z",
            error_msg=None,
        )
        assert data.estado == "Enviado"

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            ComunicacionResponse(
                id="uuid",
                materia_id="mat-uuid",
                destinatario="j***@x.com",
                asunto="Hola",
                estado="Pendiente",
                extra="x",
            )


class TestLoteResponse:
    """LoteResponse schema."""

    def test_minimal_response(self):
        data = LoteResponse(
            id="uuid",
            materia_id="mat-uuid",
            total=10,
            enviados=0,
            fallidos=0,
            estado="Pendiente",
            requiere_aprobacion=False,
            created_at="2026-06-08T10:00:00Z",
        )
        assert data.total == 10
        assert data.requiere_aprobacion is False

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            LoteResponse(
                id="uuid",
                materia_id="mat-uuid",
                total=0,
                enviados=0,
                fallidos=0,
                estado="Pendiente",
                requiere_aprobacion=False,
                created_at="2026-06-08T10:00:00Z",
                extra="x",
            )


class TestPreviewItem:
    """PreviewItem schema."""

    def test_valid_item(self):
        data = PreviewItem(
            alumno_nombre="Juan Perez",
            email_preview="j***@example.com",
            asunto_renderizado="Hola Juan",
            cuerpo_renderizado="Bienvenido",
        )
        assert data.alumno_nombre == "Juan Perez"
        assert data.email_preview == "j***@example.com"


class TestPreviewResponse:
    """PreviewResponse schema."""

    def test_empty_previews(self):
        data = PreviewResponse(previews=[])
        assert data.previews == []

    def test_one_preview(self):
        data = PreviewResponse(previews=[
            PreviewItem(
                alumno_nombre="A",
                email_preview="a***@x.com",
                asunto_renderizado="Hola",
                cuerpo_renderizado="Cuerpo",
            ),
        ])
        assert len(data.previews) == 1


class TestAprobarResponse:
    def test_response(self):
        data = AprobarResponse(
            id="uuid",
            estado="Enviando",
            mensaje="Approved",
        )
        assert data.estado == "Enviando"
