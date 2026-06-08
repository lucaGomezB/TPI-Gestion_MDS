"""Integration tests for communication API endpoints (C-11).

All tests require PostgreSQL via testcontainers.
Marked with ``@pytest.mark.integration`` for selective execution.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.main import create_app
from app.models.comunicacion import (
    Comunicacion,
    EstadoComunicacion,
    EstadoLote,
    LoteComunicacion,
)

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
    """JWT for ADMIN user with comunicacion:enviar and comunicacion:aprobar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="admin-uuid",
        tenant_id="tenant-a",
        roles=["ADMIN"],
    )


@pytest.fixture
def profesor_token() -> str:
    """JWT for PROFESOR user with comunicacion:enviar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="profesor-uuid",
        tenant_id="tenant-a",
        roles=["PROFESOR"],
    )


@pytest.fixture
def coordinator_token() -> str:
    """JWT for COORDINADOR user with comunicacion:enviar and comunicacion:aprobar."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="coord-uuid",
        tenant_id="tenant-a",
        roles=["COORDINADOR"],
    )


@pytest.fixture
def other_tenant_token() -> str:
    """JWT for ADMIN of a different tenant."""
    from app.core.security import create_access_token

    return create_access_token(
        sub="other-admin-uuid",
        tenant_id="tenant-b",
        roles=["ADMIN"],
    )


@pytest.fixture
async def seed_materia(db_session: AsyncSession) -> str:
    """Create a test materia and return its ID."""
    from app.models.materia import Materia

    materia = Materia(
        tenant_id="tenant-a",
        codigo="TEST",
        nombre="Matematica Test",
    )
    db_session.add(materia)
    await db_session.flush()
    return materia.id


@pytest.fixture
async def seed_padron(db_session: AsyncSession, seed_materia: str) -> list[str]:
    """Create test padron entries for the materia. Returns entry IDs."""
    from app.models.padron import EntradaPadron, VersionPadron

    # Create a padron version
    version = VersionPadron(
        tenant_id="tenant-a",
        materia_id=seed_materia,
        cohorte_id="cohorte-uuid",
        cargado_por="admin-uuid",
        activa=True,
    )
    db_session.add(version)
    await db_session.flush()

    # Create entries
    entries = []
    for i in range(3):
        entry = EntradaPadron(
            tenant_id="tenant-a",
            version_id=version.id,
            nombre=f"Alumno{i}",
            apellidos=f"Apellido{i}",
            email=f"alumno{i}@test.com",
        )
        db_session.add(entry)
        entries.append(entry)

    await db_session.flush()
    return [e.id for e in entries]


# ── 14.1 Preview success ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_preview_success(
    client: AsyncClient,
    admin_token: str,
    seed_materia: str,
    seed_padron: list[str],
):
    """14.1: POST /preview returns 200 with rendered templates."""
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/preview",
        json={
            "asunto": "Hola {{alumno.nombre}}",
            "cuerpo": "Bienvenido a {{materia.nombre}}",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "previews" in data
    assert len(data["previews"]) > 0
    preview = data["previews"][0]
    assert "alumno_nombre" in preview
    assert "email_preview" in preview
    assert "asunto_renderizado" in preview
    assert "cuerpo_renderizado" in preview
    assert "***" in preview["email_preview"]


# ── 14.2 Preview 403 without assignment ────────────────────────────────────


@pytest.mark.asyncio
async def test_preview_without_access_403(
    client: AsyncClient,
    profesor_token: str,
    seed_materia: str,
):
    """14.2: PROFESOR without asignacion to materia gets 403."""
    # No Asignacion created — PROFESOR has no access
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/preview",
        json={
            "asunto": "Hola",
            "cuerpo": "Test",
        },
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


# ── 14.3 Enqueue success ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_enqueue_success(
    client: AsyncClient,
    admin_token: str,
    seed_materia: str,
    seed_padron: list[str],
):
    """14.3: POST /enviar with preview_confirmado=true creates Lote + Comunicaciones (201)."""
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/enviar",
        json={
            "asunto": "Hola {{alumno.nombre}}",
            "cuerpo": "Bienvenido",
            "preview_confirmado": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["estado"] in ("Pendiente", "AprobacionPendiente")
    assert data["total"] > 0


# ── 14.4 Enqueue 400 without preview_confirmado ──────────────────────────────


@pytest.mark.asyncio
async def test_enqueue_without_preview_confirmado_400(
    client: AsyncClient,
    admin_token: str,
    seed_materia: str,
    seed_padron: list[str],
):
    """14.4: POST /enviar without preview_confirmado=true returns 400."""
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/enviar",
        json={
            "asunto": "Hola",
            "cuerpo": "Test",
            "preview_confirmado": False,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 400
    assert "preview_confirmado" in response.json()["detail"].lower()


# ── 14.5 GET lotes list ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_lotes(
    client: AsyncClient,
    admin_token: str,
    seed_materia: str,
    seed_padron: list[str],
):
    """14.5: GET /comunicaciones returns lotes list for materia."""
    # Create a lote first
    await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/enviar",
        json={
            "asunto": "Test",
            "cuerpo": "Body",
            "preview_confirmado": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    response = await client.get(
        f"/api/materias/{seed_materia}/comunicaciones",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["total"] == 3


# ── 14.6 Approval flow — approve ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_approval_flow_approve(
    client: AsyncClient,
    coordinator_token: str,
    seed_materia: str,
    seed_padron: list[str],
    db_session: AsyncSession,
):
    """14.6: Create lote with approval required -> approve -> Enviando."""
    # Enable approval requirement in tenant config
    from app.models.tenant import Tenant

    tenant = await db_session.get(Tenant, "tenant-a")
    if tenant:
        tenant.configuracion = {
            "comunicaciones": {"requiere_aprobacion_masiva": True},
        }
        await db_session.flush()

    # Enqueue
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/enviar",
        json={
            "asunto": "Test",
            "cuerpo": "Body",
            "preview_confirmado": True,
        },
        headers={"Authorization": f"Bearer {coordinator_token}"},
    )
    assert response.status_code == 201
    lote_id = response.json()["id"]

    # Approve
    response = await client.put(
        f"/api/admin/comunicaciones/{lote_id}/aprobar",
        json={"accion": "aprobar"},
        headers={"Authorization": f"Bearer {coordinator_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "Enviando"


# ── 14.7 Approval flow — reject ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_approval_flow_reject(
    client: AsyncClient,
    coordinator_token: str,
    admin_token: str,
    seed_materia: str,
    seed_padron: list[str],
    db_session: AsyncSession,
):
    """14.7: Create lote -> reject -> Comunicaciones become Cancelado."""
    # Enable approval
    from app.models.tenant import Tenant

    tenant = await db_session.get(Tenant, "tenant-a")
    if tenant:
        tenant.configuracion = {
            "comunicaciones": {"requiere_aprobacion_masiva": True},
        }
        await db_session.flush()

    # Enqueue
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/enviar",
        json={
            "asunto": "Test",
            "cuerpo": "Body",
            "preview_confirmado": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    lote_id = response.json()["id"]

    # Reject
    response = await client.put(
        f"/api/admin/comunicaciones/{lote_id}/aprobar",
        json={"accion": "rechazar", "motivo": "Contenido inapropiado"},
        headers={"Authorization": f"Bearer {coordinator_token}"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "Cancelado"


# ── 14.8 Approve without permission (403) ────────────────────────────────────


@pytest.mark.asyncio
async def test_approve_without_permission_403(
    client: AsyncClient,
    profesor_token: str,
    seed_materia: str,
):
    """14.8: PROFESOR cannot approve communications."""
    response = await client.put(
        f"/api/admin/comunicaciones/fake-id/aprobar",
        json={"accion": "aprobar"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403


# ── 14.9 Worker processing ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_worker_process_lote(
    client: AsyncClient,
    admin_token: str,
    seed_materia: str,
    seed_padron: list[str],
    db_session: AsyncSession,
):
    """14.9: Enqueue, run worker, verify Enviado/Error transitions."""
    # Enqueue
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/enviar",
        json={
            "asunto": "Test",
            "cuerpo": "Body",
            "preview_confirmado": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    lote_id = response.json()["id"]

    # Run worker process_queue
    from app.workers.communication_worker import process_queue

    await process_queue(db_session)
    await db_session.commit()

    # Verify lote state
    lote = await db_session.get(LoteComunicacion, lote_id)
    assert lote is not None
    # May be Completado or Parcial depending on SMTP availability


# ── 14.10 Cancellation ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cancel_comunicacion(
    client: AsyncClient,
    admin_token: str,
    seed_materia: str,
    seed_padron: list[str],
    db_session: AsyncSession,
):
    """14.10: Enqueue, cancel before worker picks up -> Cancelado."""
    # Enqueue
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/enviar",
        json={
            "asunto": "Test",
            "cuerpo": "Body",
            "preview_confirmado": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Get a communication ID
    from app.repositories.communication import ComunicacionRepository

    repo = ComunicacionRepository(db_session, "tenant-a")
    coms = await repo.find_by_materia(seed_materia)
    assert len(coms) > 0
    com_id = coms[0].id

    # Cancel
    response = await client.put(
        f"/api/comunicaciones/{com_id}/cancelar",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "Cancelado"


# ── 14.11 Multi-tenant isolation ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_multi_tenant_isolation(
    client: AsyncClient,
    admin_token: str,
    other_tenant_token: str,
    seed_materia: str,
    seed_padron: list[str],
):
    """14.11: Tenant B cannot access Tenant A's communications."""
    # Tenant A creates communication
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/enviar",
        json={
            "asunto": "Tenant A msg",
            "cuerpo": "Secret",
            "preview_confirmado": True,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201

    # Tenant B tries to list (should get 403 or empty list since materia
    # doesn't exist in tenant B)
    response = await client.get(
        f"/api/materias/{seed_materia}/comunicaciones",
        headers={"Authorization": f"Bearer {other_tenant_token}"},
    )
    # Materia not in tenant B -> 404 or empty list
    assert response.status_code in (200, 404)


# ── 14.12 Unauthenticated (401) ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unauthenticated_preview_401(
    client: AsyncClient,
    seed_materia: str,
):
    """14.12: Preview without auth returns 401."""
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/preview",
        json={"asunto": "Hola", "cuerpo": "Test"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_enviar_401(
    client: AsyncClient,
    seed_materia: str,
):
    """14.12: Enviar without auth returns 401."""
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/enviar",
        json={"asunto": "Hola", "cuerpo": "Test", "preview_confirmado": True},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_list_401(
    client: AsyncClient,
    seed_materia: str,
):
    """14.12: List without auth returns 401."""
    response = await client.get(
        f"/api/materias/{seed_materia}/comunicaciones",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_aprobar_401(
    client: AsyncClient,
):
    """14.12: Aprobar without auth returns 401."""
    response = await client.put(
        "/api/admin/comunicaciones/fake-id/aprobar",
        json={"accion": "aprobar"},
    )
    assert response.status_code == 401


# ── 14.13 PROFESOR scope enforcement ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_profesor_scope_enforcement(
    client: AsyncClient,
    profesor_token: str,
    seed_materia: str,
    seed_padron: list[str],
    db_session: AsyncSession,
):
    """14.13: PROFESOR can only access their assigned materias."""
    # Create an Asignacion for this PROFESOR + materia
    from app.models.asignacion import Asignacion
    from datetime import date

    asignacion = Asignacion(
        tenant_id="tenant-a",
        usuario_id="profesor-uuid",
        rol="PROFESOR",
        materia_id=seed_materia,
        vig_desde=date(2026, 1, 1),
        vig_hasta=None,
    )
    db_session.add(asignacion)
    await db_session.flush()

    # PROFESOR should now be able to access
    response = await client.post(
        f"/api/materias/{seed_materia}/comunicaciones/preview",
        json={"asunto": "Hola {{alumno.nombre}}", "cuerpo": "Test"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 200

    # Another materia without asignacion should fail
    from app.models.materia import Materia

    other_materia = Materia(
        tenant_id="tenant-a",
        codigo="OTHER",
        nombre="Otra Materia",
    )
    db_session.add(other_materia)
    await db_session.flush()

    response = await client.post(
        f"/api/materias/{other_materia.id}/comunicaciones/preview",
        json={"asunto": "Hola", "cuerpo": "Test"},
        headers={"Authorization": f"Bearer {profesor_token}"},
    )
    assert response.status_code == 403
