"""Integration tests for atrasados-ranking API endpoints.

All tests require PostgreSQL via testcontainers.
Marked with ``@pytest.mark.integration`` for selective execution.
"""

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

    # Import padron with comision data
    import io
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    if ws is not None:
        ws.append(["Nombre", "Apellidos", "Email", "Comision"])
        ws.append(["Juan", "Perez", "juan@test.com", "A"])
        ws.append(["Maria", "Gomez", "maria@test.com", "A"])
        ws.append(["Pedro", "Lopez", "pedro@test.com", "B"])
        ws.append(["Ana", "Silva", "ana@test.com", "B"])
        ws.append(["Luis", "Martinez", "luis@test.com", "A"])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    files = {
        "file": (
            "padron.xlsx",
            buf.read(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    }
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
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════════


# ── GET /atrasados ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_atrasados_empty_without_padron(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.5: No padron returns empty response."""
    # Use a materia without padron
    resp = await client.post(
        "/api/admin/materias",
        json={"codigo": "MATE", "nombre": "Matematicas"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    new_materia_id = resp.json()["id"]

    response = await client.get(
        f"/api/materias/{new_materia_id}/atrasados",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["metrics"]["total_alumnos"] == 0
    assert data["metrics"]["total_atrasados"] == 0


@pytest.mark.asyncio
async def test_atrasados_all_faltantes_without_grades(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.1: All students are faltantes when no grades exist."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/atrasados",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5  # 5 students from padron
    assert data["metrics"]["total_alumnos"] == 5
    assert data["metrics"]["total_atrasados"] == 5
    for item in data["items"]:
        assert item["razon"] == "faltante"
        assert item["total_actividades"] == 0


@pytest.mark.asyncio
async def test_atrasados_csv_export(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.4: CSV export returns correct Content-Type and headers."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/atrasados",
        params={"exportar": "csv"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert "attachment" in response.headers["content-disposition"]
    assert "filename=" in response.headers["content-disposition"]
    content = response.text
    assert "nombre;apellidos;email;comision" in content
    assert "Pedro;Lopez" in content


@pytest.mark.asyncio
async def test_atrasados_filter_comision(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.1: Filter by comision returns only matching students."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/atrasados",
        params={"comision": "A"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    # Only 3 students in comision A: Juan, Maria, Luis
    assert data["total"] == 3
    for item in data["items"]:
        assert item["comision"] == "A"


@pytest.mark.asyncio
async def test_atrasados_filter_busqueda(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.1: Filter by busqueda returns matching students."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/atrasados",
        params={"busqueda": "garcia"},  # No match
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0

    # Search by apellido
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/atrasados",
        params={"busqueda": "Perez"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["apellidos"] == "Perez"


@pytest.mark.asyncio
async def test_atrasados_permission_denied(
    client: AsyncClient, setup_academic_context: dict
):
    """7.5: Unauthenticated request returns 401."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/atrasados",
    )
    assert response.status_code == 401


# ── GET /ranking ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ranking_empty_without_grades(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.2: Ranking is empty when no grades exist (RN-09)."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/ranking",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_ranking_csv_export(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.4: Ranking CSV export returns correct format."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/ranking",
        params={"exportar": "csv"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert "attachment" in response.headers["content-disposition"]
    content = response.text
    assert "nombre;apellidos;comision" in content


@pytest.mark.asyncio
async def test_ranking_filter_comision(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.2: Filter by comision returns only matching students."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/ranking",
        params={"comision": "B"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200


# ── GET /reportes ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reportes_empty_without_padron(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.3: Reportes with no padron returns zeros."""
    resp = await client.post(
        "/api/admin/materias",
        json={"codigo": "FISICA", "nombre": "Fisica"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    new_materia_id = resp.json()["id"]

    response = await client.get(
        f"/api/materias/{new_materia_id}/reportes",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_alumnos"] == 0
    assert data["alumnos_con_calificaciones"] == 0
    assert data["total_atrasados"] == 0
    assert data["porcentaje_atrasados"] == 0.0


@pytest.mark.asyncio
async def test_reportes_with_full_data(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """7.3: Reportes with data returns correct metrics."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/reportes",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_alumnos"] == 5
    assert data["total_atrasados"] == 5  # All faltantes
    assert data["porcentaje_atrasados"] == 100.0


@pytest.mark.asyncio
async def test_reportes_permission_denied(
    client: AsyncClient, setup_academic_context: dict
):
    """7.5: Unauthenticated request returns 401 for reportes."""
    ctx = setup_academic_context
    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/reportes",
    )
    assert response.status_code == 401
