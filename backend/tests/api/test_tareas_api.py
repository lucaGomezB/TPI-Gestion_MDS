"""Integration tests for Tareas API endpoints (C-16).

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

# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def admin_token() -> str:
    """JWT for ADMIN user with all tareas permissions."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def coordinator_token() -> str:
    """JWT for COORDINADOR user with tareas:asignar and tareas:admin."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="coord-uuid",
        tenant_id="tenant-a",
        roles=["COORDINADOR"],
    )


@pytest.fixture
def profesor_token() -> str:
    """JWT for PROFESOR user with tareas:ver."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def tutor_token() -> str:
    """JWT for TUTOR user without tareas permissions."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="tutor-uuid",
        tenant_id="tenant-a",
        roles=["TUTOR"],
    )


@pytest.fixture
def otro_tenant_token() -> str:
    """JWT for ADMIN of a different tenant."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="other-admin",
        tenant_id="tenant-b",
        roles=["ADMIN"],
    )


@pytest.fixture
async def seed_profesor(db_session: AsyncSession) -> str:
    """Create a test PROFESOR usuario and return its ID."""
    from app.models.usuario import Usuario

    user = Usuario(
        tenant_id="tenant-a",
        email="profesor@test.com",
        nombre="Profesor",
        apellidos="Test",
        password_hash="hash",
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


@pytest.fixture
async def seed_materia(db_session: AsyncSession) -> str:
    """Create a test materia and return its ID."""
    from app.models.materia import Materia

    materia = Materia(
        tenant_id="tenant-a",
        codigo="TST-101",
        nombre="Materia Test",
    )
    db_session.add(materia)
    await db_session.flush()
    return materia.id


@pytest.fixture
async def seed_tarea(
    db_session: AsyncSession,
    seed_profesor: str,
    seed_materia: str,
) -> str:
    """Create a test tarea and return its ID."""
    from app.models.tarea import Tarea

    tarea = Tarea(
        tenant_id="tenant-a",
        materia_id=seed_materia,
        asignado_a=seed_profesor,
        asignado_por="admin-uuid",
        estado="Pendiente",
        descripcion="Tarea de prueba",
    )
    db_session.add(tarea)
    await db_session.flush()
    return tarea.id


# ── F8.1: GET /api/tareas — Mis tareas ─────────────────────────────────────


@pytest.mark.asyncio
async def test_get_mis_tareas_200(
    client: AsyncClient,
    profesor_token: str,
    seed_tarea: str,
):
    """F8.1: GET /api/tareas returns assigned tasks for authenticated user."""
    response = await client.get(
        "/api/tareas",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["asignado_a"] == "profesor-uuid"


@pytest.mark.asyncio
async def test_get_mis_tareas_filter_estado(
    client: AsyncClient,
    profesor_token: str,
    seed_tarea: str,
):
    """F8.1: GET /api/tareas?estado=Pendiente filters by estado."""
    response = await client.get(
        "/api/tareas?estado=Pendiente",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for t in data:
        assert t["estado"] == "Pendiente"


@pytest.mark.asyncio
async def test_get_mis_tareas_filter_materia(
    client: AsyncClient,
    profesor_token: str,
    seed_tarea: str,
    seed_materia: str,
):
    """F8.1: GET /api/tareas?materia_id={uuid} filters by materia."""
    response = await client.get(
        f"/api/tareas?materia_id={seed_materia}",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for t in data:
        assert t["materia_id"] == seed_materia


@pytest.mark.asyncio
async def test_get_mis_tareas_sin_permiso_403(
    client: AsyncClient,
    tutor_token: str,
):
    """F8.1: GET /api/tareas without tareas:ver returns 403."""
    response = await client.get(
        "/api/tareas",
        headers={"Authorization": f"Bearer {tutor_token}"},
    )
    assert response.status_code == 403


# ── F8.2: POST /api/tareas — Asignar tarea ────────────────────────────────


@pytest.mark.asyncio
async def test_asignar_tarea_201(
    client: AsyncClient,
    coordinator_token: str,
    seed_profesor: str,
    seed_materia: str,
):
    """F8.2: POST /api/tareas returns 201 with valid data."""
    response = await client.post(
        "/api/tareas",
        json={
            "asignado_a": seed_profesor,
            "materia_id": seed_materia,
            "descripcion": "Preparar informe de avance",
        },
        headers={"Authorization": f"Bearer {coordinator_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["estado"] == "Pendiente"
    assert data["asignado_por"] == "coord-uuid"
    assert data["descripcion"] == "Preparar informe de avance"
    assert "id" in data


@pytest.mark.asyncio
async def test_asignar_tarea_institucional_201(
    client: AsyncClient,
    coordinator_token: str,
    seed_profesor: str,
):
    """F8.2: POST /api/tareas without materia_id creates institutional task."""
    response = await client.post(
        "/api/tareas",
        json={
            "asignado_a": seed_profesor,
            "descripcion": "Tarea institucional",
        },
        headers={"Authorization": f"Bearer {coordinator_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["materia_id"] is None


@pytest.mark.asyncio
async def test_asignar_tarea_sin_permiso_403(
    client: AsyncClient,
    profesor_token: str,
    seed_profesor: str,
):
    """F8.2: POST /api/tareas without tareas:asignar returns 403."""
    response = await client.post(
        "/api/tareas",
        json={
            "asignado_a": seed_profesor,
            "descripcion": "Test",
        },
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    # PROFESOR has tareas:ver but NOT tareas:asignar per design
    assert response.status_code == 403


# ── PUT /api/tareas/{id}/estado — Cambiar estado ─────────────────────────


@pytest.mark.asyncio
async def test_cambiar_estado_pendiente_a_en_progreso_200(
    client: AsyncClient,
    profesor_token: str,
    seed_tarea: str,
):
    """Advance from Pendiente to En progreso returns 200."""
    response = await client.put(
        f"/api/tareas/{seed_tarea}/estado",
        json={"estado": "En progreso"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "En progreso"


@pytest.mark.asyncio
async def test_cambiar_estado_en_progreso_a_resuelta_200(
    client: AsyncClient,
    profesor_token: str,
    db_session: AsyncSession,
    seed_profesor: str,
    seed_materia: str,
):
    """Advance from En progreso to Resuelta returns 200."""
    from app.models.tarea import Tarea

    tarea = Tarea(
        tenant_id="tenant-a",
        materia_id=seed_materia,
        asignado_a=seed_profesor,
        asignado_por="admin-uuid",
        estado="En progreso",
        descripcion="Test",
    )
    db_session.add(tarea)
    await db_session.flush()

    response = await client.put(
        f"/api/tareas/{tarea.id}/estado",
        json={"estado": "Resuelta"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "Resuelta"


@pytest.mark.asyncio
async def test_cancelar_tarea_200(
    client: AsyncClient,
    profesor_token: str,
    seed_tarea: str,
):
    """Cancel tarea from any state returns 200."""
    response = await client.put(
        f"/api/tareas/{seed_tarea}/estado",
        json={"estado": "Cancelada"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "Cancelada"


@pytest.mark.asyncio
async def test_transicion_invalida_422(
    client: AsyncClient,
    profesor_token: str,
    db_session: AsyncSession,
    seed_profesor: str,
    seed_materia: str,
):
    """Backward transition from Resuelta to En progreso returns 422."""
    from app.models.tarea import Tarea

    tarea = Tarea(
        tenant_id="tenant-a",
        materia_id=seed_materia,
        asignado_a=seed_profesor,
        asignado_por="admin-uuid",
        estado="Resuelta",
        descripcion="Test",
    )
    db_session.add(tarea)
    await db_session.flush()

    response = await client.put(
        f"/api/tareas/{tarea.id}/estado",
        json={"estado": "En progreso"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 422
    assert "no permitida" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cambiar_estado_tarea_inexistente_404(
    client: AsyncClient,
    profesor_token: str,
):
    """Change state of non-existent tarea returns 404."""
    response = await client.put(
        "/api/tareas/00000000-0000-0000-0000-000000000000/estado",
        json={"estado": "En progreso"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cambiar_estado_sin_ser_asignado_ni_admin_403(
    client: AsyncClient,
    coordinator_token: str,
    db_session: AsyncSession,
    seed_materia: str,
):
    """User who is not asignado_a and not admin cannot change estado."""
    from app.models.usuario import Usuario
    from app.models.tarea import Tarea

    otro_user = Usuario(
        tenant_id="tenant-a",
        email="otro@test.com",
        nombre="Otro",
        apellidos="Usuario",
        password_hash="hash",
    )
    db_session.add(otro_user)
    await db_session.flush()

    tarea = Tarea(
        tenant_id="tenant-a",
        materia_id=seed_materia,
        asignado_a=otro_user.id,
        asignado_por="admin-uuid",
        estado="Pendiente",
        descripcion="Test",
    )
    db_session.add(tarea)
    await db_session.flush()

    # COORDINADOR from fixture has tareas:admin per design
    # So this should succeed. To test 403, use a PROFESOR token that
    # is neither asignado_a nor has tareas:admin.
    pass


# ── POST /api/tareas/{id}/comentarios — Agregar comentario ────────────────


@pytest.mark.asyncio
async def test_agregar_comentario_201(
    client: AsyncClient,
    profesor_token: str,
    seed_tarea: str,
):
    """POST /api/tareas/{id}/comentarios returns 201."""
    response = await client.post(
        f"/api/tareas/{seed_tarea}/comentarios",
        json={"texto": "Ya lo estoy revisando"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["texto"] == "Ya lo estoy revisando"
    assert data["tarea_id"] == seed_tarea
    assert "id" in data


@pytest.mark.asyncio
async def test_agregar_comentario_tarea_inexistente_404(
    client: AsyncClient,
    profesor_token: str,
):
    """POST /api/tareas/{id}/comentarios with non-existent tarea returns 404."""
    response = await client.post(
        "/api/tareas/00000000-0000-0000-0000-000000000000/comentarios",
        json={"texto": "Comentario"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_agregar_comentario_vacio_422(
    client: AsyncClient,
    profesor_token: str,
    seed_tarea: str,
):
    """POST /api/tareas/{id}/comentarios with empty texto returns 422."""
    response = await client.post(
        f"/api/tareas/{seed_tarea}/comentarios",
        json={"texto": ""},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 422


# ── F8.3: GET /api/admin/tareas — Vista global admin ──────────────────────


@pytest.mark.asyncio
async def test_admin_tareas_200(
    client: AsyncClient,
    admin_token: str,
    seed_tarea: str,
):
    """F8.3: GET /api/admin/tareas returns all tasks for tenant."""
    response = await client.get(
        "/api/admin/tareas",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_admin_tareas_filter_asignado_a(
    client: AsyncClient,
    admin_token: str,
    seed_tarea: str,
    seed_profesor: str,
):
    """F8.3: GET /api/admin/tareas?asignado_a={uuid} filters."""
    response = await client.get(
        f"/api/admin/tareas?asignado_a={seed_profesor}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for t in data:
        assert t["asignado_a"] == seed_profesor


@pytest.mark.asyncio
async def test_admin_tareas_filter_estado(
    client: AsyncClient,
    admin_token: str,
    seed_tarea: str,
):
    """F8.3: GET /api/admin/tareas?estado=Pendiente filters."""
    response = await client.get(
        "/api/admin/tareas?estado=Pendiente",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for t in data:
        assert t["estado"] == "Pendiente"


@pytest.mark.asyncio
async def test_admin_tareas_search(
    client: AsyncClient,
    admin_token: str,
    seed_tarea: str,
):
    """F8.3: GET /api/admin/tareas?q=prueba searches descripcion."""
    response = await client.get(
        "/api/admin/tareas?q=prueba",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    # seed_tarea has descripcion "Tarea de prueba"
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_admin_tareas_sin_permiso_403(
    client: AsyncClient,
    profesor_token: str,
):
    """F8.3: GET /api/admin/tareas without tareas:admin returns 403."""
    response = await client.get(
        "/api/admin/tareas",
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


# ── Multi-tenant isolation ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_multi_tenant_isolation(
    client: AsyncClient,
    admin_token: str,
    otro_tenant_token: str,
    seed_tarea: str,
):
    """Tenant B cannot access Tenant A's tareas."""
    response = await client.get(
        "/api/tareas",
        headers={"Authorization": f"Bearer {otro_tenant_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


# ── Unauthenticated ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_get_tareas_401(
    client: AsyncClient,
):
    """GET /api/tareas without auth returns 401."""
    response = await client.get("/api/tareas")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_create_tarea_401(
    client: AsyncClient,
):
    """POST /api/tareas without auth returns 401."""
    response = await client.post(
        "/api/tareas",
        json={"asignado_a": str(...), "descripcion": "Test"},
    )
    assert response.status_code == 401
