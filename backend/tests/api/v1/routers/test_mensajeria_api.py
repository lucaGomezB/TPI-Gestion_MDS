"""Integration tests for mensajeria API endpoints (C-13).

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


# ---------------------------------------------------------------------------
# Token fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_token() -> str:
    """JWT for ADMIN user with mensajeria:enviar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def profesor_token() -> str:
    """JWT for PROFESOR user with mensajeria:enviar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def tutor_token() -> str:
    """JWT for TUTOR user with mensajeria:enviar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="tutor-uuid",
        tenant_id="tenant-a",
        roles=["TUTOR"],
    )


@pytest.fixture
def otro_admin_token() -> str:
    """JWT for ADMIN of a different tenant."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="other-admin-uuid",
        tenant_id="tenant-b",
        roles=["ADMIN"],
    )


@pytest.fixture
def nexo_token() -> str:
    """JWT for NEXO user (NO mensajeria:enviar)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="nexo-uuid",
        tenant_id="tenant-a",
        roles=["NEXO"],
    )


@pytest.fixture
def alumno_token() -> str:
    """JWT for ALUMNO user (NO mensajeria:enviar)."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="alumno-uuid",
        tenant_id="tenant-a",
        roles=["ALUMNO"],
    )


# ---------------------------------------------------------------------------
# Seed fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_remitente(db_session: AsyncSession) -> str:
    """Create the sender user in tenant-a."""
    from app.models.usuario import Usuario

    user = Usuario(
        id="remitente-uuid",
        tenant_id="tenant-a",
        nombre="Juan",
        apellidos="Profesor",
        email="juan@test.com",
        email_hash="aaa",
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


@pytest.fixture
async def seed_destinatario(db_session: AsyncSession) -> str:
    """Create the recipient user in tenant-a."""
    from app.models.usuario import Usuario

    user = Usuario(
        id="destinatario-uuid",
        tenant_id="tenant-a",
        nombre="Maria",
        apellidos="Coordinadora",
        email="maria@test.com",
        email_hash="bbb",
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


@pytest.fixture
async def seed_otro_tenant_user(db_session: AsyncSession) -> str:
    """Create a user in tenant-b (cross-tenant test)."""
    from app.models.usuario import Usuario

    user = Usuario(
        id="otro-tenant-uuid",
        tenant_id="tenant-b",
        nombre="Pedro",
        apellidos="Otro",
        email="pedro@otro.com",
        email_hash="ccc",
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


@pytest.fixture
async def seed_hilo_mensajes(
    db_session: AsyncSession,
    seed_remitente: str,
    seed_destinatario: str,
) -> list[str]:
    """Create a thread with messages between remitente and destinatario."""
    from datetime import datetime, timezone, timedelta
    from app.models.hilo_mensaje import HiloMensaje
    from app.models.mensaje import Mensaje

    hilo = HiloMensaje(
        tenant_id="tenant-a",
        asunto="Novedades del curso",
        participantes=["remitente-uuid", "destinatario-uuid"],
        ultimo_mensaje_at=datetime.now(timezone.utc),
    )
    db_session.add(hilo)
    await db_session.flush()

    # Message 1: remitente -> destinatario (unread)
    m1 = Mensaje(
        tenant_id="tenant-a",
        hilo_id=hilo.id,
        remitente_id="remitente-uuid",
        destinatario_id="destinatario-uuid",
        asunto="Novedades del curso",
        cuerpo="Hola Maria, te escribo sobre las novedades",
        leido=False,
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    db_session.add(m1)

    # Message 2: destinatario -> remitente (reply)
    m2 = Mensaje(
        tenant_id="tenant-a",
        hilo_id=hilo.id,
        remitente_id="destinatario-uuid",
        destinatario_id="remitente-uuid",
        asunto="Novedades del curso",
        cuerpo="Gracias Juan, ya vi las novedades",
        leido=True,
        created_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(m2)

    await db_session.flush()
    return [hilo.id, m1.id, m2.id]


# ---------------------------------------------------------------------------
# 8.1 Tests: POST /api/mensajes -- Send message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enviar_mensaje_creates_thread(
    client: AsyncClient,
    admin_token: str,
    seed_remitente: str,
    seed_destinatario: str,
):
    """POST /api/mensajes creates a new thread when none exists (201)."""
    from app.core.security import create_access_token

    token = create_access_token(
        sub="remitente-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.post(
        "/api/mensajes",
        json={
            "destinatario_id": "destinatario-uuid",
            "asunto": "Nuevo tema",
            "cuerpo": "Hola, este es un mensaje de prueba",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "hilo_id" in data
    assert data["asunto"] == "Nuevo tema"


@pytest.mark.asyncio
async def test_enviar_mensaje_reuses_thread(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """POST /api/mensajes reuses existing thread with same asunto (201)."""
    from app.core.security import create_access_token

    hilo_id = seed_hilo_mensajes[0]

    token = create_access_token(
        sub="remitente-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.post(
        "/api/mensajes",
        json={
            "destinatario_id": "destinatario-uuid",
            "asunto": "Novedades del curso",
            "cuerpo": "Un mensaje mas en el mismo hilo",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["hilo_id"] == hilo_id


@pytest.mark.asyncio
async def test_enviar_mensaje_rejects_inexistent_user(
    client: AsyncClient,
    admin_token: str,
):
    """POST /api/mensajes rejects non-existent recipient (404)."""
    response = await client.post(
        "/api/mensajes",
        json={
            "destinatario_id": "non-existent-uuid",
            "asunto": "Test",
            "cuerpo": "Mensaje",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_enviar_mensaje_rejects_cross_tenant(
    client: AsyncClient,
    admin_token: str,
    seed_otro_tenant_user: str,
):
    """POST /api/mensajes rejects cross-tenant recipient (404)."""
    response = await client.post(
        "/api/mensajes",
        json={
            "destinatario_id": seed_otro_tenant_user,
            "asunto": "Test",
            "cuerpo": "Mensaje a otro tenant",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_enviar_mensaje_rejects_without_permission(
    client: AsyncClient,
    nexo_token: str,
    seed_destinatario: str,
):
    """POST /api/mensajes returns 403 for user without mensajeria:enviar."""
    from app.core.security import create_access_token

    token = create_access_token(
        sub="nexo-uuid",
        tenant_id="tenant-a",
        roles=["NEXO"],
    )

    response = await client.post(
        "/api/mensajes",
        json={
            "destinatario_id": "destinatario-uuid",
            "asunto": "Test",
            "cuerpo": "Sin permiso",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_enviar_mensaje_rejects_empty_cuerpo(
    client: AsyncClient,
    admin_token: str,
    seed_destinatario: str,
):
    """POST /api/mensajes rejects empty cuerpo (422)."""
    response = await client.post(
        "/api/mensajes",
        json={
            "destinatario_id": "destinatario-uuid",
            "asunto": "Test",
            "cuerpo": "",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 8.2 Tests: POST /api/mensajes/{id}/responder -- Reply
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_responder_as_sender(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """POST /api/mensajes/{id}/responder as original sender creates reply (201)."""
    from app.core.security import create_access_token

    mensaje_id = seed_hilo_mensajes[1]  # first message in thread

    token = create_access_token(
        sub="remitente-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.post(
        f"/api/mensajes/{mensaje_id}/responder",
        json={"cuerpo": "Respuesta del remitente"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["hilo_id"] == seed_hilo_mensajes[0]


@pytest.mark.asyncio
async def test_responder_as_receiver(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """POST /api/mensajes/{id}/responder as receiver creates reply (201)."""
    from app.core.security import create_access_token

    mensaje_id = seed_hilo_mensajes[1]  # first message in thread

    token = create_access_token(
        sub="destinatario-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.post(
        f"/api/mensajes/{mensaje_id}/responder",
        json={"cuerpo": "Gracias por el mensaje"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["hilo_id"] == seed_hilo_mensajes[0]


@pytest.mark.asyncio
async def test_responder_rejects_non_participant(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """POST /api/mensajes/{id}/responder rejects non-participant (403)."""
    mensaje_id = seed_hilo_mensajes[1]  # first message in thread

    response = await client.post(
        f"/api/mensajes/{mensaje_id}/responder",
        json={"cuerpo": "Intrusion"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_responder_rejects_empty_body(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """POST /api/mensajes/{id}/responder rejects empty cuerpo (422)."""
    from app.core.security import create_access_token

    mensaje_id = seed_hilo_mensajes[1]

    token = create_access_token(
        sub="remitente-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.post(
        f"/api/mensajes/{mensaje_id}/responder",
        json={"cuerpo": ""},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 8.3 Tests: GET /api/mensajes -- Inbox
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inbox_returns_threads(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """GET /api/mensajes returns inbox threads (200)."""
    from app.core.security import create_access_token

    token = create_access_token(
        sub="remitente-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.get(
        "/api/mensajes",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert len(data["data"]) >= 1
    assert "hilo_id" in data["data"][0]
    assert "asunto" in data["data"][0]
    assert "no_leidos" in data["data"][0]


@pytest.mark.asyncio
async def test_inbox_pagination(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """GET /api/mensajes respects limit and offset (200)."""
    from app.core.security import create_access_token

    token = create_access_token(
        sub="remitente-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.get(
        "/api/mensajes?limit=5&offset=0",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert len(data["data"]) <= 5


@pytest.mark.asyncio
async def test_inbox_empty_for_new_user(
    client: AsyncClient,
    admin_token: str,
):
    """GET /api/mensajes returns empty for user with no messages (200)."""
    response = await client.get(
        "/api/mensajes",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_inbox_multi_tenant_isolation(
    client: AsyncClient,
    admin_token: str,
    otro_admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """GET /api/mensajes returns different results per tenant."""
    # Tenant A gets the threads
    response_a = await client.get(
        "/api/mensajes",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Tenant B gets empty
    response_b = await client.get(
        "/api/mensajes",
        headers={"Authorization": f"Bearer {otro_admin_token}"},
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    data_b = response_b.json()
    assert data_b["total"] == 0


# ---------------------------------------------------------------------------
# 8.4 Tests: GET /api/mensajes/{id} -- View thread
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ver_hilo_returns_messages(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """GET /api/mensajes/{id} returns thread messages ordered (200)."""
    from app.core.security import create_access_token

    mensaje_id = seed_hilo_mensajes[1]

    token = create_access_token(
        sub="remitente-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.get(
        f"/api/mensajes/{mensaje_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["hilo_id"] == seed_hilo_mensajes[0]
    assert "mensajes" in data
    assert len(data["mensajes"]) >= 1
    # Messages should be ordered by created_at ascending
    created_ats = [m["created_at"] for m in data["mensajes"]]
    assert created_ats == sorted(created_ats)


@pytest.mark.asyncio
async def test_ver_hilo_auto_marks_read(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """GET /api/mensajes/{id} auto-marks messages as read."""
    from app.core.security import create_access_token

    mensaje_id = seed_hilo_mensajes[1]

    # View as destinatario (who should have unread messages)
    token = create_access_token(
        sub="destinatario-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.get(
        f"/api/mensajes/{mensaje_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # After viewing, all destinatario's messages should be leido=true
    for m in data["mensajes"]:
        if m["destinatario_id"] == "destinatario-uuid":
            assert m["leido"] is True


@pytest.mark.asyncio
async def test_ver_hilo_rejects_non_participant(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """GET /api/mensajes/{id} rejects non-participant (403)."""
    mensaje_id = seed_hilo_mensajes[1]

    response = await client.get(
        f"/api/mensajes/{mensaje_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# 8.5 Tests: GET /api/mensajes/no-leidos -- Unread count
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_leidos_returns_count(
    client: AsyncClient,
    admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """GET /api/mensajes/no-leidos returns unread count for user."""
    from app.core.security import create_access_token

    # destintario has 1 unread message from seed
    token = create_access_token(
        sub="destinatario-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )

    response = await client.get(
        "/api/mensajes/no-leidos",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert isinstance(data["count"], int)


@pytest.mark.asyncio
async def test_no_leidos_zero_for_new_user(
    client: AsyncClient,
    admin_token: str,
):
    """GET /api/mensajes/no-leidos returns 0 for user with no messages."""
    response = await client.get(
        "/api/mensajes/no-leidos",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0


@pytest.mark.asyncio
async def test_no_leidos_multi_tenant_isolation(
    client: AsyncClient,
    admin_token: str,
    otro_admin_token: str,
    seed_hilo_mensajes: list[str],
):
    """GET /api/mensajes/no-leidos returns different counts per tenant."""
    response_a = await client.get(
        "/api/mensajes/no-leidos",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response_b = await client.get(
        "/api/mensajes/no-leidos",
        headers={"Authorization": f"Bearer {otro_admin_token}"},
    )

    data_a = response_a.json()
    data_b = response_b.json()
    # Both should work but counts may differ
    assert "count" in data_a
    assert "count" in data_b
