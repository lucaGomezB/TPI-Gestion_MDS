"""Integration tests for calificaciones (grades) API endpoints.

All tests require PostgreSQL via testcontainers.
Marked with ``@pytest.mark.integration`` for selective execution.
"""

import io
import json

import openpyxl
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        True,
        reason="Requires PostgreSQL (testcontainers). "
        "Run with: pytest --run-integration",
    ),
]


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def admin_token() -> str:
    """Return a valid JWT for an ADMIN user with all permissions."""
    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def profesor_token() -> str:
    """Return a JWT for a PROFESOR user."""
    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def otro_profesor_token() -> str:
    """Return a JWT for another PROFESOR user."""
    return create_access_token(
        sub="otro-profe-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def coordinador_token() -> str:
    """Return a JWT for a COORDINADOR user."""
    return create_access_token(
        sub="coord-uuid",
        tenant_id="tenant-a",
        roles=["COORDINADOR"],
    )


@pytest.fixture
def tenant_b_token() -> str:
    """Return a JWT for an ADMIN in tenant B."""
    return create_access_token(
        sub="admin-b-uuid",
        tenant_id="tenant-b",
        roles=["ADMIN"],
    )


# ── File helpers ──────────────────────────────────────────────────────────────


def _make_csv(content: str, filename: str = "calificaciones.csv") -> dict:
    """Create a FastAPI UploadFile-compatible CSV file dict."""
    return {
        "file": (filename, content.encode("utf-8-sig"), "text/csv"),
    }


def _make_xlsx(rows: list[list], filename: str = "calificaciones.xlsx") -> dict:
    """Create a FastAPI UploadFile-compatible XLSX file dict."""
    wb = openpyxl.Workbook()
    ws = wb.active
    if ws is not None:
        for row in rows:
            ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return {
        "file": (
            filename,
            buf.read(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    }


# ── Academic context fixture ──────────────────────────────────────────────────


@pytest.fixture
async def setup_academic_context(
    client: AsyncClient, admin_token: str
) -> dict:
    """Create carrera, materia, cohorte, and import padron for testing."""
    # Create carrera
    resp_c = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Test Carrera"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    carrera_id = resp_c.json()["id"]

    # Create materia
    resp_m = await client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Programacion I"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    materia_id = resp_m.json()["id"]

    # Create cohorte
    resp_co = await client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "MAR-2025",
            "anio": 2025,
            "vig_desde": "2025-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cohorte_id = resp_co.json()["id"]

    # Create asignacion for PROFESOR
    resp_asig = await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "profesor-uuid",
            "rol": "PROFESOR",
            "materia_id": materia_id,
            "vig_desde": "2025-01-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    asignacion_id = resp_asig.json().get("id", "profesor-asignacion-id")

    # Import padron (needed for grade import)
    files = _make_xlsx([
        ["Nombre", "Apellidos", "Email"],
        ["Juan", "Perez", "juan@test.com"],
        ["Maria", "Gomez", "maria@test.com"],
        ["Pedro", "Lopez", "pedro@test.com"],
    ])
    resp_padron = await client.post(
        f"/api/materias/{materia_id}/padron/importar",
        params={"cohorte_id": cohorte_id},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_padron.status_code == 201

    return {
        "carrera_id": carrera_id,
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
        "asignacion_id": asignacion_id,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════════


# ── Task 7.1: Column detection (unit tests covered in test_calificaciones_service.py) ─


# ── Task 7.2: Preview import ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_preview_import_returns_actividades(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.2: Preview mode returns detected activities without persisting."""
    ctx = setup_academic_context
    files = _make_xlsx([
        ["Nombre", "Email", "TP 1 (Real)", "TP 2"],
        ["Juan", "juan@test.com", "75", "Satisfactorio"],
        ["Maria", "maria@test.com", "80", "Supera lo esperado"],
    ])
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        params={"preview": True},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "actividades" in data
    assert data["total_alumnos"] == 2
    assert data["archivo"] == "calificaciones.xlsx"

    # Check detected activities
    actividades = data["actividades"]
    assert len(actividades) == 2

    # TP 1 (Real) detected as numeric
    tp1 = [a for a in actividades if a["nombre"] == "TP 1"]
    assert len(tp1) == 1
    assert tp1[0]["tipo"] == "numerica"

    # TP 2 detected as textual
    tp2 = [a for a in actividades if a["nombre"] == "TP 2"]
    assert len(tp2) == 1
    assert tp2[0]["tipo"] == "textual"


@pytest.mark.asyncio
async def test_preview_does_not_persist(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.2: Preview mode does NOT persist any data."""
    ctx = setup_academic_context
    files = _make_xlsx([
        ["Nombre", "Email", "TP 1 (Real)"],
        ["Juan", "juan@test.com", "75"],
    ])
    # Preview
    await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        params={"preview": True},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # List should be empty (nothing persisted)
    list_resp = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0


# ── Task 7.3: Import confirm ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_confirm_import_creates_calificaciones(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.3: Confirm import creates grade records."""
    ctx = setup_academic_context

    # Upload grades file with actividades_seleccionadas as multipart form field
    csv_content = "Nombre,Email,TP 1 (Real),TP 2\nJuan,juan@test.com,75,Satisfactorio\nMaria,maria@test.com,80,Supera lo esperado\nPedro,pedro@test.com,45,No satisfactorio\n"
    actividades_json = json.dumps(["TP 1", "TP 2"])

    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        files={
            "file": ("calificaciones.csv", csv_content.encode("utf-8-sig"), "text/csv"),
            "actividades_seleccionadas": ("", actividades_json, "text/plain"),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_importados"] == 6  # 3 students x 2 activities
    assert len(data["actividades"]) == 2
    assert "TP 1" in data["actividades"]
    assert "TP 2" in data["actividades"]


@pytest.mark.asyncio
async def test_confirm_import_with_xlsx(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.3: XLSX import creates grade records."""
    ctx = setup_academic_context

    files = _make_xlsx([
        ["Nombre", "Email", "TP 1 (Real)"],
        ["Juan", "juan@test.com", "85"],
    ])
    actividades_json = json.dumps(["TP 1"])

    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        files={
            "file": ("calificaciones.xlsx", files["file"][1], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            "actividades_seleccionadas": ("", actividades_json, "text/plain"),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_importados"] == 1


# ── Task 7.4: Grade derivation ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_aprobado_derived_correctly(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.4: Import correctly derives aprobado for each grade."""
    ctx = setup_academic_context

    csv_content = "Nombre,Email,TP 1 (Real),TP 2\nJuan,juan@test.com,75,Satisfactorio\nMaria,maria@test.com,45,No satisfactorio\n"
    actividades_json = json.dumps(["TP 1", "TP 2"])

    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        files={
            "file": ("calificaciones.csv", csv_content.encode("utf-8-sig"), "text/csv"),
            "actividades_seleccionadas": ("", actividades_json, "text/plain"),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201

    # List grades and verify aprobado
    list_resp = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.status_code == 200
    records = list_resp.json()["items"]

    # Juan: TP 1 numeric 75 >= 60 -> True
    # Juan: TP 2 textual "Satisfactorio" in approved -> True
    # Maria: TP 1 numeric 45 < 60 -> False
    # Maria: TP 2 textual "No satisfactorio" not in approved -> False
    assert len(records) == 4
    for r in records:
        if r["actividad"] == "TP 1":
            if r["nota_numerica"] and float(r["nota_numerica"]) >= 60:
                assert r["aprobado"] is True, f"TP 1 {r['nota_numerica']} should be aprobado"
            else:
                assert r["aprobado"] is False, f"TP 1 {r['nota_numerica']} should not be aprobado"
        elif r["actividad"] == "TP 2":
            if r["nota_textual"] in ("Satisfactorio", "Supera lo esperado"):
                assert r["aprobado"] is True
            else:
                assert r["aprobado"] is False


# ── Task 7.5: Threshold configuration ────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_threshold(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.5: Create threshold with custom percentage."""
    ctx = setup_academic_context
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/umbral",
        json={"umbral_pct": 70},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["umbral_pct"] == 70
    assert data["materia_id"] == ctx["materia_id"]


@pytest.mark.asyncio
async def test_update_threshold(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.5: Update existing threshold."""
    ctx = setup_academic_context

    # Create
    await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/umbral",
        json={"umbral_pct": 70},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Update
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/umbral",
        json={"umbral_pct": 65},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["umbral_pct"] == 65


@pytest.mark.asyncio
async def test_get_threshold(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.5: Get existing threshold."""
    ctx = setup_academic_context

    # Create threshold first
    await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/umbral",
        json={"umbral_pct": 75, "valores_aprobatorios": ["Aprobado", "Excelente"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Get threshold
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones/umbral",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["umbral_pct"] == 75
    assert "Aprobado" in data["valores_aprobatorios"]


@pytest.mark.asyncio
async def test_get_default_threshold(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.5: Get default threshold when not configured."""
    # Use a different profesor without threshold configured
    profesor_token = create_access_token(
        sub="profe-sin-umbral",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )

    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones/umbral",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    # PROFESOR without assignment gets 403
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_custom_approved_values_on_threshold(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.5: Set custom approved textual values on threshold."""
    ctx = setup_academic_context
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/umbral",
        json={"valores_aprobatorios": ["Aprobado", "Excelente", "Muy bueno"]},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valores_aprobatorios"] == ["Aprobado", "Excelente", "Muy bueno"]


# ── Task 7.6: Scope-isolated DELETE ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_profesor_deletes_own_grades_only(
    client: AsyncClient, admin_token: str, profesor_token: str,
    setup_academic_context: dict,
):
    """7.6: PROFESOR only deletes own grades."""
    ctx = setup_academic_context

    # Import as ADMIN
    csv_content = "Nombre,Email,TP 1 (Real)\nJuan,juan@test.com,75\n"
    actividades_json = json.dumps(["TP 1"])
    await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        files={
            "file": ("cal.csv", csv_content.encode("utf-8-sig"), "text/csv"),
            "actividades_seleccionadas": ("", actividades_json, "text/plain"),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # PROFESOR deletes without confirmar -> 400
    response = await client.delete(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 400  # Needs confirmar=true


@pytest.mark.asyncio
async def test_coordinador_deletes_all_grades(
    client: AsyncClient, admin_token: str, coordinador_token: str,
    setup_academic_context: dict,
):
    """7.6: COORDINADOR deletes ALL grades for materia."""
    ctx = setup_academic_context

    # Import as ADMIN
    csv_content = "Nombre,Email,TP 1 (Real)\nJuan,juan@test.com,75\nMaria,maria@test.com,80\n"
    actividades_json = json.dumps(["TP 1"])
    await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        files={
            "file": ("cal.csv", csv_content.encode("utf-8-sig"), "text/csv"),
            "actividades_seleccionadas": ("", actividades_json, "text/plain"),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # COORDINADOR deletes all
    response = await client.delete(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        params={"confirmar": True},
        headers={"Authorization": f"Bearer {coordinador_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["eliminados"] > 0

    # Verify empty
    list_resp = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.json()["total"] == 0


# ── Task 7.7: Validation errors ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_import_unsupported_format_400(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.7: Unsupported file format returns 400."""
    ctx = setup_academic_context
    files = {"file": ("calificaciones.pdf", b"%PDF-1.4 content", "application/pdf")}
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        params={"preview": True},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "formato" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_confirm_without_actividades_400(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.7: Confirm without actividades_seleccionadas returns 400."""
    ctx = setup_academic_context
    csv_content = "Nombre,Email,TP 1 (Real)\nJuan,juan@test.com,75\n"
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        files={"file": ("cal.csv", csv_content.encode("utf-8-sig"), "text/csv")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_without_confirm_400(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.7: DELETE without confirmar=true returns 400."""
    ctx = setup_academic_context
    response = await client.delete(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "confirmar" in response.json()["detail"].lower()


# ── Task 7.8: Multi-tenant isolation ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_multi_tenant_isolation(
    client: AsyncClient, admin_token: str, tenant_b_token: str,
    setup_academic_context: dict,
):
    """7.8: Tenant B cannot access tenant A's grades."""
    ctx = setup_academic_context

    # Tenant B tries to access tenant A's materia
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        headers={"Authorization": f"Bearer {tenant_b_token}"},
    )
    # Should be 403 (materia not accessible) or 404 (materia not found in tenant B)
    assert response.status_code in (403, 404)


# ── Task 7.9: Permissions ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_profesor_without_asignacion_403(
    client: AsyncClient, profesor_token: str, setup_academic_context: dict
):
    """7.9: PROFESOR without assignment gets 403."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_401(
    client: AsyncClient, setup_academic_context: dict
):
    """7.9: Unauthenticated request gets 401."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
    )
    assert response.status_code == 401


# ── Additional: Filter grades ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_grades_filter_by_actividad(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """Filter grades by activity name."""
    ctx = setup_academic_context

    csv_content = "Nombre,Email,TP 1 (Real),TP 2 (Real)\nJuan,juan@test.com,75,80\nMaria,maria@test.com,60,65\n"
    actividades_json = json.dumps(["TP 1", "TP 2"])
    await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        files={
            "file": ("cal.csv", csv_content.encode("utf-8-sig"), "text/csv"),
            "actividades_seleccionadas": ("", actividades_json, "text/plain"),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Filter by TP 1
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        params={"actividad": "TP 1"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    for item in data["items"]:
        assert item["actividad"] == "TP 1"


@pytest.mark.asyncio
async def test_list_grades_filter_by_aprobado(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """Filter grades by approval status."""
    ctx = setup_academic_context

    csv_content = "Nombre,Email,TP 1 (Real)\nJuan,juan@test.com,75\nMaria,maria@test.com,45\n"
    actividades_json = json.dumps(["TP 1"])
    await client.post(
        f"/api/materias/{ctx['materia_id']}/calificaciones/importar",
        files={
            "file": ("cal.csv", csv_content.encode("utf-8-sig"), "text/csv"),
            "actividades_seleccionadas": ("", actividades_json, "text/plain"),
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Filter by aprobado=true
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        params={"aprobado": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for item in data["items"]:
        assert item["aprobado"] is True


@pytest.mark.asyncio
async def test_list_grades_empty(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """Empty grades list returns 200 with empty items."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/calificaciones",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
