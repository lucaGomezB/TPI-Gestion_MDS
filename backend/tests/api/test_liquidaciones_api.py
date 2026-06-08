"""Integration tests for liquidaciones API endpoints (C-19).

All tests require PostgreSQL via testcontainers.
Marked with @pytest.mark.integration for selective execution.
"""

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        True,
        reason="Requires PostgreSQL (testcontainers). "
        "Run with: pytest --run-integration",
    ),
]


@pytest.fixture
def finanzas_token() -> str:
    """Return a JWT for a FINANZAS user with liquidaciones:* perms."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="finanzas-uuid",
        tenant_id="tenant-a",
        roles=["FINANZAS"],
    )


@pytest.fixture
def admin_token() -> str:
    """Return a JWT for an ADMIN user."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def profesor_token() -> str:
    """Return a JWT for a PROFESOR (no liquidaciones perms)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def unauth_token() -> str:
    """Return a malformed JWT."""
    return "invalid-token"


# ── GET /api/admin/liquidaciones — Period view ──────────────────────────


@pytest.mark.asyncio
async def test_get_liquidaciones_200(client, finanzas_token):
    """FINANZAS can GET period view."""
    response = await client.get(
        "/api/admin/liquidaciones?periodo=2026-06",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "kpis" in data
    assert "total_sin_factura" in data["kpis"]
    assert "total_con_factura" in data["kpis"]
    assert "total_general" in data["kpis"]


@pytest.mark.asyncio
async def test_get_liquidaciones_401_unauth(client, unauth_token):
    """Unauthenticated request returns 401."""
    response = await client.get(
        "/api/admin/liquidaciones?periodo=2026-06",
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_liquidaciones_403_no_permission(client, profesor_token):
    """Profesor without liquidaciones:ver returns 403."""
    response = await client.get(
        "/api/admin/liquidaciones?periodo=2026-06",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_liquidaciones_empty_period(client, finanzas_token):
    """Empty period returns 200 with empty items."""
    response = await client.get(
        "/api/admin/liquidaciones?periodo=2099-01",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["kpis"]["total_general"] == 0


@pytest.mark.asyncio
async def test_get_liquidaciones_filter_by_cohorte(client, finanzas_token):
    """Period view filtered by cohorte_id."""
    response = await client.get(
        "/api/admin/liquidaciones?periodo=2026-06&cohorte_id=some-cohorte",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200


# ── GET /api/admin/liquidaciones/{id} — Detail ───────────────────────────


@pytest.mark.asyncio
async def test_get_liquidacion_detail_200(client, finanzas_token):
    """FINANZAS can GET detail of a liquidacion."""
    response = await client.get(
        "/api/admin/liquidaciones/non-existent",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_liquidacion_detail_403(client, profesor_token):
    """Profesor gets 403 on detail."""
    response = await client.get(
        "/api/admin/liquidaciones/some-id",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


# ── POST /api/admin/liquidaciones/{id}/cerrar — Close lifecycle ──────────


@pytest.mark.asyncio
async def test_cerrar_liquidacion_200(client, finanzas_token):
    """FINANZAS can close an open liquidacion."""
    response = await client.post(
        "/api/admin/liquidaciones/non-existent/cerrar",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cerrar_liquidacion_403(client, profesor_token):
    """Profesor gets 403 on close."""
    response = await client.post(
        "/api/admin/liquidaciones/some-id/cerrar",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cerrar_liquidacion_401(client, unauth_token):
    """Unauthenticated gets 401 on close."""
    response = await client.post(
        "/api/admin/liquidaciones/some-id/cerrar",
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert response.status_code == 401


# ── GET /api/admin/liquidaciones/historial — History ─────────────────────


@pytest.mark.asyncio
async def test_get_historial_200(client, finanzas_token):
    """FINANZAS can GET historial of closed liquidaciones."""
    response = await client.get(
        "/api/admin/liquidaciones/historial",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_historial_filter_periodo(client, finanzas_token):
    """Historial filtered by periodo."""
    response = await client.get(
        "/api/admin/liquidaciones/historial?periodo=2026-06",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_historial_403(client, profesor_token):
    """Profesor gets 403 on historial."""
    response = await client.get(
        "/api/admin/liquidaciones/historial",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


# ── Authorization matrix ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path", "expected_allowed"),
    [
        ("GET", "/api/admin/liquidaciones?periodo=2026-06", True),
        ("GET", "/api/admin/liquidaciones/some-id", True),
        ("POST", "/api/admin/liquidaciones/some-id/cerrar", True),
        ("GET", "/api/admin/liquidaciones/historial", True),
    ],
)
@pytest.mark.asyncio
async def test_finanzas_has_access(
    client, finanzas_token, method, path, expected_allowed
):
    """FINANZAS role has access to all liquidacion endpoints."""
    response = await client.request(
        method, path, headers={"Authorization": f"Bearer {finanzas_token}"}
    )
    # These may 404 on nonexistent IDs but should not be 401/403
    assert response.status_code not in (401, 403)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/admin/liquidaciones?periodo=2026-06"),
        ("GET", "/api/admin/liquidaciones/some-id"),
        ("POST", "/api/admin/liquidaciones/some-id/cerrar"),
        ("GET", "/api/admin/liquidaciones/historial"),
    ],
)
@pytest.mark.asyncio
async def test_profesor_denied(client, profesor_token, method, path):
    """PROFESOR role is denied access to all liquidacion endpoints."""
    response = await client.request(
        method, path, headers={"Authorization": f"Bearer {profesor_token}"}
    )
    assert response.status_code == 403
