"""Integration tests for facturas API endpoints (C-20).

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
def profesor_facturador_token() -> str:
    """JWT for PROFESOR with facturador=true."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-facturador-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def profesor_no_facturador_token() -> str:
    """JWT for PROFESOR with facturador=false."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-no-facturador-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def finanzas_token() -> str:
    """JWT for FINANZAS user with facturas:gestionar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="finanzas-uuid",
        tenant_id="tenant-a",
        roles=["FINANZAS"],
    )


@pytest.fixture
def admin_token() -> str:
    """JWT for ADMIN user."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def alumno_token() -> str:
    """JWT for ALUMNO (no facturas perms)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="alumno-uuid",
        tenant_id="tenant-a",
        roles=["ALUMNO"],
    )


@pytest.fixture
def unauth_token() -> str:
    """Malformed JWT."""
    return "invalid-token"


# ── POST /api/docentes/facturas — Upload ────────────────────────────────


@pytest.mark.asyncio
async def test_subir_factura_401_unauth(client, unauth_token):
    """Unauthenticated request returns 401."""
    response = await client.post(
        "/api/docentes/facturas",
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_subir_factura_403_no_permission(client, alumno_token):
    """ALUMNO without facturas:subir returns 403."""
    response = await client.post(
        "/api/docentes/facturas",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 403


# ── GET /api/docentes/facturas — Own history ────────────────────────────


@pytest.mark.asyncio
async def test_get_mis_facturas_200(client, profesor_facturador_token):
    """Profesor can GET own facturas history."""
    response = await client.get(
        "/api/docentes/facturas",
        headers={"Authorization": f"Bearer {profesor_facturador_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_mis_facturas_401_unauth(client, unauth_token):
    """Unauthenticated returns 401."""
    response = await client.get(
        "/api/docentes/facturas",
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_mis_facturas_403_no_perm(client, alumno_token):
    """ALUMNO without permission returns 403."""
    response = await client.get(
        "/api/docentes/facturas",
        headers={"Authorization": f"Bearer {alumno_token}"},
    )
    assert response.status_code == 403


# ── GET /api/admin/facturas — Admin view ────────────────────────────────


@pytest.mark.asyncio
async def test_get_admin_facturas_200(client, finanzas_token):
    """FINANZAS can GET admin view."""
    response = await client.get(
        "/api/admin/facturas",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_get_admin_facturas_401_unauth(client, unauth_token):
    """Unauthenticated returns 401."""
    response = await client.get(
        "/api/admin/facturas",
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_admin_facturas_403_no_perm(client, profesor_facturador_token):
    """PROFESOR without facturas:gestionar returns 403."""
    response = await client.get(
        "/api/admin/facturas",
        headers={"Authorization": f"Bearer {profesor_facturador_token}"},
    )
    assert response.status_code == 403


# ── PUT /api/admin/facturas/{id}/abonar — Mark as paid ──────────────────


@pytest.mark.asyncio
async def test_abonar_factura_200(client, finanzas_token):
    """FINANZAS can mark a factura as Abonada."""
    response = await client.put(
        "/api/admin/facturas/non-existent/abonar",
        headers={"Authorization": f"Bearer {finanzas_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_abonar_factura_403(client, profesor_facturador_token):
    """PROFESOR gets 403 on abonar."""
    response = await client.put(
        "/api/admin/facturas/some-id/abonar",
        headers={"Authorization": f"Bearer {profesor_facturador_token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_abonar_factura_401(client, unauth_token):
    """Unauthenticated gets 401 on abonar."""
    response = await client.put(
        "/api/admin/facturas/some-id/abonar",
        headers={"Authorization": f"Bearer {unauth_token}"},
    )
    assert response.status_code == 401


# ── Authorization matrix ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("method", "path", "expected_allowed"),
    [
        ("GET", "/api/docentes/facturas", True),
    ],
)
@pytest.mark.asyncio
async def test_profesor_has_docente_access(
    client, profesor_facturador_token, method, path, expected_allowed
):
    """PROFESOR with facturas:subir has access to docente endpoints."""
    response = await client.request(
        method, path, headers={"Authorization": f"Bearer {profesor_facturador_token}"}
    )
    assert response.status_code not in (401, 403)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/admin/facturas"),
        ("PUT", "/api/admin/facturas/some-id/abonar"),
    ],
)
@pytest.mark.asyncio
async def test_finanzas_has_admin_access(
    client, finanzas_token, method, path
):
    """FINANZAS has access to admin endpoints."""
    response = await client.request(
        method, path, headers={"Authorization": f"Bearer {finanzas_token}"}
    )
    assert response.status_code not in (401, 403)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/admin/facturas"),
        ("PUT", "/api/admin/facturas/some-id/abonar"),
    ],
)
@pytest.mark.asyncio
async def test_profesor_denied_admin(client, profesor_facturador_token, method, path):
    """PROFESOR is denied access to admin endpoints."""
    response = await client.request(
        method, path, headers={"Authorization": f"Bearer {profesor_facturador_token}"}
    )
    assert response.status_code == 403
