"""Integration tests for salary grid API endpoints (C-18).

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
    """Return a valid JWT for an ADMIN user with all permissions."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def finanzas_token() -> str:
    """Return a JWT for a FINANZAS user with liquidaciones:configurar-salarios."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="finanzas-uuid",
        tenant_id="tenant-a",
        roles=["FINANZAS"],
    )


@pytest.fixture
def profesor_token() -> str:
    """Return a JWT for a PROFESOR (no salary grid perms)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def otro_tenant_token() -> str:
    """Return a JWT for an ADMIN in a different tenant."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="other-admin",
        tenant_id="tenant-b",
        roles=["ADMIN"],
    )


@pytest.fixture
def unauth_token() -> str:
    """Return a malformed JWT."""
    return "invalid-token"


# ── Task 7.1: SalarioBase CRUD + overlap + vigente ─────────────────────


@pytest.mark.asyncio
async def test_create_salario_base_201(
    client: AsyncClient, finanzas_token: str
):
    """Create salary base entry returns 201."""
    response = await client.post(
        "/api/admin/salarios/base",
        json={
            "rol": "PROFESOR",
            "monto": 150000.00,
            "desde": "2026-01-01",
        },
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["rol"] == "PROFESOR"
    assert data["monto"] == 150000.00
    assert data["desde"] == "2026-01-01"
    assert data["hasta"] is None
    assert "id" in data
    assert "tenant_id" in data


@pytest.mark.asyncio
async def test_create_salario_base_with_hasta_201(
    client: AsyncClient, finanzas_token: str
):
    """Create salary base with explicit hasta."""
    response = await client.post(
        "/api/admin/salarios/base",
        json={
            "rol": "PROFESOR",
            "monto": 140000.00,
            "desde": "2025-06-01",
            "hasta": "2025-12-31",
        },
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 201
    assert response.json()["hasta"] == "2025-12-31"


@pytest.mark.asyncio
async def test_create_salario_base_overlap_409(
    client: AsyncClient, finanzas_token: str
):
    """Reject overlapping date range for same role."""
    # Create first entry
    await client.post(
        "/api/admin/salarios/base",
        json={
            "rol": "PROFESOR",
            "monto": 150000.00,
            "desde": "2026-01-01",
            "hasta": "2026-12-31",
        },
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    # Create overlapping entry
    response = await client.post(
        "/api/admin/salarios/base",
        json={
            "rol": "PROFESOR",
            "monto": 160000.00,
            "desde": "2026-06-01",
            "hasta": "2026-12-31",
        },
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_salario_base_200(
    client: AsyncClient, finanzas_token: str
):
    """List all salary base entries."""
    # Create two entries
    await client.post(
        "/api/admin/salarios/base",
        json={"rol": "PROFESOR", "monto": 150000.00, "desde": "2026-01-01"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    await client.post(
        "/api/admin/salarios/base",
        json={"rol": "TUTOR", "monto": 80000.00, "desde": "2026-01-01"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    response = await client.get(
        "/api/admin/salarios/base",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_salario_base_200(
    client: AsyncClient, finanzas_token: str
):
    """Get single salary base entry by ID."""
    created = await client.post(
        "/api/admin/salarios/base",
        json={"rol": "COORDINADOR", "monto": 200000.00, "desde": "2026-01-01"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    entry_id = created.json()["id"]

    response = await client.get(
        f"/api/admin/salarios/base/{entry_id}",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == entry_id


@pytest.mark.asyncio
async def test_get_salario_base_404(
    client: AsyncClient, finanzas_token: str
):
    """Get non-existent salary base returns 404."""
    response = await client.get(
        "/api/admin/salarios/base/nonexistent-id",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_salario_base_200(
    client: AsyncClient, finanzas_token: str
):
    """Update salary base entry."""
    created = await client.post(
        "/api/admin/salarios/base",
        json={"rol": "PROFESOR", "monto": 150000.00, "desde": "2026-01-01"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    entry_id = created.json()["id"]

    response = await client.put(
        f"/api/admin/salarios/base/{entry_id}",
        json={"monto": 160000.00},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    assert response.json()["monto"] == 160000.00


@pytest.mark.asyncio
async def test_update_salario_base_overlap_409(
    client: AsyncClient, finanzas_token: str
):
    """Reject overlapping update."""
    await client.post(
        "/api/admin/salarios/base",
        json={"rol": "PROFESOR", "monto": 150000.00, "desde": "2026-01-01", "hasta": "2026-06-30"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    created2 = await client.post(
        "/api/admin/salarios/base",
        json={"rol": "PROFESOR", "monto": 160000.00, "desde": "2026-07-01", "hasta": "2026-12-31"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    entry2_id = created2.json()["id"]

    # Update entry2 to overlap with entry1
    response = await client.put(
        f"/api/admin/salarios/base/{entry2_id}",
        json={"desde": "2026-03-01"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_salario_base_invalid_rol_422(
    client: AsyncClient, finanzas_token: str
):
    """Reject invalid rol."""
    response = await client.post(
        "/api/admin/salarios/base",
        json={"rol": "INEXISTENTE", "monto": 1000.00, "desde": "2026-01-01"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_salario_base_missing_fields_422(
    client: AsyncClient, finanzas_token: str
):
    """Reject missing monto or desde."""
    response = await client.post(
        "/api/admin/salarios/base",
        json={"rol": "PROFESOR"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 422


# ── Task 7.2: SalarioPlus CRUD + overlap + vigente ─────────────────────


@pytest.mark.asyncio
async def test_create_salario_plus_201(
    client: AsyncClient, finanzas_token: str
):
    """Create salary plus entry returns 201."""
    response = await client.post(
        "/api/admin/salarios/plus",
        json={
            "grupo": "PROG",
            "rol": "PROFESOR",
            "descripcion": "Plus Programacion",
            "monto": 5000.00,
            "desde": "2026-01-01",
        },
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["grupo"] == "PROG"
    assert data["rol"] == "PROFESOR"
    assert data["monto"] == 5000.00


@pytest.mark.asyncio
async def test_list_salario_plus_200(
    client: AsyncClient, finanzas_token: str
):
    """List all salary plus entries."""
    await client.post(
        "/api/admin/salarios/plus",
        json={
            "grupo": "PROG",
            "rol": "PROFESOR",
            "descripcion": "Plus Programacion",
            "monto": 5000.00,
            "desde": "2026-01-01",
        },
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    response = await client.get(
        "/api/admin/salarios/plus",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_update_salario_plus_200(
    client: AsyncClient, finanzas_token: str
):
    """Update salary plus entry."""
    created = await client.post(
        "/api/admin/salarios/plus",
        json={
            "grupo": "PROG",
            "rol": "PROFESOR",
            "descripcion": "Plus Programacion",
            "monto": 5000.00,
            "desde": "2026-01-01",
        },
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    entry_id = created.json()["id"]

    response = await client.put(
        f"/api/admin/salarios/plus/{entry_id}",
        json={"monto": 6000.00},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    assert response.json()["monto"] == 6000.00


@pytest.mark.asyncio
async def test_create_salario_plus_overlap_409(
    client: AsyncClient, finanzas_token: str
):
    """Reject overlapping date range for same grupo+rol."""
    await client.post(
        "/api/admin/salarios/plus",
        json={
            "grupo": "PROG",
            "rol": "PROFESOR",
            "descripcion": "Original",
            "monto": 5000.00,
            "desde": "2026-01-01",
            "hasta": "2026-12-31",
        },
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    response = await client.post(
        "/api/admin/salarios/plus",
        json={
            "grupo": "PROG",
            "rol": "PROFESOR",
            "descripcion": "Overlap",
            "monto": 6000.00,
            "desde": "2026-06-01",
            "hasta": "2026-12-31",
        },
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 409


# ── Task 7.3: GrupoMateria CRUD + assignment ────────────────────────────


@pytest.mark.asyncio
async def test_create_grupo_materia_201(
    client: AsyncClient, finanzas_token: str
):
    """Create subject group returns 201."""
    response = await client.post(
        "/api/admin/salarios/grupos",
        json={"grupo": "PROG", "descripcion": "Materias de Programacion"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 201
    assert response.json()["grupo"] == "PROG"


@pytest.mark.asyncio
async def test_create_grupo_materia_duplicate_409(
    client: AsyncClient, finanzas_token: str
):
    """Reject duplicate group key within tenant."""
    await client.post(
        "/api/admin/salarios/grupos",
        json={"grupo": "PROG", "descripcion": "Original"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    response = await client.post(
        "/api/admin/salarios/grupos",
        json={"grupo": "PROG", "descripcion": "Duplicate"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_grupos_materia_200(
    client: AsyncClient, finanzas_token: str
):
    """List all subject groups."""
    await client.post(
        "/api/admin/salarios/grupos",
        json={"grupo": "PROG"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    response = await client.get(
        "/api/admin/salarios/grupos",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_assign_materias_to_grupo_200(
    client: AsyncClient, admin_token: str, finanzas_token: str
):
    """Assign materias to a group (requires existing materia from admin context)."""
    # Create a materia first (admin has estructura_academica:gestionar)
    resp_m = await client.post(
        "/api/admin/materias",
        json={"codigo": "TEST_MAT", "nombre": "Test Materia"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    materia_id = resp_m.json()["id"]

    # Create a group
    resp_g = await client.post(
        "/api/admin/salarios/grupos",
        json={"grupo": "TEST_GRP"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    grupo_id = resp_g.json()["id"]

    # Assign materia to group
    response = await client.put(
        f"/api/admin/salarios/grupos/{grupo_id}/materias",
        json={"materia_ids": [materia_id]},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    assigned = response.json()
    assert len(assigned) == 1
    assert assigned[0]["materia_id"] == materia_id


@pytest.mark.asyncio
async def test_get_materias_by_grupo_200(
    client: AsyncClient, admin_token: str, finanzas_token: str
):
    """Get materias assigned to a group."""
    resp_m = await client.post(
        "/api/admin/materias",
        json={"codigo": "TEST_MAT2", "nombre": "Test Materia 2"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    materia_id = resp_m.json()["id"]

    resp_g = await client.post(
        "/api/admin/salarios/grupos",
        json={"grupo": "TEST_GRP2"},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    grupo_id = resp_g.json()["id"]

    await client.put(
        f"/api/admin/salarios/grupos/{grupo_id}/materias",
        json={"materia_ids": [materia_id]},
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )

    response = await client.get(
        f"/api/admin/salarios/grupos/{grupo_id}/materias",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


# ── Task 7.4: Auth/permission tests ─────────────────────────────────────


@pytest.mark.asyncio
async def test_salario_base_401_without_auth(client: AsyncClient):
    """No auth token returns 401."""
    response = await client.get("/api/admin/salarios/base")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_salario_base_403_wrong_role(
    client: AsyncClient, profesor_token: str
):
    """PROFESOR cannot access salary grid."""
    response = await client.get(
        "/api/admin/salarios/base",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_salario_plus_401_without_auth(client: AsyncClient):
    """No auth token returns 401."""
    response = await client.get("/api/admin/salarios/plus")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_salario_plus_403_wrong_role(
    client: AsyncClient, profesor_token: str
):
    """PROFESOR cannot access salary plus."""
    response = await client.get(
        "/api/admin/salarios/plus",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_grupos_materia_401_without_auth(client: AsyncClient):
    """No auth token returns 401."""
    response = await client.get("/api/admin/salarios/grupos")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_grupos_materia_403_wrong_role(
    client: AsyncClient, profesor_token: str
):
    """PROFESOR cannot access subject groups."""
    response = await client.get(
        "/api/admin/salarios/grupos",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_salario_base_200_finanzas(
    client: AsyncClient, finanzas_token: str
):
    """FINANZAS can access salary base."""
    response = await client.get(
        "/api/admin/salarios/base",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_salario_plus_200_finanzas(
    client: AsyncClient, finanzas_token: str
):
    """FINANZAS can access salary plus."""
    response = await client.get(
        "/api/admin/salarios/plus",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_grupos_materia_200_finanzas(
    client: AsyncClient, finanzas_token: str
):
    """FINANZAS can access subject groups."""
    response = await client.get(
        "/api/admin/salarios/grupos",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
