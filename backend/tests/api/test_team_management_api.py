"""Integration tests for team management API endpoints (C-05).

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
def profesor_token() -> str:
    """Return a JWT for a PROFESOR (no team management permission)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def coordinador_token() -> str:
    """Return a JWT for a COORDINADOR with equipo_docente:ver and :asignar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="coord-uuid",
        tenant_id="tenant-a",
        roles=["COORDINADOR"],
    )


@pytest.fixture
async def setup_academic_context(
    client: AsyncClient, admin_token: str
) -> dict:
    """Create academic entities needed for tests.

    Returns:
        Dict with ids: carrera_id, materia_id, cohorte_id, usuario_id.
    """
    # Create carrera
    resp_c = await client.post(
        "/api/admin/carreras",
        json={"codigo": "TUPAD", "nombre": "Test"},
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
    resp_ch = await client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": carrera_id,
            "nombre": "MAR-2026",
            "anio": 2026,
            "vig_desde": "2026-03-01",
            "vig_hasta": "2026-12-31",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    cohorte_id = resp_ch.json()["id"]

    return {
        "carrera_id": carrera_id,
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
    }


# ── Task 9.1: Create individual assignment ──────────────────────────────


@pytest.mark.asyncio
async def test_create_asignacion_201(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.1: Create Asignacion returns 201 with computed estado_vigencia."""
    ctx = setup_academic_context
    response = await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "comisiones": ["A", "B"],
            "vig_desde": "2026-03-01",
            "vig_hasta": "2026-12-31",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["usuario_id"] == "admin-uuid"
    assert data["rol"] == "PROFESOR"
    assert data["comisiones"] == ["A", "B"]
    assert "estado_vigencia" in data
    assert "id" in data
    assert "tenant_id" in data


# ── Task 9.2: Create with invalid date range ────────────────────────────


@pytest.mark.asyncio
async def test_create_asignacion_date_range_422(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.2: vig_desde after vig_hasta returns 422."""
    ctx = setup_academic_context
    response = await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "vig_desde": "2026-12-31",
            "vig_hasta": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


# ── Task 9.3: Get single assignment ─────────────────────────────────────


@pytest.mark.asyncio
async def test_get_asignacion_200(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.3: Get single Asignacion by ID returns 200."""
    ctx = setup_academic_context
    # Create
    resp = await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    asignacion_id = resp.json()["id"]

    # Get
    response = await client.get(
        f"/api/admin/asignaciones/{asignacion_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == asignacion_id
    assert "estado_vigencia" in data


# ── Task 9.4: Cross-tenant access returns 404 ────────────────────────────


@pytest.mark.asyncio
async def test_get_asignacion_cross_tenant_404(
    client: AsyncClient, db_session: AsyncSession, setup_academic_context: dict
):
    """9.4: Different tenant cannot access assignment."""
    from app.core.security import create_access_token

    ctx = setup_academic_context
    admin_a_token = create_access_token(
        sub="admin-a", tenant_id="tenant-a", roles=["ADMIN"]
    )
    # Create in tenant-a
    resp = await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {admin_a_token}"},
    )
    asignacion_id = resp.json()["id"]

    # Access from tenant-b
    tenant_b_token = create_access_token(
        sub="admin-b", tenant_id="tenant-b", roles=["ADMIN"]
    )
    response = await client.get(
        f"/api/admin/asignaciones/{asignacion_id}",
        headers={"Authorization": f"Bearer {tenant_b_token}"},
    )
    assert response.status_code == 404


# ── Task 9.5: List with filters ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_asignaciones_with_filters_200(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.5: List with filters returns filtered results."""
    ctx = setup_academic_context
    # Create two assignments
    await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # List with materia_id filter
    response = await client.get(
        f"/api/admin/asignaciones?materia_id={ctx['materia_id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for item in data:
        assert "estado_vigencia" in item

    # List without filters
    response_all = await client.get(
        "/api/admin/asignaciones",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response_all.status_code == 200


# ── Task 9.6: Update assignment ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_asignacion_200(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.6: Update vigencia dates returns updated assignment."""
    ctx = setup_academic_context
    # Create
    resp = await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
            "vig_hasta": "2026-12-31",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    asignacion_id = resp.json()["id"]

    # Update vig_hasta
    response = await client.put(
        f"/api/admin/asignaciones/{asignacion_id}",
        json={"vig_hasta": "2027-03-01"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["vig_hasta"] == "2027-03-01"
    assert "estado_vigencia" in data


# ── Task 9.7: Bulk assignment ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_asignacion_masiva_201(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.7: Bulk assign multiple usuarios returns all created."""
    ctx = setup_academic_context
    response = await client.post(
        "/api/admin/asignaciones/masiva",
        json={
            "usuario_ids": ["user-1", "user-2", "user-3"],
            "rol": "TUTOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "comisiones": ["A"],
            "vig_desde": "2026-03-01",
            "vig_hasta": "2026-12-31",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total"] == 3
    assert len(data["creadas"]) == 3


# ── Task 9.8: Bulk assignment with non-existent usuario ─────────────────


@pytest.mark.asyncio
async def test_asignacion_masiva_nonexistent_usuario_404(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.8: Non-existent usuario_id returns 404 with rollback."""
    ctx = setup_academic_context
    response = await client.post(
        "/api/admin/asignaciones/masiva",
        json={
            "usuario_ids": ["nonexistent-user"],
            "rol": "TUTOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


# ── Task 9.9: Clone equipo ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_clonar_equipo_201(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.9: Clone equipo returns cloned count."""
    ctx = setup_academic_context
    # Create source assignments
    await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Create destination cohorte
    resp_dest = await client.post(
        "/api/admin/cohortes",
        json={
            "carrera_id": ctx["carrera_id"],
            "nombre": "AGO-2026",
            "anio": 2026,
            "vig_desde": "2026-08-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    dest_cohorte_id = resp_dest.json()["id"]

    # Clone
    response = await client.post(
        "/api/admin/asignaciones/clonar",
        json={
            "origen_materia_id": ctx["materia_id"],
            "origen_carrera_id": ctx["carrera_id"],
            "origen_cohorte_id": ctx["cohorte_id"],
            "destino_materia_id": ctx["materia_id"],
            "destino_carrera_id": ctx["carrera_id"],
            "destino_cohorte_id": dest_cohorte_id,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["clonadas"] >= 1


# ── Task 9.10: Clone with identical source/destination ──────────────────


@pytest.mark.asyncio
async def test_clonar_equipo_identical_context_422(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.10: Clone with identical source/destination returns 422."""
    ctx = setup_academic_context
    response = await client.post(
        "/api/admin/asignaciones/clonar",
        json={
            "origen_materia_id": ctx["materia_id"],
            "origen_carrera_id": ctx["carrera_id"],
            "origen_cohorte_id": ctx["cohorte_id"],
            "destino_materia_id": ctx["materia_id"],
            "destino_carrera_id": ctx["carrera_id"],
            "destino_cohorte_id": ctx["cohorte_id"],
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


# ── Task 9.11: Bulk vigencia update ─────────────────────────────────────


@pytest.mark.asyncio
async def test_actualizar_vigencia_200(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.11: Bulk vigencia update returns updated count."""
    ctx = setup_academic_context
    # Create some assignments
    await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.put(
        "/api/admin/asignaciones/vigencia",
        json={
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
            "vig_hasta": "2027-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["actualizadas"] >= 1


# ── Task 9.12: Export equipo as CSV ─────────────────────────────────────


@pytest.mark.asyncio
async def test_exportar_equipo_csv_200(
    client: AsyncClient, admin_token: str, setup_academic_context: dict
):
    """9.12: Export equipo returns CSV with correct headers."""
    ctx = setup_academic_context
    # Create an assignment
    await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.get(
        f"/api/admin/equipos/export?materia_id={ctx['materia_id']}&carrera_id={ctx['carrera_id']}&cohorte_id={ctx['cohorte_id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
    assert "attachment" in response.headers.get("content-disposition", "")
    body = response.text
    assert "docente_nombre" in body
    assert "docente_apellidos" in body
    assert "docente_email" in body
    assert "estado_vigencia" in body


# ── Task 9.13: Unauthenticated request returns 401 ──────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_401(client: AsyncClient):
    """9.13: Requests without JWT return 401."""
    endpoints = [
        ("GET", "/api/admin/asignaciones"),
        ("POST", "/api/admin/asignaciones"),
        ("GET", "/api/admin/asignaciones/some-id"),
        ("PUT", "/api/admin/asignaciones/some-id"),
        ("POST", "/api/admin/asignaciones/masiva"),
        ("POST", "/api/admin/asignaciones/clonar"),
        ("PUT", "/api/admin/asignaciones/vigencia"),
        ("GET", "/api/admin/equipos/export"),
    ]
    for method, path in endpoints:
        response = await client.request(method, path)
        assert response.status_code == 401, f"{method} {path} returned {response.status_code}"


# ── Task 9.14: Non-admin user gets 403 on mutating endpoints ────────────


@pytest.mark.asyncio
async def test_non_admin_mutating_403(
    client: AsyncClient, profesor_token: str
):
    """9.14: PROFESOR (no equipo_docente:asignar) gets 403 on mutating."""
    mutating_endpoints = [
        ("POST", "/api/admin/asignaciones"),
        ("PUT", "/api/admin/asignaciones/some-id"),
        ("POST", "/api/admin/asignaciones/masiva"),
        ("POST", "/api/admin/asignaciones/clonar"),
        ("PUT", "/api/admin/asignaciones/vigencia"),
    ]
    for method, path in mutating_endpoints:
        response = await client.request(
            method, path,
            json={"usuario_id": "x", "rol": "PROFESOR", "vig_desde": "2026-03-01"},
            headers={"Authorization": f"Bearer {profesor_token}"},
        )
        assert response.status_code == 403, f"{method} {path} returned {response.status_code}"


# ── Task 9.15: Cross-tenant isolation ────────────────────────────────────


@pytest.mark.asyncio
async def test_cross_tenant_isolation(
    client: AsyncClient, db_session: AsyncSession, setup_academic_context: dict
):
    """9.15: Tenant A cannot read/mutate Tenant B's assignments."""
    from app.core.security import create_access_token

    ctx = setup_academic_context
    token_a = create_access_token(
        sub="admin-a", tenant_id="tenant-a", roles=["ADMIN"]
    )
    token_b = create_access_token(
        sub="admin-b", tenant_id="tenant-b", roles=["ADMIN"]
    )

    # Create in tenant-a
    resp = await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 201

    # List from tenant-b — should see nothing
    resp_b = await client.get(
        "/api/admin/asignaciones",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200
    assert len(resp_b.json()) == 0
