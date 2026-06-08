"""Comprehensive tests for the audit log subsystem.

Test categories:
- **Unit tests** (11.1-11.3): No database required. Test enum, repository
  interface, and action code validation.
- **Integration tests** (11.4-11.13): Require a running PostgreSQL with
  migrations applied. Use testcontainers for ephemeral DB setup.

All integration tests are marked with ``@pytest.mark.integration``.
"""

import re
from datetime import UTC, datetime, timedelta
from typing import Any, AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.action_codes import AccionAuditoria
from app.repositories.audit_repository import AuditRepository


# ═══════════════════════════════════════════════════════════════════════════════
# 11.1 Unit test: AccionAuditoria enum — all codes exist, values match names
# ═══════════════════════════════════════════════════════════════════════════════

class TestAccionAuditoriaEnum:
    """Verify the action code closed catalog (RN-24)."""

    EXPECTED_CODES = [
        "CALIFICACIONES_IMPORTAR",
        "PADRON_CARGAR",
        "COMUNICACION_ENVIAR",
        "ASIGNACION_MODIFICAR",
        "LIQUIDACION_CALCULAR",
        "LIQUIDACION_CERRAR",
        "COLOQUIO_CREAR",
        "COLOQUIO_RESERVAR",
        "COLOQUIO_RESULTADO",
        "IMPERSONACION_INICIAR",
        "IMPERSONACION_FINALIZAR",
        "ATRASADOS_CONSULTAR",
        "RANKING_CONSULTAR",
        "NOTAS_FINALES_CONSULTAR",
        "EXPORT_ATRASADOS_CONSULTAR",
        "MONITOR_GENERAL_CONSULTAR",
        "SEGUIMIENTO_CONSULTAR",
    ]

    @pytest.mark.parametrize("code", EXPECTED_CODES)
    def test_enum_contains_code(self, code: str) -> None:
        """Each expected code should exist as a member of AccionAuditoria."""
        assert hasattr(AccionAuditoria, code), f"Missing action code: {code}"

    def test_enum_values_match_names(self) -> None:
        """Every member's string value should match its name."""
        for member in AccionAuditoria:
            assert member.value == member.name, (
                f"{member.name}.value == '{member.value}', expected '{member.name}'"
            )

    def test_enum_is_str_enum(self) -> None:
        """AccionAuditoria should be a StrEnum (values are strings)."""
        for member in AccionAuditoria:
            assert isinstance(member.value, str)

    def test_enum_count(self) -> None:
        """Should have exactly the expected number of action codes."""
        assert len(AccionAuditoria) == len(self.EXPECTED_CODES)

    def test_enum_members_are_unique(self) -> None:
        """No duplicate values."""
        values = [m.value for m in AccionAuditoria]
        assert len(values) == len(set(values))


# ═══════════════════════════════════════════════════════════════════════════════
# 11.2 Unit test: AuditRepository append-only enforcement
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditRepositoryAppendOnly:
    """Verify that AuditRepository does NOT expose update/delete methods."""

    @pytest.fixture
    def repo_methods(self) -> set[str]:
        """Return the set of public method names on AuditRepository."""
        return {
            name
            for name in dir(AuditRepository)
            if not name.startswith("_")
        }

    def test_repository_has_create_method(self, repo_methods: set[str]) -> None:
        """AuditRepository should have a create() method."""
        assert "create" in repo_methods

    def test_repository_has_search_method(self, repo_methods: set[str]) -> None:
        """AuditRepository should have a search() method."""
        assert "search" in repo_methods

    def test_repository_has_get_docente_interacciones_method(
        self, repo_methods: set[str]
    ) -> None:
        """AuditRepository should have get_docente_interacciones()."""
        assert "get_docente_interacciones" in repo_methods

    def test_repository_has_export_search_method(
        self, repo_methods: set[str]
    ) -> None:
        """AuditRepository should have export_search()."""
        assert "export_search" in repo_methods

    def test_repository_does_not_have_update(self, repo_methods: set[str]) -> None:
        """AuditRepository must NOT have an update() method."""
        assert "update" not in repo_methods

    def test_repository_does_not_have_delete(self, repo_methods: set[str]) -> None:
        """AuditRepository must NOT have a delete() method."""
        assert "delete" not in repo_methods


# ═══════════════════════════════════════════════════════════════════════════════
# 11.3 Unit test: Invalid action code rejection
# ═══════════════════════════════════════════════════════════════════════════════

class TestInvalidActionCode:
    """Verify that log_action() rejects invalid action codes."""

    @pytest.mark.asyncio
    async def test_invalid_str_code_raises_value_error(self) -> None:
        """Calling log_action() with an invalid string should raise ValueError."""
        from app.services.audit_service import AuditService

        # Create a mock repo that fails loudly if called
        class _MockRepo:
            async def create(self, data: dict) -> None:
                msg = "Should not be reached — validation should fail first"
                raise RuntimeError(msg)

        service = AuditService(_MockRepo())  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="Invalid action code"):
            await service.log_action(
                accion="NOT_A_VALID_CODE",
                actor_id="some-uuid",
                tenant_id="some-tenant",
            )

    @pytest.mark.asyncio
    async def test_invalid_type_raises_value_error(self) -> None:
        """Calling log_action() with a non-str, non-Enum value should raise ValueError."""
        from app.services.audit_service import AuditService

        class _MockRepo:
            async def create(self, data: dict) -> None:
                msg = "Should not be reached"
                raise RuntimeError(msg)

        service = AuditService(_MockRepo())  # type: ignore[arg-type]

        with pytest.raises(ValueError, match="Invalid action code type"):
            await service.log_action(
                accion=12345,  # type: ignore[arg-type]
                actor_id="some-uuid",
                tenant_id="some-tenant",
            )


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS — Require PostgreSQL with testcontainers
# ═══════════════════════════════════════════════════════════════════════════════

# Skip all integration tests if testcontainers is not installed
try:
    from testcontainers.postgres import PostgresContainer  # noqa: F401

    HAS_TESTCONTAINERS = True
except ImportError:  # noqa: S110
    HAS_TESTCONTAINERS = False

pytestmark_integration = pytest.mark.skipif(
    not HAS_TESTCONTAINERS,
    reason="testcontainers not installed; run: pip install testcontainers",
)


def _skip_if_no_testcontainers() -> None:
    if not HAS_TESTCONTAINERS:
        pytest.skip("testcontainers not available")


@pytest.fixture(scope="module")
def postgres_container() -> Any:
    """Start a PostgreSQL container for integration tests.

    This fixture has ``module`` scope — the container is started once
    per test module and reused across all integration tests in this file.
    """
    _skip_if_no_testcontainers()
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer("postgres:16-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture
async def audit_db_session(
    postgres_container: Any,
) -> AsyncGenerator[AsyncSession, None]:
    """Create an async session connected to the test PostgreSQL container,
    with the audit_log table and triggers applied.
    """
    dsn = postgres_container.get_connection_url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    engine = create_async_engine(dsn, echo=False)

    # Create the audit_log table directly (simulating migration 013)
    async with engine.begin() as conn:
        await conn.execute(
            text("""
                CREATE EXTENSION IF NOT EXISTS pgcrypto;
            """)
        )
        await conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    nombre VARCHAR(255) NOT NULL,
                    activo BOOLEAN NOT NULL DEFAULT true
                )
            """)
        )
        # Insert a default tenant
        await conn.execute(
            text("""
                INSERT INTO tenants (id, nombre)
                VALUES ('test-tenant-0000-0000-000000000001', 'Test Tenant')
                ON CONFLICT (id) DO NOTHING
            """)
        )
        await conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id),
                    nombre VARCHAR(100) NOT NULL,
                    apellidos VARCHAR(100) NOT NULL,
                    email TEXT NOT NULL
                )
            """)
        )
        # Insert a default user
        await conn.execute(
            text("""
                INSERT INTO usuarios (id, tenant_id, nombre, apellidos, email)
                VALUES (
                    'test-user-0000-0000-0000-000000000001',
                    'test-tenant-0000-0000-0000-000000000001',
                    'Test', 'User', 'test@example.com'
                )
                ON CONFLICT (id) DO NOTHING
            """)
        )
        # Insert a second tenant user
        await conn.execute(
            text("""
                INSERT INTO usuarios (id, tenant_id, nombre, apellidos, email)
                VALUES (
                    'test-user-0000-0000-0000-000000000002',
                    'test-tenant-0000-0000-0000-000000000002',
                    'Other', 'User', 'other@example.com'
                )
                ON CONFLICT (id) DO NOTHING
            """)
        )

        # Create audit_log table (simplified — matches migration 013)
        await conn.execute(
            text("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id UUID NOT NULL REFERENCES tenants(id),
                    fecha_hora TIMESTAMPTZ NOT NULL DEFAULT now(),
                    actor_id UUID NOT NULL REFERENCES usuarios(id),
                    impersonado_id UUID REFERENCES usuarios(id),
                    materia_id UUID,
                    accion VARCHAR(50) NOT NULL,
                    detalle JSONB,
                    filas_afectadas INTEGER,
                    ip VARCHAR(45),
                    user_agent VARCHAR(500)
                )
            """)
        )

        # Full-text search support (generated column)
        await conn.execute(
            text("""
                ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS search_vector TSVECTOR
                    GENERATED ALWAYS AS (
                        to_tsvector('spanish',
                            coalesce(accion, '') || ' ' ||
                            coalesce(detalle::text, '') || ' ' ||
                            coalesce(ip, '')
                        )
                    ) STORED;
            """)
        )

        # Indexes
        await conn.execute(
            text("""
                CREATE INDEX IF NOT EXISTS ix_audit_log_tenant_fecha
                    ON audit_log(tenant_id, fecha_hora DESC)
            """)
        )
        await conn.execute(
            text("""
                CREATE INDEX IF NOT EXISTS ix_audit_log_tenant_accion
                    ON audit_log(tenant_id, accion)
            """)
        )
        await conn.execute(
            text("""
                CREATE INDEX IF NOT EXISTS ix_audit_log_tenant_actor
                    ON audit_log(tenant_id, actor_id, fecha_hora DESC)
            """)
        )
        await conn.execute(
            text("""
                CREATE INDEX IF NOT EXISTS ix_audit_log_search_vector
                    ON audit_log USING GIN(search_vector)
            """)
        )

        # Append-only triggers
        await conn.execute(
            text("""
                CREATE OR REPLACE FUNCTION reject_audit_modification()
                RETURNS TRIGGER AS $$
                BEGIN
                    RAISE EXCEPTION 'audit_log is append-only: UPDATE and DELETE are forbidden';
                END;
                $$ LANGUAGE plpgsql;
            """)
        )
        await conn.execute(
            text("""
                DROP TRIGGER IF EXISTS trg_reject_audit_update ON audit_log
            """)
        )
        await conn.execute(
            text("""
                CREATE TRIGGER trg_reject_audit_update
                    BEFORE UPDATE ON audit_log
                    FOR EACH ROW EXECUTE FUNCTION reject_audit_modification()
            """)
        )
        await conn.execute(
            text("""
                DROP TRIGGER IF EXISTS trg_reject_audit_delete ON audit_log
            """)
        )
        await conn.execute(
            text("""
                CREATE TRIGGER trg_reject_audit_delete
                    BEFORE DELETE ON audit_log
                    FOR EACH ROW EXECUTE FUNCTION reject_audit_modification()
            """)
        )

    # Create a session for test use
    from sqlalchemy.orm import sessionmaker

    session_factory = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session

    await engine.dispose()


# ── Constants for test data ───────────────────────────────────────────────────

TENANT_A = "test-tenant-0000-0000-0000-000000000001"
TENANT_B = "test-tenant-0000-0000-0000-000000000002"
ACTOR_A = "test-user-0000-0000-0000-000000000001"
ACTOR_B = "test-user-0000-0000-0000-000000000002"
MATERIA_X = "test-materia-0000-0000-0000-000000000001"
MATERIA_Y = "test-materia-0000-0000-0000-000000000002"


# ═══════════════════════════════════════════════════════════════════════════════
# 11.4 Integration: Audit log creation
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_creation(audit_db_session: AsyncSession) -> None:
    """Creating an audit log entry should persist all fields correctly."""
    repo = AuditRepository(audit_db_session)

    entry = await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "CALIFICACIONES_IMPORTAR",
            "materia_id": MATERIA_X,
            "detalle": {"actividades": 5, "alumnos": 30},
            "filas_afectadas": 150,
            "ip": "192.168.1.1",
            "user_agent": "Mozilla/5.0 Test",
        }
    )

    assert entry.id is not None
    assert entry.tenant_id == TENANT_A
    assert entry.actor_id == ACTOR_A
    assert entry.accion == "CALIFICACIONES_IMPORTAR"
    assert entry.materia_id == MATERIA_X
    assert entry.detalle == {"actividades": 5, "alumnos": 30}
    assert entry.filas_afectadas == 150
    assert entry.ip == "192.168.1.1"
    assert entry.user_agent == "Mozilla/5.0 Test"
    assert entry.fecha_hora is not None  # server_default should set this
    assert entry.impersonado_id is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_minimal_fields(audit_db_session: AsyncSession) -> None:
    """Creating an audit log with only required fields should succeed."""
    repo = AuditRepository(audit_db_session)

    entry = await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "PADRON_CARGAR",
        }
    )

    assert entry.id is not None
    assert entry.accion == "PADRON_CARGAR"
    assert entry.materia_id is None
    assert entry.impersonado_id is None
    assert entry.detalle is None
    assert entry.filas_afectadas is None
    assert entry.ip is None
    assert entry.user_agent is None


# ═══════════════════════════════════════════════════════════════════════════════
# 11.5 Integration: Append-only trigger
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_append_only_update_rejected(audit_db_session: AsyncSession) -> None:
    """Direct SQL UPDATE on audit_log should be rejected by trigger."""
    repo = AuditRepository(audit_db_session)

    entry = await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "LIQUIDACION_CERRAR",
        }
    )

    with pytest.raises(Exception, match="audit_log is append-only"):
        await audit_db_session.execute(
            text(
                "UPDATE audit_log SET accion = 'PADRON_CARGAR' WHERE id = :id"
            ).bindparams(id=entry.id)
        )
        await audit_db_session.commit()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_append_only_delete_rejected(audit_db_session: AsyncSession) -> None:
    """Direct SQL DELETE on audit_log should be rejected by trigger."""
    repo = AuditRepository(audit_db_session)

    entry = await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "COMUNICACION_ENVIAR",
        }
    )

    with pytest.raises(Exception, match="audit_log is append-only"):
        await audit_db_session.execute(
            text("DELETE FROM audit_log WHERE id = :id").bindparams(id=entry.id)
        )
        await audit_db_session.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# 11.6 Integration: Full-text search
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_text_search_by_keyword(audit_db_session: AsyncSession) -> None:
    """Searching by keyword should return matching entries."""
    repo = AuditRepository(audit_db_session)

    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "CALIFICACIONES_IMPORTAR",
            "detalle": {"actividades": 10},
        }
    )
    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "COMUNICACION_ENVIAR",
            "detalle": {"mensaje": "Recordatorio"},
        }
    )

    # Search for "calificaciones"
    items, total = await repo.search(
        tenant_id=TENANT_A,
        q="calificaciones",
    )
    assert total >= 1
    assert all("CALIFICACIONES" in item.accion for item in items)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_text_search_no_results(audit_db_session: AsyncSession) -> None:
    """Searching with a term that matches nothing should return empty results."""
    repo = AuditRepository(audit_db_session)

    items, total = await repo.search(
        tenant_id=TENANT_A,
        q="xyznonexistentterm12345",
    )
    assert total == 0
    assert items == []


# ═══════════════════════════════════════════════════════════════════════════════
# 11.7 Integration: Filters
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_by_action(audit_db_session: AsyncSession) -> None:
    """Filtering by accion should return only entries with that action code."""
    repo = AuditRepository(audit_db_session)

    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "CALIFICACIONES_IMPORTAR",
        }
    )
    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "PADRON_CARGAR",
        }
    )

    items, total = await repo.search(
        tenant_id=TENANT_A,
        accion="CALIFICACIONES_IMPORTAR",
    )
    assert total >= 1
    assert all(item.accion == "CALIFICACIONES_IMPORTAR" for item in items)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_by_actor(audit_db_session: AsyncSession) -> None:
    """Filtering by actor_id should return only entries by that user."""
    repo = AuditRepository(audit_db_session)

    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "COMUNICACION_ENVIAR",
        }
    )

    items, total = await repo.search(
        tenant_id=TENANT_A,
        actor_id=ACTOR_A,
    )
    assert total >= 1
    assert all(item.actor_id == ACTOR_A for item in items)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_by_materia(audit_db_session: AsyncSession) -> None:
    """Filtering by materia_id should return only entries for that subject."""
    repo = AuditRepository(audit_db_session)

    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "CALIFICACIONES_IMPORTAR",
            "materia_id": MATERIA_X,
        }
    )

    items, total = await repo.search(
        tenant_id=TENANT_A,
        materia_id=MATERIA_X,
    )
    assert total >= 1
    assert all(item.materia_id == MATERIA_X for item in items)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_by_date_range(audit_db_session: AsyncSession) -> None:
    """Filtering by date range should return only entries within that range."""
    repo = AuditRepository(audit_db_session)

    # Create entry with explicit fecha_hora override
    from sqlalchemy import insert

    stmt = insert(
        audit_db_session.get_bind().dialect  # type: ignore
    ).returning(
        # We use raw SQL for explicit dates
    )

    # Insert with explicit past date
    past_date = datetime(2025, 1, 1, tzinfo=UTC)
    await audit_db_session.execute(
        text(
            """INSERT INTO audit_log (tenant_id, actor_id, accion, fecha_hora)
               VALUES (:tenant, :actor, :accion, :fecha)"""
        ).bindparams(
            tenant=TENANT_A,
            actor=ACTOR_A,
            accion="PADRON_CARGAR",
            fecha=past_date,
        )
    )
    await audit_db_session.flush()

    items, total = await repo.search(
        tenant_id=TENANT_A,
        fecha_desde=datetime(2024, 1, 1, tzinfo=UTC),
        fecha_hasta=datetime(2025, 6, 1, tzinfo=UTC),
    )
    assert total >= 1

    items_outside, total_outside = await repo.search(
        tenant_id=TENANT_A,
        fecha_desde=datetime(2026, 6, 1, tzinfo=UTC),
    )
    assert total_outside == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_multiple_combined(audit_db_session: AsyncSession) -> None:
    """Multiple filters should be applied conjunctively."""
    repo = AuditRepository(audit_db_session)

    # Create matching entry
    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "COMUNICACION_ENVIAR",
            "materia_id": MATERIA_X,
            "ip": "10.0.0.1",
        }
    )

    # All filters match
    items, total = await repo.search(
        tenant_id=TENANT_A,
        accion="COMUNICACION_ENVIAR",
        actor_id=ACTOR_A,
        materia_id=MATERIA_X,
        ip="10.0.0.1",
    )
    assert total >= 1

    # Non-matching materia_id should yield 0 results
    items_non, total_non = await repo.search(
        tenant_id=TENANT_A,
        accion="COMUNICACION_ENVIAR",
        materia_id=MATERIA_Y,
    )
    assert total_non == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 11.8 Integration: Tenant isolation
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_tenant_isolation(audit_db_session: AsyncSession) -> None:
    """Two different tenants must see separate search results."""
    repo = AuditRepository(audit_db_session)

    # Create entry in tenant A
    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "CALIFICACIONES_IMPORTAR",
        }
    )

    # Create entry in tenant B
    await repo.create(
        {
            "tenant_id": TENANT_B,
            "actor_id": ACTOR_B,
            "accion": "COMUNICACION_ENVIAR",
        }
    )

    # Tenant A sees only its own entry
    items_a, total_a = await repo.search(tenant_id=TENANT_A)
    assert total_a >= 1
    assert all(item.tenant_id == TENANT_A for item in items_a)

    # Tenant B sees only its own entry
    items_b, total_b = await repo.search(tenant_id=TENANT_B)
    assert total_b >= 1
    assert all(item.tenant_id == TENANT_B for item in items_b)


# ═══════════════════════════════════════════════════════════════════════════════
# 11.9 Integration: Impersonation
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_impersonation_recorded(audit_db_session: AsyncSession) -> None:
    """Impersonated actions must record both actor_id and impersonado_id."""
    repo = AuditRepository(audit_db_session)

    entry = await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "impersonado_id": ACTOR_B,
            "accion": "IMPERSONACION_INICIAR",
        }
    )

    assert entry.actor_id == ACTOR_A
    assert entry.impersonado_id == ACTOR_B


# ═══════════════════════════════════════════════════════════════════════════════
# 11.10 Integration: PII sanitization
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_pii_not_in_detalle(audit_db_session: AsyncSession) -> None:
    """Audit log detalle must not contain known PII patterns."""
    repo = AuditRepository(audit_db_session)

    # Create entries with various detalle
    entries_data = [
        {"tenant_id": TENANT_A, "actor_id": ACTOR_A, "accion": "CALIFICACIONES_IMPORTAR",
         "detalle": {"actividades": 5, "alumnos": 30}},
        {"tenant_id": TENANT_A, "actor_id": ACTOR_A, "accion": "COMUNICACION_ENVIAR",
         "detalle": {"destinatarios": 20, "mensaje": "Recordatorio de entrega"}},
        {"tenant_id": TENANT_A, "actor_id": ACTOR_A, "accion": "PADRON_CARGAR",
         "detalle": {"alumnos_agregados": 15}},
    ]

    for data in entries_data:
        await repo.create(data)

    # Fetch all entries and verify no PII patterns in detalle
    items, _ = await repo.search(tenant_id=TENANT_A, limit=100)

    # PII patterns to check
    pii_patterns = {
        "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
        "dni": re.compile(r"\b\d{7,8}\b"),
        "cuil": re.compile(r"\b\d{2}-\d{8}-\d{1}\b"),
        "cbu": re.compile(r"\b\d{22}\b"),
    }

    for entry in items:
        detalle = entry.detalle or {}
        detalle_str = str(detalle)

        for name, pattern in pii_patterns.items():
            matches = pattern.findall(detalle_str)
            assert not matches, (
                f"Found {name} pattern in audit entry {entry.id}: {matches}"
            )

        # Also check that suspicious key names are not present
        forbidden_keys = {"email", "dni", "cuil", "cbu", "alias_cbu"}
        for key in detalle:
            assert key.lower() not in forbidden_keys, (
                f"Forbidden key '{key}' found in audit entry {entry.id}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 11.11 Integration: Docente interacciones
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_docente_interacciones_with_data(audit_db_session: AsyncSession) -> None:
    """Docente interacciones should return aggregated metrics."""
    repo = AuditRepository(audit_db_session)

    # Create multiple entries for the same actor
    for i in range(5):
        await repo.create(
            {
                "tenant_id": TENANT_A,
                "actor_id": ACTOR_A,
                "accion": "CALIFICACIONES_IMPORTAR" if i % 2 == 0
                else "COMUNICACION_ENVIAR",
                "materia_id": MATERIA_X if i < 3 else MATERIA_Y,
                "detalle": {"index": i},
            }
        )

    result = await repo.get_docente_interacciones(
        tenant_id=TENANT_A, docente_id=ACTOR_A
    )

    assert result["docente_id"] == ACTOR_A
    assert result["total_acciones"] == 5
    assert "CALIFICACIONES_IMPORTAR" in result["por_accion"]
    assert "COMUNICACION_ENVIAR" in result["por_accion"]
    assert len(result["por_materia"]) >= 1
    assert len(result["ultimas_acciones"]) == 5


@pytest.mark.integration
@pytest.mark.asyncio
async def test_docente_interacciones_no_activity(
    audit_db_session: AsyncSession,
) -> None:
    """Docente with no activity should return zero counts."""
    repo = AuditRepository(audit_db_session)

    result = await repo.get_docente_interacciones(
        tenant_id=TENANT_A, docente_id=ACTOR_B
    )

    assert result["docente_id"] == ACTOR_B
    assert result["total_acciones"] == 0
    assert result["por_accion"] == {}
    assert result["por_materia"] == []
    assert result["ultimas_acciones"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# 11.12 Integration: Export
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_json(audit_db_session: AsyncSession) -> None:
    """JSON export should return audit entries as JSON array."""
    repo = AuditRepository(audit_db_session)

    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "CALIFICACIONES_IMPORTAR",
            "detalle": {"test": True},
        }
    )

    rows = await repo.export_search(tenant_id=TENANT_A)
    assert len(rows) >= 1

    row = rows[0]
    assert "id" in row
    assert "accion" in row
    assert "detalle" in row
    assert "fecha_hora" in row


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_csv_structure(audit_db_session: AsyncSession) -> None:
    """CSV export should contain headers and data."""
    repo = AuditRepository(audit_db_session)

    await repo.create(
        {
            "tenant_id": TENANT_A,
            "actor_id": ACTOR_A,
            "accion": "PADRON_CARGAR",
        }
    )

    rows = await repo.export_search(tenant_id=TENANT_A)
    assert len(rows) >= 1

    expected_keys = {
        "id", "tenant_id", "fecha_hora", "actor_id", "impersonado_id",
        "materia_id", "accion", "detalle", "filas_afectadas", "ip", "user_agent",
    }
    row_keys = set(rows[0].keys())
    assert expected_keys.issubset(row_keys), f"Missing keys: {expected_keys - row_keys}"


# ═══════════════════════════════════════════════════════════════════════════════
# 11.13 Integration: Permission enforcement
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
@pytest.mark.asyncio
async def test_permission_auditoria_ver_required(audit_db_session: AsyncSession) -> None:
    """The auditoria:ver permission should be required for all audit endpoints.

    This test verifies that the ``require_permission`` dependency rejects
    users without the ``auditoria:ver`` permission when accessing audit routes.
    """
    from app.api.v1.routers.admin_auditoria import router as audit_router
    from app.core.dependencies import get_current_user
    from app.core.permissions import ROL_PERMISSIONS
    from fastapi import FastAPI
    from httpx import ASGITransport, AsyncClient

    app = FastAPI()
    app.include_router(audit_router)

    # Override get_db to use our test session
    async def _override_db() -> AsyncGenerator[AsyncSession]:
        yield audit_db_session

    app.dependency_overrides[get_current_user] = lambda: {
        "id": ACTOR_A,
        "tenant_id": TENANT_A,
        "roles": ["ALUMNO"],  # ALUMNO does NOT have auditoria:ver
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Search endpoint
        response = await client.get("/api/admin/auditoria")
        assert response.status_code == 403, (
            f"Expected 403 for ALUMNO without auditoria:ver, got {response.status_code}"
        )

        # Export endpoint
        response = await client.get("/api/admin/auditoria/exportar")
        assert response.status_code == 403

        # Docente interacciones endpoint
        response = await client.get(
            f"/api/admin/auditoria/docentes/{ACTOR_A}/interacciones"
        )
        assert response.status_code == 403

    # Verify that COORDINADOR (who HAS auditoria:ver) can access
    app.dependency_overrides[get_current_user] = lambda: {
        "id": ACTOR_A,
        "tenant_id": TENANT_A,
        "roles": ["COORDINADOR"],
    }

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/admin/auditoria")
        assert response.status_code == 200, (
            f"Expected 200 for COORDINADOR with auditoria:ver, got {response.status_code}"
        )
