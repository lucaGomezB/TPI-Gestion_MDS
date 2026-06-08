"""Integration tests for academic structure API endpoints.

All tests require PostgreSQL via testcontainers.
Marked with ``@pytest.mark.integration`` for selective execution.
"""

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
    """Return a valid JWT for an ADMIN user with estructura_academica:gestionar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def profesor_token() -> str:
    """Return a JWT for a PROFESOR (no academic structure permission)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.mark.asyncio
async def test_post_carreras_201(
    client: AsyncClient, admin_token: str
):
    """8.1: Create Carrera returns 201."""
    response = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Tecnicatura Universitaria"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == "TUPAD"
    assert data["estado"] == "Activa"
    assert "id" in data


@pytest.mark.asyncio
async def test_post_carreras_duplicate_409(
    client: AsyncClient, admin_token: str, db_session: AsyncSession
):
    """8.2: Duplicate codigo returns 409."""
    # Create first
    await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "First"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # Try duplicate
    response = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Second"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_carreras_200(
    client: AsyncClient, admin_token: str
):
    """8.3: List carreras returns tenant-scoped list."""
    response = await client.get(
        "/api/admin/carreras",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_carreras_cross_tenant_404(
    client: AsyncClient, db_session: AsyncSession
):
    """8.4: Different tenant returns 404."""
    from app.core.security import create_access_token

    tenant_b_token = create_access_token(
        sub="user-b",
        tenant_id="tenant-b",
        roles=["ADMIN"],
    )
    # Create a carrera in tenant-a
    admin_token_a = create_access_token(
        sub="admin-a",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )
    resp = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Test"},
        headers={"Authorization": f"Bearer {admin_token_a}"},
    )
    carrera_id = resp.json()["id"]

    # Get from tenant-b
    response = await client.get(
        f"/api/admin/carreras/{carrera_id}",
        headers={"Authorization": f"Bearer {tenant_b_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_put_carreras_inactiva_200(
    client: AsyncClient, admin_token: str
):
    """8.5: Update Carrera estado to Inactiva."""
    # Create
    resp = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    carrera_id = resp.json()["id"]

    # Update
    response = await client.put(
        f"/api/admin/carreras/{carrera_id}",
        json={"estado": "Inactiva"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "Inactiva"


@pytest.mark.asyncio
async def test_post_cohortes_with_vigencia_201(
    client: AsyncClient, admin_token: str
):
    """8.6: Create Cohorte with vig_desde and vig_hasta."""
    # Create a carrera first
    resp = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    carrera_id = resp.json()["id"]

    response = await client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "MAR-2025",
            "anio": 2025,
            "vig_desde": "2025-03-01",
            "vig_hasta": "2025-12-31",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "MAR-2025"
    assert data["vig_hasta"] == "2025-12-31"


@pytest.mark.asyncio
async def test_post_cohortes_duplicate_409(
    client: AsyncClient, admin_token: str
):
    """8.7: Duplicate nombre in same carrera returns 409."""
    resp = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    carrera_id = resp.json()["id"]

    # Create first cohorte
    await client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "MAR-2025",
            "anio": 2025,
            "vig_desde": "2025-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # Duplicate
    response = await client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "MAR-2025",
            "anio": 2025,
            "vig_desde": "2025-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_post_materias_uppercase_201(
    client: AsyncClient, admin_token: str
):
    """8.8: Create Materia with lowercase codigo gets uppercased."""
    response = await client.post(
        "/api/admin/materias",
        json={"codigo": "prog_i", "nombre": "Programación I"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    assert response.json()["codigo"] == "PROG_I"


@pytest.mark.asyncio
async def test_post_materias_duplicate_409(
    client: AsyncClient, admin_token: str
):
    """8.9: Duplicate codigo for Materia returns 409."""
    await client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "First"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    response = await client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Second"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_upload_programa_materia_201(
    client: AsyncClient, admin_token: str
):
    """8.10: Upload PDF for ProgramaMateria."""
    resp_c = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    carrera_id = resp_c.json()["id"]

    resp_m = await client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Prog I"},
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

    response = await client.post(
        "/api/admin/programas-materia/upload",
        data={
            "titulo": "Programa 2025",
            "materia_id": materia_id,
            "carrera_id": carrera_id,
            "cohorte_id": cohorte_id,
        },
        files={"file": ("programa.pdf", b"%PDF-1.4 test content", "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Programa 2025"
    assert "id" in data


@pytest.mark.asyncio
async def test_delete_programa_materia_204(
    client: AsyncClient, admin_token: str
):
    """8.11: Delete ProgramaMateria returns 204."""
    # Setup - create entities and upload
    resp_c = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Test"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    carrera_id = resp_c.json()["id"]
    resp_m = await client.post(
        "/api/admin/materias",
        json={"codigo": "PROG_I", "nombre": "Prog I"},
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
    resp_u = await client.post(
        "/api/admin/programas-materia/upload",
        data={
            "titulo": "Programa 2025",
            "materia_id": materia_id,
            "carrera_id": carrera_id,
            "cohorte_id": cohorte_id,
        },
        files={"file": ("programa.pdf", b"%PDF-1.4 content", "application/pdf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    programa_id = resp_u.json()["id"]

    response = await client.delete(
        f"/api/admin/programas-materia/{programa_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_cross_tenant_isolation(
    client: AsyncClient, db_session: AsyncSession
):
    """8.12: Cross-tenant isolation."""
    from app.core.security import create_access_token

    token_a = create_access_token(
        sub="admin-a", tenant_id="tenant-a", roles=["ADMIN"]
    )
    token_b = create_access_token(
        sub="admin-b", tenant_id="tenant-b", roles=["ADMIN"]
    )

    # Create in tenant A
    resp = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Tenant A Carrera"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 201
    carrera_a_id = resp.json()["id"]

    # List from tenant B
    resp_b = await client.get(
        "/api/admin/carreras",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200
    ids_b = [c["id"] for c in resp_b.json()]
    assert carrera_a_id not in ids_b


@pytest.mark.asyncio
async def test_non_admin_403(
    client: AsyncClient, profesor_token: str
):
    """8.13: Non-admin user gets 403."""
    response = await client.get(
        "/api/admin/carreras",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403
    assert "Not enough permissions" in response.json()["detail"]


@pytest.mark.asyncio
async def test_unauthenticated_401(client: AsyncClient):
    """8.14: Unauthenticated request gets 401."""
    response = await client.get("/api/admin/carreras")
    assert response.status_code == 401
