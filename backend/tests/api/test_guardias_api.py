"""Integration tests for guardia API endpoints (C-14, F6.6).

All tests require PostgreSQL via testcontainers.
Marked with ``@pytest.mark.integration`` for selective execution.
"""

import pytest
from httpx import AsyncClient

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        True,
        reason="Requires PostgreSQL (testcontainers). "
        "Run with: pytest --run-integration",
    ),
]


# ── Token fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def admin_token() -> str:
    """Return a valid JWT for an ADMIN user."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def profesor_token() -> str:
    """Return a JWT for a PROFESOR (guardias:registrar)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def tutor_token() -> str:
    """Return a JWT for a TUTOR (guardias:registrar)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="tutor-uuid",
        tenant_id="tenant-a",
        roles=["TUTOR"],
    )


@pytest.fixture
async def setup_guardia_context(
    client: AsyncClient, admin_token: str
) -> dict:
    """Create academic entities needed for guardia tests.

    Returns:
        Dict with ids: materia_id, asignacion_id, carrera_id, cohorte_id.
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

    # Create asignacion
    resp_a = await client.post(
        "/api/admin/asignaciones",
        json={
            "usuario_id": "admin-uuid",
            "rol": "PROFESOR",
            "materia_id": materia_id,
            "carrera_id": carrera_id,
            "cohorte_id": cohorte_id,
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    asignacion_id = resp_a.json()["id"]

    return {
        "carrera_id": carrera_id,
        "materia_id": materia_id,
        "cohorte_id": cohorte_id,
        "asignacion_id": asignacion_id,
    }


# ── Task 8.6: Guardia registration ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_registrar_guardia_201(
    client: AsyncClient, profesor_token: str, setup_guardia_context: dict
):
    """8.6: Register guardia returns 201 with full data."""
    ctx = setup_guardia_context
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/guardias",
        json={
            "asignacion_id": ctx["asignacion_id"],
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "dia": "Lunes",
            "horario": "14:00-16:00",
            "comentarios": "Atencion a alumnos",
        },
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["dia"] == "Lunes"
    assert data["horario"] == "14:00-16:00"
    assert data["comentarios"] == "Atencion a alumnos"
    assert "id" in data
    assert "tenant_id" in data


@pytest.mark.asyncio
async def test_registrar_guardia_minimal_201(
    client: AsyncClient, tutor_token: str, setup_guardia_context: dict
):
    """8.6: Register guardia with minimal fields returns 201."""
    ctx = setup_guardia_context
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/guardias",
        json={
            "asignacion_id": ctx["asignacion_id"],
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "dia": "Martes",
            "horario": "10:00-12:00",
        },
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["estado"] == "Pendiente"  # default


@pytest.mark.asyncio
async def test_registrar_guardia_sin_permiso_403(
    client: AsyncClient, setup_guardia_context: dict
):
    """8.6: User without guardias:registrar gets 403."""
    from app.core.security import create_access_token

    alumno_token = create_access_token(
        sub="alumno-uuid", tenant_id="tenant-a", roles=["ALUMNO"]
    )
    ctx = setup_guardia_context
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/guardias",
        json={
            "asignacion_id": ctx["asignacion_id"],
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "dia": "Lunes",
            "horario": "14:00",
        },
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 403


# ── Task 8.7: Guardia queries ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_listar_guardias_por_materia_200(
    client: AsyncClient, admin_token: str, setup_guardia_context: dict
):
    """8.7: List guardias by materia returns only matching records."""
    ctx = setup_guardia_context
    # Create a guardia
    await client.post(
        f"/api/materias/{ctx['materia_id']}/guardias",
        json={
            "asignacion_id": ctx["asignacion_id"],
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "dia": "Lunes",
            "horario": "14:00-16:00",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/guardias",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_listar_guardias_filtro_estado_200(
    client: AsyncClient, admin_token: str, setup_guardia_context: dict
):
    """8.7: Filter guardias by estado returns filtered results."""
    ctx = setup_guardia_context
    # Create a guardia
    await client.post(
        f"/api/materias/{ctx['materia_id']}/guardias",
        json={
            "asignacion_id": ctx["asignacion_id"],
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "dia": "Lunes",
            "horario": "14:00-16:00",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.get(
        f"/api/materias/{ctx['materia_id']}/guardias?estado=Pendiente",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["estado"] == "Pendiente"


@pytest.mark.asyncio
async def test_listar_guardias_tenant_isolation(
    client: AsyncClient, setup_guardia_context: dict
):
    """8.7: Tenant B cannot see Tenant A's guardias."""
    from app.core.security import create_access_token

    ctx = setup_guardia_context
    token_a = create_access_token(
        sub="admin-a", tenant_id="tenant-a", roles=["ADMIN"]
    )
    token_b = create_access_token(
        sub="admin-b", tenant_id="tenant-b", roles=["ADMIN"]
    )

    # Create guardia in tenant A
    await client.post(
        f"/api/materias/{ctx['materia_id']}/guardias",
        json={
            "asignacion_id": ctx["asignacion_id"],
            "materia_id": ctx["materia_id"],
            "carrera_id": ctx["carrera_id"],
            "cohorte_id": ctx["cohorte_id"],
            "dia": "Lunes",
            "horario": "14:00-16:00",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # List from tenant B
    resp_b = await client.get(
        f"/api/materias/{ctx['materia_id']}/guardias",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200
    data = resp_b.json()
    assert data["total"] == 0


# ── Unauthenticated ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_401(client: AsyncClient):
    """Requests without JWT return 401 on guardia endpoints."""
    endpoints = [
        ("POST", "/api/materias/some-id/guardias"),
        ("GET", "/api/materias/some-id/guardias"),
    ]
    for method, path in endpoints:
        response = await client.request(method, path)
        assert response.status_code == 401, f"{method} {path} returned {response.status_code}"
