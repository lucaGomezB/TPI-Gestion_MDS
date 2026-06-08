"""Tests for manual import parser with sample xlsx/csv files.

Tests cover:
- Valid grade file with (Real) columns (csv)
- File with no (Real) columns -> error
- File with textual scale values
- Corrupt file -> parse error
"""

import os

import pytest

os.environ["SECRET_KEY"] = "a" * 32
os.environ["ENCRYPTION_KEY"] = "b" * 32

from app.schemas.manual_import import PreviewResult  # noqa: E402
from app.services.manual_import_service import manual_import_service  # noqa: E402


SAMPLE_DICTADO_ID = "00000000-0000-4000-8000-000000000001"
TEST_TENANT_ID = "00000000-0000-4000-8000-000000000002"


@pytest.mark.asyncio
async def test_valid_csv_with_real_columns() -> None:
    """Test parsing a valid CSV with (Real) grade columns."""
    csv_content = (
        "Apellido,Nombre,DNI,Trabajo Practico 1 (Real),Examen Parcial (Real)\r\n"
        "Perez,Juan,12345678,85,90\r\n"
        "Gomez,Maria,23456789,92,88\r\n"
        "Lopez,Carlos,34567890,78,95\r\n"
    )

    preview = await manual_import_service.parse_and_preview(
        filename="notas.csv",
        file_content=csv_content.encode("utf-8"),
        dictado_id=SAMPLE_DICTADO_ID,
    )

    assert isinstance(preview, PreviewResult)
    assert len(preview.activities) == 2
    assert preview.activities[0].name == "Trabajo Practico 1"
    assert preview.activities[0].scale_type == "numeric"
    assert preview.activities[1].name == "Examen Parcial"
    assert preview.students_count == 3
    assert len(preview.sample_students) > 0
    assert preview.filename == "notas.csv"


@pytest.mark.asyncio
async def test_csv_without_real_columns_raises_error() -> None:
    """Test that a file with no (Real) columns raises an error."""
    csv_content = (
        "Apellido,Nombre,DNI,Nota Final,Comentario\r\n"
        "Perez,Juan,12345678,85,Muy bien\r\n"
    )

    with pytest.raises(ValueError, match="No grade columns found"):
        await manual_import_service.parse_and_preview(
            filename="notas.csv",
            file_content=csv_content.encode("utf-8"),
            dictado_id=SAMPLE_DICTADO_ID,
        )


@pytest.mark.asyncio
async def test_csv_with_textual_scale_values() -> None:
    """Test parsing CSV with textual scale values."""
    csv_content = (
        "Apellido,Nombre,DNI,TP 1 (Real),TP 2 (Real)\r\n"
        "Perez,Juan,12345678,Satisfactorio,Muy bueno\r\n"
        "Gomez,Maria,23456789,No satisfactorio,Excelente\r\n"
    )

    preview = await manual_import_service.parse_and_preview(
        filename="notas.csv",
        file_content=csv_content.encode("utf-8"),
        dictado_id=SAMPLE_DICTADO_ID,
    )

    assert len(preview.activities) == 2
    assert preview.activities[0].scale_type == "textual"
    assert "Satisfactorio" in preview.activities[0].detected_values
    assert "No satisfactorio" in preview.activities[0].detected_values


@pytest.mark.asyncio
async def test_corrupt_file_raises_error() -> None:
    """Test that a corrupt/binary file raises a parse error."""
    with pytest.raises(ValueError, match="Could not parse"):
        await manual_import_service.parse_and_preview(
            filename="notas.xlsx",
            file_content=b"\x00\x01\x02\xff\xfe\xfd corrupt binary",
            dictado_id=SAMPLE_DICTADO_ID,
        )


@pytest.mark.asyncio
async def test_unsupported_format() -> None:
    """Test that an unsupported format raises an error."""
    with pytest.raises(ValueError, match="Unsupported file format"):
        await manual_import_service.parse_and_preview(
            filename="notas.pdf",
            file_content=b"%PDF-1.4 fake pdf",
            dictado_id=SAMPLE_DICTADO_ID,
        )


@pytest.mark.asyncio
async def test_csv_semicolon_separator() -> None:
    """Test parsing a semicolon-separated CSV."""
    csv_content = (
        "Apellido;Nombre;DNI;TP 1 (Real);Examen (Real)\r\n"
        "Perez;Juan;12345678;85;90\r\n"
    )

    preview = await manual_import_service.parse_and_preview(
        filename="notas.csv",
        file_content=csv_content.encode("utf-8-sig"),
        dictado_id=SAMPLE_DICTADO_ID,
    )

    assert len(preview.activities) == 2
    assert preview.students_count == 1


@pytest.mark.asyncio
async def test_confirm_import_without_activities_raises() -> None:
    """Test that confirming with empty activity_ids raises error."""
    from app.schemas.manual_import import ImportConfirmRequest

    # First create a preview session
    csv_content = (
        "Nombre,DNI,Actividad (Real)\r\n"
        "Juan Perez,12345678,85\r\n"
    )

    preview = await manual_import_service.parse_and_preview(
        filename="notas.csv",
        file_content=csv_content.encode("utf-8"),
        dictado_id=SAMPLE_DICTADO_ID,
    )

    request = ImportConfirmRequest(
        session_token=preview.session_token,
        activity_ids=[],
    )

    with pytest.raises(ValueError, match="(?i)at least one activity"):
        from unittest.mock import AsyncMock

        mock_db = AsyncMock()
        await manual_import_service.confirm_import(
            request=request,
            db=mock_db,
            tenant_id=TEST_TENANT_ID,
        )


@pytest.mark.asyncio
async def test_confirm_import_success() -> None:
    """Test that confirming an import returns expected counts."""
    from app.schemas.manual_import import ImportConfirmRequest

    csv_content = (
        "Nombre,DNI,TP 1 (Real),TP 2 (Real)\r\n"
        "Juan Perez,12345678,85,90\r\n"
        "Maria Gomez,23456789,92,88\r\n"
    )

    preview = await manual_import_service.parse_and_preview(
        filename="notas.csv",
        file_content=csv_content.encode("utf-8"),
        dictado_id=SAMPLE_DICTADO_ID,
    )

    request = ImportConfirmRequest(
        session_token=preview.session_token,
        activity_ids=["TP 1", "TP 2"],
    )

    from unittest.mock import AsyncMock

    mock_db = AsyncMock()
    result = await manual_import_service.confirm_import(
        request=request,
        db=mock_db,
        tenant_id=TEST_TENANT_ID,
    )

    assert result.status == "completed"
    assert result.activities_imported == 2
    assert result.grades_imported == 4  # 2 activities * 2 students
    assert result.students_enrolled == 2


@pytest.mark.asyncio
async def test_expired_session_raises() -> None:
    """Test that an invalid/expired session raises error."""
    from app.schemas.manual_import import ImportConfirmRequest
    from unittest.mock import AsyncMock

    request = ImportConfirmRequest(
        session_token="nonexistent-session-token",
        activity_ids=["TP 1"],
    )

    with pytest.raises(ValueError, match="not found or has expired"):
        mock_db = AsyncMock()
        await manual_import_service.confirm_import(
            request=request,
            db=mock_db,
            tenant_id=TEST_TENANT_ID,
        )
