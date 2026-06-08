"""Integration tests for encuentro API endpoints (C-14, F6.1–F6.5).

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
    """Return a JWT for a PROFESOR (encuentros:crear, encuentros:editar)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def coordinador_token() -> str:
    """Return a JWT for a COORDINADOR."""
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
    """Create academic entities needed for encuentro tests.

    Returns:
        Dict with ids: materia_id, asignacion_id.
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


# ── Task 8.1: Slot recurrente creation ────────────────────────────────────────


@pytest.mark.asyncio
async def test_crear_slot_recurrente_201(
    client: AsyncClient, profesor_token: str, setup_academic_context: dict
):
    """8.1: Create recurrent slot returns 201 with slot + generated instances."""
    ctx = setup_academic_context
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/encuentros/slot",
        json={
            "asignacion_id": ctx["asignacion_id"],
            "materia_id": ctx["materia_id"],
            "titulo": "Clase Semanal",
            "hora": "10:00",
            "dia_semana": "Lunes",
            "fecha_inicio": "2026-03-02",
            "cant_semanas": 4,
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "slot" in data
    assert "instancias" in data
    assert data["total_instancias"] == 4
    assert data["slot"]["titulo"] == "Clase Semanal"


@pytest.mark.asyncio
async def test_crear_slot_sin_permiso_403(
    client: AsyncClient, setup_academic_context: dict
):
    """8.1: User without encuentros:crear gets 403."""
    from app.core.security import create_access_token

    alumno_token = create_access_token(
        sub="alumno-uuid", tenant_id="tenant-a", roles=["ALUMNO"]
    )
    ctx = setup_academic_context
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/encuentros/slot",
        json={
            "asignacion_id": ctx["asignacion_id"],
            "materia_id": ctx["materia_id"],
            "titulo": "Clase",
            "hora": "10:00",
            "dia_semana": "Lunes",
            "fecha_inicio": "2026-03-02",
            "vig_desde": "2026-03-01",
        },
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 403


# ── Task 8.2: Encuentro unico creation ────────────────────────────────────────


@pytest.mark.asyncio
async def test_crear_encuentro_unico_201(
    client: AsyncClient, profesor_token: str, setup_academic_context: dict
):
    """8.2: Create single encuentro without slot returns 201."""
    ctx = setup_academic_context
    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/encuentros/unico",
        json={
            "materia_id": ctx["materia_id"],
            "fecha": "2026-06-15",
            "hora": "14:00",
            "titulo": "Clase Extraordinaria",
        },
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Clase Extraordinaria"
    assert data["slot_id"] is None
    assert "id" in data


# ── Task 8.3: Instancia edicion ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_editar_instancia_estado_200(
    client: AsyncClient, profesor_token: str, setup_academic_context: dict
):
    """8.3: Update instance estado to Realizado returns 200."""
    ctx = setup_academic_context
    # Create instance first
    resp = await client.post(
        f"/api/materias/{ctx['materia_id']}/encuentros/unico",
        json={
            "materia_id": ctx["materia_id"],
            "fecha": "2026-06-15",
            "hora": "14:00",
            "titulo": "Test",
        },
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    instance_id = resp.json()["id"]

    # Update estado
    response = await client.put(
        f"/api/encuentros/{instance_id}",
        json={"estado": "Realizado"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "Realizado"


@pytest.mark.asyncio
async def test_editar_instancia_video_url_200(
    client: AsyncClient, profesor_token: str, setup_academic_context: dict
):
    """8.3: Update instance video_url returns 200."""
    ctx = setup_academic_context
    resp = await client.post(
        f"/api/materias/{ctx['materia_id']}/encuentros/unico",
        json={
            "materia_id": ctx["materia_id"],
            "fecha": "2026-06-15",
            "hora": "14:00",
            "titulo": "Test",
        },
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    instance_id = resp.json()["id"]

    response = await client.put(
        f"/api/encuentros/{instance_id}",
        json={"video_url": "https://vimeo.com/123456"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 200
    assert response.json()["video_url"] == "https://vimeo.com/123456"


@pytest.mark.asyncio
async def test_editar_instancia_404(
    client: AsyncClient, profesor_token: str
):
    """8.3: Updating non-existent instance returns 404."""
    response = await client.put(
        "/api/encuentros/nonexistent-id",
        json={"estado": "Realizado"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 404


# ── Task 8.4: Embed generation ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generar_embed_html_200(
    client: AsyncClient, coordinador_token: str, setup_academic_context: dict
):
    """8.4: Embed generation returns HTML and Markdown."""
    ctx = setup_academic_context
    # Create an instance first
    await client.post(
        f"/api/materias/{ctx['materia_id']}/encuentros/unico",
        json={
            "materia_id": ctx["materia_id"],
            "fecha": "2026-06-15",
            "hora": "14:00",
            "titulo": "Clase Test",
        },
        headers={"Authorization": f"Bearer {coordinador_token}"},
    )

    response = await client.post(
        f"/api/materias/{ctx['materia_id']}/encuentros/embed",
        headers={"Authorization": f"Bearer {coordinador_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "html" in data
    assert "markdown" in data
    assert data["total"] >= 1
    assert "<table>" in data["html"] or "No hay encuentros" in data["html"]


@pytest.mark.asyncio
async def test_generar_embed_empty_200(
    client: AsyncClient, coordinador_token: str, setup_academic_context: dict
):
    """8.4: Embed for materia without instances returns empty."""
    # Create a materia with no instances
    resp_m = await client.post(
        "/api/admin/materias",
        json={"codigo": "EMPTY", "nombre": "Sin instancias"},
        headers={"Authorization": f"Bearer {coordinador_token}"},
    )
    empty_materia_id = resp_m.json()["id"]

    response = await client.post(
        f"/api/materias/{empty_materia_id}/encuentros/embed",
        headers={"Authorization": f"Bearer {coordinador_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert "No hay encuentros" in data["html"]


# ── Task 8.5: Vista transversal ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_vista_transversal_coordinador_200(
    client: AsyncClient, coordinador_token: str, setup_academic_context: dict
):
    """8.5: COORDINADOR can access vista transversal."""
    response = await client.get(
        "/api/admin/encuentros",
        headers={"Authorization": f"Bearer {coordinador_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "instancias" in data


@pytest.mark.asyncio
async def test_vista_transversal_admin_200(
    client: AsyncClient, admin_token: str
):
    """8.5: ADMIN can access vista transversal."""
    response = await client.get(
        "/api/admin/encuentros",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_vista_transversal_forbidden_role_403(
    client: AsyncClient
):
    """8.5: PROFESOR cannot access vista transversal."""
    from app.core.security import create_access_token

    token = create_access_token(
        sub="profesor-uuid", tenant_id="tenant-a", roles=["PROFESOR"]
    )
    response = await client.get(
        "/api/admin/encuentros",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


# ── Unauthenticated ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_401(client: AsyncClient):
    """Requests without JWT return 401 on all encuentro endpoints."""
    endpoints = [
        ("POST", "/api/materias/some-id/encuentros/slot"),
        ("POST", "/api/materias/some-id/encuentros/unico"),
        ("PUT", "/api/encuentros/some-id"),
        ("POST", "/api/materias/some-id/encuentros/embed"),
        ("GET", "/api/admin/encuentros"),
    ]
    for method, path in endpoints:
        response = await client.request(method, path)
        assert response.status_code == 401, f"{method} {path} returned {response.status_code}"
