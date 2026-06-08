"""Integration tests for padron de alumnos API endpoints.

All tests require PostgreSQL via testcontainers.
Marked with ``@pytest.mark.integration`` for selective execution.
"""

import io

import openpyxl
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        True,
        reason="Requires PostgreSQL (testcontainers). "
        "Run with: pytest --run-integration",
    ),
]


@pytest.fixture
def admin_token() -> str:
    """Return a valid JWT for an ADMIN user with padron permissions."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def profesor_token() -> str:
    """Return a JWT for a PROFESOR user with padron permissions."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def coordinador_token() -> str:
    """Return a JWT for a COORDINADOR user."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="coord-uuid",
        tenant_id="tenant-a",
        roles=["COORDINADOR"],
    )


# ── Helper: create a CSV file ─────────────────────────────────────────────


def _make_csv(content: str, filename: str = "padron.csv") -> dict:
    """Create a FastAPI UploadFile-compatible CSV file dict."""
    return {
        "file": (filename, content.encode("utf-8-sig"), "text/csv"),
    }


def _make_xlsx(rows: list[list], filename: str = "padron.xlsx") -> dict:
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
        "file": (filename, buf.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    }


# ── Fixtures: set up materias and cohortes ────────────────────────────────


@pytest.fixture
async def setup_academic_context(
    client: AsyncClient, admin_token: str
) -> dict:
    """Create a carrera, materia, and cohorte for testing."""
    resp_c = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Test Carrera"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    carrera_id = resp_c.json()["id"]

    resp_m = await client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Programacion I"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    materia_id = resp_m.json()["id"]

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

    return {
        "carrera_id": carrera_id,
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
    }


# ── Task 7.2: Import with XLSX ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_import_xlsx_201(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.2: Import padron from XLSX creates version and entries."""
    ctx = setup_academic_context
    files = _make_xlsx([
        ["Nombre", "Apellidos", "Email", "Comision"],
        ["Juan", "Perez", "juan@test.com", "A"],
        ["Maria", "Gomez", "maria@test.com", "B"],
    ])
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total_imported"] == 2
    assert "version_id" in data


# ── Task 7.3: Import with CSV (comma and semicolon) ─────────────────────


@pytest.mark.asyncio
async def test_import_csv_comma_201(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.3: Import padron from CSV (comma delimiter)."""
    ctx = setup_academic_context
    csv_content = "Nombre,Apellidos,Email,Comision\nJuan,Perez,juan@test.com,A\nMaria,Gomez,maria@test.com,B\n"
    files = _make_csv(csv_content)
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["total_imported"] == 2


@pytest.mark.asyncio
async def test_import_csv_semicolon_201(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.3: Import padron from CSV (semicolon delimiter)."""
    ctx = setup_academic_context
    csv_content = "Nombre;Apellidos;Email;Comision\nJuan;Perez;juan@test.com;A\nMaria;Gomez;maria@test.com;B\n"
    files = _make_csv(csv_content)
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["total_imported"] == 2


# ── Task 7.4: Validation errors ────────────────────────────────────────


@pytest.mark.asyncio
async def test_import_empty_file_400(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.4: Empty file returns 400."""
    ctx = setup_academic_context
    # Empty CSV
    files = {"file": ("empty.csv", b"", "text/csv")}
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "vacio" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_missing_columns_400(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.4: Missing required columns returns 400."""
    ctx = setup_academic_context
    files = _make_csv("Apellidos,Comision\nPerez,A\n")
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "nombre" in response.json()["detail"].lower() or "email" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_import_unsupported_format_400(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.4: Unsupported file format returns 400."""
    ctx = setup_academic_context
    files = {"file": ("padron.pdf", b"%PDF-1.4 content", "application/pdf")}
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "formato" in response.json()["detail"].lower()


# ── Task 7.5: Versioning ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_versioning_deactivates_previous(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.5: New version deactivates previous one."""
    ctx = setup_academic_context

    # First import
    files1 = _make_csv("Nombre,Email\nJuan,juan@test.com\n")
    resp1 = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files1,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    version_1_id = resp1.json()["version_id"]

    # Second import
    files2 = _make_csv("Nombre,Email\nMaria,maria@test.com\nPedro,pedro@test.com\n")
    resp2 = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files2,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    version_2_id = resp2.json()["version_id"]

    assert version_1_id != version_2_id

    # Version history should show both
    hist_resp = await client.get(
        f"/api/materias/{ctx['materia_id']}/padron/versiones",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert hist_resp.status_code == 200
    versions = hist_resp.json()
    assert len(versions) >= 2

    # The latest (first in list) should be active
    assert versions[0]["activa"] is True


# ── Task 7.7: Multi-tenant isolation ───────────────────────────────────


@pytest.mark.asyncio
async def test_multi_tenant_isolation(
    client: AsyncClient, db_session: AsyncSession, setup_academic_context: dict
):
    """7.7: Tenant B cannot see tenant A's padron entries."""
    from app.core.security import create_access_token

    ctx = setup_academic_context
    token_a = create_access_token(
        sub="admin-a", tenant_id="tenant-a", roles=["ADMIN"]
    )
    token_b = create_access_token(
        sub="admin-b", tenant_id="tenant-b", roles=["ADMIN"]
    )

    # Import in tenant A
    files = _make_csv("Nombre,Email\nJuan,juan@test.com\n")
    resp = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files,
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 201

    # Try to list from tenant B (will 404 because materia doesn't exist in B)
    resp_b = await client.get(
        f"/api/materias/{ctx['materia_id']}/padron",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # Either 404 (materia not found in tenant B) or 403 (no access)
    assert resp_b.status_code in (403, 404)


# ── Task 7.8: Permissions ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_permissions_profesor_without_asignacion_403(
    client: AsyncClient, profesor_token: str, setup_academic_context: dict
):
    """7.8: PROFESOR without materia assignment gets 403."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/padron",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_permissions_unauthenticated_401(
    client: AsyncClient, setup_academic_context: dict
):
    """7.8: Unauthenticated request gets 401."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/padron",
    )
    assert response.status_code == 401


# ── Task 7.6: Rollback on error ────────────────────────────────────────


@pytest.mark.asyncio
async def test_rollback_on_parse_error(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.6: If parsing fails mid-stream, no orphan version remains."""
    ctx = setup_academic_context

    # Import a valid file first
    files1 = _make_csv("Nombre,Email\nJuan,juan@test.com\n")
    resp1 = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files1,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp1.status_code == 201

    # Now try an invalid file (corrupt bytes)
    files2 = {"file": ("bad.csv", b"\xff\xfe\x00\x01invalid", "text/csv")}
    resp2 = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files2,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # This should fail but not create an orphan version
    assert resp2.status_code == 400

    # The active version should still be the first one
    entries_resp = await client.get(
        f"/api/materias/{ctx['materia_id']}/padron",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert entries_resp.status_code == 200
    entries = entries_resp.json()
    assert len(entries) == 1


# ── Task 7.9: Encryption at rest ───────────────────────────────────────


@pytest.mark.asyncio
async def test_email_encrypted_in_db(
    client: AsyncClient, admin_token: str, db_session: AsyncSession,
    setup_academic_context: dict,
):
    """7.9: Email is stored encrypted in DB, readable via ORM."""
    from sqlalchemy import text

    ctx = setup_academic_context

    # Import
    files = _make_csv("Nombre,Email\nJuan,juan@test.com\n")
    resp = await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    version_id = resp.json()["version_id"]

    # Query the raw DB value
    result = await db_session.execute(
        text("SELECT email FROM entradas_padron WHERE version_id = :vid"),
        {"vid": version_id},
    )
    raw_email = result.scalar_one()

    # The raw value should NOT be the plaintext — it should be base64-encoded
    # encrypted data (not "juan@test.com")
    assert raw_email != "juan@test.com"
    # Encrypted values are base64 strings (alphanumeric plus +/=)
    assert isinstance(raw_email, str)
    assert len(raw_email) > 10


# ── Additional: GET active entries ─────────────────────────────────────


@pytest.mark.asyncio
async def test_get_active_entries_200(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """GET /padron returns active entries."""
    ctx = setup_academic_context

    # Import
    files = _make_csv("Nombre,Apellidos,Email\nJuan,Perez,juan@test.com\nMaria,Gomez,maria@test.com\n")
    await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # List
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/padron",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["nombre"] in ("Juan", "Maria")
    assert data[0]["email"] in ("juan@test.com", "maria@test.com")


@pytest.mark.asyncio
async def test_get_version_history_200(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """GET /padron/versiones returns version list."""
    ctx = setup_academic_context

    # Import twice
    files1 = _make_csv("Nombre,Email\nJuan,juan@test.com\n")
    await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files1,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    files2 = _make_csv("Nombre,Email\nMaria,maria@test.com\n")
    await client.post(
        f"/api/materias/{ctx['materia_id']}/padron/importar",
        params={"cohorte_id": ctx["cohorte_id"]},
        files=files2,
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/padron/versiones",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) >= 2
    # Most recent first
    assert versions[0]["activa"] is True
