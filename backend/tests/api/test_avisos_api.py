"""Integration tests for avisos API endpoints (C-12).

All tests require PostgreSQL via testcontainers.
Marked with @pytest.mark.integration for selective execution.
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


# ── Token fixtures ──────────────────────────────────────────────────────


@pytest.fixture
def admin_token() -> str:
    """JWT for ADMIN user with avisos:publicar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def coordinador_token() -> str:
    """JWT for COORDINADOR user with avisos:publicar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="coord-uuid",
        tenant_id="tenant-a",
        roles=["COORDINADOR"],
    )


@pytest.fixture
def profesor_token() -> str:
    """JWT for PROFESOR user (NO avisos:publicar)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def otro_tenant_token() -> str:
    """JWT for ADMIN of a different tenant."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="other-admin-uuid",
        tenant_id="tenant-b",
        roles=["ADMIN"],
    )


@pytest.fixture
def alumno_token() -> str:
    """JWT for ALUMNO user (can view avisos and ack)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="alumno-uuid",
        tenant_id="tenant-a",
        roles=["ALUMNO"],
    )


# ── Seed fixtures ───────────────────────────────────────────────────────


@pytest.fixture
async def seed_aviso(db_session: AsyncSession) -> str:
    """Create a test aviso and return its ID."""
    from app.models.aviso import Aviso
    from datetime import datetime, timezone, timedelta

    aviso = Aviso(
        tenant_id="tenant-a",
        titulo="Aviso de prueba",
        cuerpo="Contenido del aviso",
        alcance="Global",
        severidad="Info",
        inicio_en=datetime.now(timezone.utc) - timedelta(days=1),
        fin_en=datetime.now(timezone.utc) + timedelta(days=30),
        orden=1,
        activo=True,
        requiere_ack=False,
    )
    db_session.add(aviso)
    await db_session.flush()
    return aviso.id


@pytest.fixture
async def seed_aviso_requiere_ack(db_session: AsyncSession) -> str:
    """Create a test aviso that requires acknowledgment."""
    from app.models.aviso import Aviso
    from datetime import datetime, timezone, timedelta

    aviso = Aviso(
        tenant_id="tenant-a",
        titulo="Aviso con ack",
        cuerpo="Requiere confirmacion",
        alcance="Global",
        severidad="Alta",
        inicio_en=datetime.now(timezone.utc) - timedelta(days=1),
        fin_en=datetime.now(timezone.utc) + timedelta(days=30),
        orden=2,
        activo=True,
        requiere_ack=True,
    )
    db_session.add(aviso)
    await db_session.flush()
    return aviso.id


# ── 5.2 Tests: CRUD admin ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_create_aviso(
    client: AsyncClient,
    admin_token: str,
):
    """POST /api/admin/avisos creates a new aviso (201)."""
    response = await client.post(
        "/api/admin/avisos",
        json={
            "titulo": "Nuevo aviso",
            "cuerpo": "Contenido importante",
            "alcance": "Global",
            "severidad": "Info",
            "inicio_en": "2026-01-01T00:00:00Z",
            "fin_en": "2026-12-31T23:59:59Z",
            "orden": 1,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Nuevo aviso"
    assert "id" in data
    assert data["activo"] is True


@pytest.mark.asyncio
async def test_admin_create_aviso_422_missing_fields(
    client: AsyncClient,
    admin_token: str,
):
    """POST /api/admin/avisos without required fields returns 422."""
    response = await client.post(
        "/api/admin/avisos",
        json={"titulo": "Incompleto"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_create_aviso_422_alcance_context(
    client: AsyncClient,
    admin_token: str,
):
    """POST /api/admin/avisos with PorMateria but no materia_id returns 422."""
    response = await client.post(
        "/api/admin/avisos",
        json={
            "titulo": "Sin materia",
            "cuerpo": "Test",
            "alcance": "PorMateria",
            "severidad": "Info",
            "inicio_en": "2026-01-01T00:00:00Z",
            "fin_en": "2026-12-31T23:59:59Z",
            "orden": 1,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_create_aviso_422_vigencia(
    client: AsyncClient,
    admin_token: str,
):
    """POST /api/admin/avisos with inicio > fin returns 422."""
    response = await client.post(
        "/api/admin/avisos",
        json={
            "titulo": "Mal rango",
            "cuerpo": "Test",
            "alcance": "Global",
            "severidad": "Info",
            "inicio_en": "2026-12-31T00:00:00Z",
            "fin_en": "2026-01-01T00:00:00Z",
            "orden": 1,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_list_avisos(
    client: AsyncClient,
    admin_token: str,
    seed_aviso: str,
):
    """GET /api/admin/avisos returns avisos list (200)."""
    response = await client.get(
        "/api/admin/avisos",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_admin_list_avisos_with_filters(
    client: AsyncClient,
    admin_token: str,
    seed_aviso: str,
):
    """GET /api/admin/avisos?activo=true filters results."""
    response = await client.get(
        "/api/admin/avisos?activo=true",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["activo"] is True for item in data["items"])


@pytest.mark.asyncio
async def test_admin_get_aviso_detail(
    client: AsyncClient,
    admin_token: str,
    seed_aviso: str,
):
    """GET /api/admin/avisos/{id} returns aviso detail (200)."""
    response = await client.get(
        f"/api/admin/avisos/{seed_aviso}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["id"] == seed_aviso


@pytest.mark.asyncio
async def test_admin_get_aviso_404(
    client: AsyncClient,
    admin_token: str,
):
    """GET /api/admin/avisos/nonexistent returns 404."""
    response = await client.get(
        "/api/admin/avisos/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_update_aviso(
    client: AsyncClient,
    admin_token: str,
    seed_aviso: str,
):
    """PUT /api/admin/avisos/{id} updates aviso (200)."""
    response = await client.put(
        f"/api/admin/avisos/{seed_aviso}",
        json={"titulo": "Titulo actualizado"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["titulo"] == "Titulo actualizado"


@pytest.mark.asyncio
async def test_admin_deactivate_aviso(
    client: AsyncClient,
    admin_token: str,
    seed_aviso: str,
):
    """DELETE /api/admin/avisos/{id} deactivates aviso (204)."""
    response = await client.delete(
        f"/api/admin/avisos/{seed_aviso}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_admin_403_without_permission(
    client: AsyncClient,
    profesor_token: str,
):
    """Admin endpoints return 403 for users without avisos:publicar."""
    response = await client.post(
        "/api/admin/avisos",
        json={
            "titulo": "Test",
            "cuerpo": "Test",
            "alcance": "Global",
            "severidad": "Info",
            "inicio_en": "2026-01-01T00:00:00Z",
            "fin_en": "2026-12-31T23:59:59Z",
            "orden": 1,
        },
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


# ── 5.3 Tests: visualizacion ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_public_list_avisos(
    client: AsyncClient,
    alumno_token: str,
    seed_aviso: str,
):
    """GET /api/avisos returns visible avisos (200)."""
    response = await client.get(
        "/api/avisos",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_public_list_only_active_in_vigencia(
    client: AsyncClient,
    alumno_token: str,
    db_session: AsyncSession,
):
    """GET /api/avisos returns only avisos within vigencia window (RN-18)."""
    from app.models.aviso import Aviso
    from datetime import datetime, timezone, timedelta

    # Create a future aviso (should NOT appear)
    future = Aviso(
        tenant_id="tenant-a",
        titulo="Futuro",
        cuerpo="No visible",
        alcance="Global",
        severidad="Info",
        inicio_en=datetime.now(timezone.utc) + timedelta(days=10),
        fin_en=datetime.now(timezone.utc) + timedelta(days=20),
        orden=1,
        activo=True,
    )
    db_session.add(future)
    # Create a past aviso (should NOT appear)
    past = Aviso(
        tenant_id="tenant-a",
        titulo="Pasado",
        cuerpo="No visible",
        alcance="Global",
        severidad="Info",
        inicio_en=datetime.now(timezone.utc) - timedelta(days=20),
        fin_en=datetime.now(timezone.utc) - timedelta(days=10),
        orden=2,
        activo=True,
    )
    db_session.add(past)
    await db_session.flush()

    response = await client.get(
        "/api/avisos",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    aviso_ids = [a["id"] for a in data]
    assert future.id not in aviso_ids
    assert past.id not in aviso_ids


@pytest.mark.asyncio
async def test_public_list_empty_when_no_visible(
    client: AsyncClient,
    otro_tenant_token: str,
):
    """GET /api/avisos returns empty list when no avisos for tenant."""
    response = await client.get(
        "/api/avisos",
        headers={"Authorization": f"Bearer {otro_tenant_token}"},
    )
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_public_list_filter_by_severidad(
    client: AsyncClient,
    alumno_token: str,
    db_session: AsyncSession,
):
    """GET /api/avisos?severidad=Critico filters by severity."""
    from app.models.aviso import Aviso
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    # Create critico aviso
    critico = Aviso(
        tenant_id="tenant-a",
        titulo="Critico",
        cuerpo="Urgente",
        alcance="Global",
        severidad="Critico",
        inicio_en=now - timedelta(days=1),
        fin_en=now + timedelta(days=30),
        orden=1,
        activo=True,
    )
    db_session.add(critico)
    # Create baja aviso
    baja = Aviso(
        tenant_id="tenant-a",
        titulo="Baja",
        cuerpo="Normal",
        alcance="Global",
        severidad="Baja",
        inicio_en=now - timedelta(days=1),
        fin_en=now + timedelta(days=30),
        orden=2,
        activo=True,
    )
    db_session.add(baja)
    await db_session.flush()

    response = await client.get(
        "/api/avisos?severidad=Critico",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for aviso in data:
        assert aviso["severidad"] == "Critico"


# ── 5.4 Tests: acknowledgment ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ack_success(
    client: AsyncClient,
    alumno_token: str,
    seed_aviso_requiere_ack: str,
):
    """POST /api/avisos/{id}/ack confirms reading (200)."""
    response = await client.post(
        f"/api/avisos/{seed_aviso_requiere_ack}/ack",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["acknowledged"] is True
    assert "leido_en" in data


@pytest.mark.asyncio
async def test_ack_idempotent(
    client: AsyncClient,
    alumno_token: str,
    seed_aviso_requiere_ack: str,
):
    """POST /api/avisos/{id}/ack twice returns same result (idempotent)."""
    first = await client.post(
        f"/api/avisos/{seed_aviso_requiere_ack}/ack",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert first.status_code == 200

    second = await client.post(
        f"/api/avisos/{seed_aviso_requiere_ack}/ack",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert second.status_code == 200
    assert second.json()["acknowledged"] is True


@pytest.mark.asyncio
async def test_ack_rejected_no_requiere_ack(
    client: AsyncClient,
    alumno_token: str,
    seed_aviso: str,
):
    """POST /api/avisos/{id}/ack for aviso without requiere_ack returns 400."""
    response = await client.post(
        f"/api/avisos/{seed_aviso}/ack",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_ack_404_nonexistent(
    client: AsyncClient,
    alumno_token: str,
):
    """POST /api/avisos/nonexistent/ack returns 404."""
    response = await client.post(
        "/api/avisos/00000000-0000-0000-0000-000000000000/ack",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 404


# ── 5.5 Tests: multi-tenant isolation ────────────────────────────────────


@pytest.mark.asyncio
async def test_multi_tenant_admin_list(
    client: AsyncClient,
    admin_token: str,
    otro_tenant_token: str,
    seed_aviso: str,
):
    """Tenant B admin should not see Tenant A's avisos in admin list."""
    response = await client.get(
        "/api/admin/avisos",
        headers={"Authorization": f"Bearer {otro_tenant_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    aviso_ids = [a["id"] for a in data["items"]]
    assert seed_aviso not in aviso_ids


@pytest.mark.asyncio
async def test_multi_tenant_admin_get(
    client: AsyncClient,
    otro_tenant_token: str,
    seed_aviso: str,
):
    """Tenant B admin cannot access Tenant A's aviso by id (404)."""
    response = await client.get(
        f"/api/admin/avisos/{seed_aviso}",
        headers={"Authorization": f"Bearer {otro_tenant_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_multi_tenant_public_list(
    client: AsyncClient,
    otro_tenant_token: str,
    seed_aviso: str,
):
    """Tenant B user should not see Tenant A's avisos."""
    response = await client.get(
        "/api/avisos",
        headers={"Authorization": f"Bearer {otro_tenant_token}"},
    )
    assert response.status_code == 200
    aviso_ids = [a["id"] for a in response.json()]
    assert seed_aviso not in aviso_ids


@pytest.mark.asyncio
async def test_multi_tenant_ack_404(
    client: AsyncClient,
    otro_tenant_token: str,
    seed_aviso_requiere_ack: str,
):
    """Tenant B user cannot ack Tenant A's aviso (404)."""
    response = await client.post(
        f"/api/avisos/{seed_aviso_requiere_ack}/ack",
        headers={"Authorization": f"Bearer {otro_tenant_token}"},
    )
    assert response.status_code == 404


# ── Unauthenticated (401) ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_admin_list_401(client: AsyncClient):
    """Admin endpoints without auth return 401."""
    response = await client.get("/api/admin/avisos")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_public_list_401(client: AsyncClient):
    """Public avisos endpoint without auth returns 401."""
    response = await client.get("/api/avisos")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_ack_401(client: AsyncClient):
    """Ack endpoint without auth returns 401."""
    response = await client.post(
        "/api/avisos/fake-id/ack",
    )
    assert response.status_code == 401
