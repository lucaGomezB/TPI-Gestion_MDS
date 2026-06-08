"""Repositories for coloquio entities.

Provides tenant-scoped CRUD for:
- EvaluacionColoquio (convocatorias)
- ReservaColoquio (student reservations)
- ResultadoColoquio (exam results)
- Admin metrics queries
"""

from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluacion_coloquio import EvaluacionColoquio
from app.models.reserva_coloquio import ReservaColoquio
from app.models.resultado_coloquio import ResultadoColoquio


class EvaluacionColoquioRepository:
    """Tenant-scoped CRUD for EvaluacionColoquio."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> EvaluacionColoquio:
        """Create a new EvaluacionColoquio with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = EvaluacionColoquio(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> EvaluacionColoquio | None:
        """Get an EvaluacionColoquio by ID, scoped to tenant."""
        result = await self.session.execute(
            select(EvaluacionColoquio).where(
                EvaluacionColoquio.id == id,
                EvaluacionColoquio.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_materia(
        self, materia_id: str, activa: bool | None = None
    ) -> list[EvaluacionColoquio]:
        """List evaluaciones for a materia with optional activa filter."""
        stmt = select(EvaluacionColoquio).where(
            EvaluacionColoquio.tenant_id == self.tenant_id,
            EvaluacionColoquio.materia_id == materia_id,
        )
        if activa is not None:
            stmt = stmt.where(EvaluacionColoquio.activa == activa)
        stmt = stmt.order_by(EvaluacionColoquio.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_activas(self) -> list[EvaluacionColoquio]:
        """List all active evaluaciones for the tenant."""
        result = await self.session.execute(
            select(EvaluacionColoquio).where(
                EvaluacionColoquio.tenant_id == self.tenant_id,
                EvaluacionColoquio.activa == True,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def update(self, id: str, data: dict) -> EvaluacionColoquio | None:
        """Update an EvaluacionColoquio, scoped to tenant."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def update_dias(
        self, id: str, dias: list[dict]
    ) -> EvaluacionColoquio | None:
        """Update the dias JSONB field atomically."""
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        instance.dias = dias
        await self.session.flush()
        return instance

    async def count_activas(self) -> int:
        """Count active evaluaciones for the tenant."""
        result = await self.session.execute(
            select(func.count(EvaluacionColoquio.id)).where(
                EvaluacionColoquio.tenant_id == self.tenant_id,
                EvaluacionColoquio.activa == True,  # noqa: E712
            )
        )
        return result.scalar_one() or 0


class ReservaColoquioRepository:
    """Tenant-scoped CRUD for ReservaColoquio."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> ReservaColoquio:
        """Create a new ReservaColoquio with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = ReservaColoquio(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> ReservaColoquio | None:
        """Get a ReservaColoquio by ID, scoped to tenant."""
        result = await self.session.execute(
            select(ReservaColoquio).where(
                ReservaColoquio.id == id,
                ReservaColoquio.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_evaluacion(
        self, evaluacion_id: str
    ) -> list[ReservaColoquio]:
        """List all reservations for an evaluacion."""
        result = await self.session.execute(
            select(ReservaColoquio).where(
                ReservaColoquio.evaluacion_id == evaluacion_id,
                ReservaColoquio.tenant_id == self.tenant_id,
            )
        )
        return list(result.scalars().all())

    async def get_by_alumno_y_evaluacion(
        self, evaluacion_id: str, alumno_id: str
    ) -> ReservaColoquio | None:
        """Find a reservation by alumno and evaluacion."""
        result = await self.session.execute(
            select(ReservaColoquio).where(
                ReservaColoquio.evaluacion_id == evaluacion_id,
                ReservaColoquio.alumno_id == alumno_id,
                ReservaColoquio.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_reservas_por_dia(
        self, evaluacion_id: str, dia: date
    ) -> int:
        """Count reservations for a specific day in an evaluacion."""
        result = await self.session.execute(
            select(func.count(ReservaColoquio.id)).where(
                ReservaColoquio.evaluacion_id == evaluacion_id,
                ReservaColoquio.dia == dia,
                ReservaColoquio.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one() or 0

    async def count_activas(self) -> int:
        """Count all reservations for the tenant."""
        result = await self.session.execute(
            select(func.count(ReservaColoquio.id)).where(
                ReservaColoquio.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one() or 0


class ResultadoColoquioRepository:
    """Tenant-scoped CRUD for ResultadoColoquio."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def create(self, data: dict) -> ResultadoColoquio:
        """Create a new ResultadoColoquio with tenant_id auto-assigned."""
        data.setdefault("tenant_id", self.tenant_id)
        instance = ResultadoColoquio(**data)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def get_by_id(self, id: str) -> ResultadoColoquio | None:
        """Get a ResultadoColoquio by ID, scoped to tenant."""
        result = await self.session.execute(
            select(ResultadoColoquio).where(
                ResultadoColoquio.id == id,
                ResultadoColoquio.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_evaluacion(
        self, evaluacion_id: str
    ) -> list[ResultadoColoquio]:
        """List all results for an evaluacion."""
        result = await self.session.execute(
            select(ResultadoColoquio).where(
                ResultadoColoquio.evaluacion_id == evaluacion_id,
                ResultadoColoquio.tenant_id == self.tenant_id,
            )
        )
        return list(result.scalars().all())

    async def get_by_alumno_y_evaluacion(
        self, evaluacion_id: str, alumno_id: str
    ) -> ResultadoColoquio | None:
        """Find a result by alumno and evaluacion."""
        result = await self.session.execute(
            select(ResultadoColoquio).where(
                ResultadoColoquio.evaluacion_id == evaluacion_id,
                ResultadoColoquio.alumno_id == alumno_id,
                ResultadoColoquio.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_total(self) -> int:
        """Count all results for the tenant."""
        result = await self.session.execute(
            select(func.count(ResultadoColoquio.id)).where(
                ResultadoColoquio.tenant_id == self.tenant_id,
            )
        )
        return result.scalar_one() or 0


class ColoquioAdminRepository:
    """Admin-level queries for coloquio metrics across all materias."""

    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id

    async def get_metricas(self) -> dict:
        """Get aggregated coloquio metrics for the tenant.

        Returns:
            Dict with total_convocatorias, total_alumnos_importados,
            total_reservas_activas, total_resultados_registrados.
        """
        # Total active convocatorias
        convocatorias_result = await self.session.execute(
            select(func.count(EvaluacionColoquio.id)).where(
                EvaluacionColoquio.tenant_id == self.tenant_id,
                EvaluacionColoquio.activa == True,  # noqa: E712
            )
        )
        total_convocatorias = convocatorias_result.scalar_one() or 0

        # Total unique students imported (across all evaluaciones for tenant)
        # We approximate this via the total distinct alumno_id in reservas
        alumnos_result = await self.session.execute(
            select(func.count(func.distinct(ReservaColoquio.alumno_id))).where(
                ReservaColoquio.tenant_id == self.tenant_id,
            )
        )
        total_alumnos_importados = alumnos_result.scalar_one() or 0

        # Total active reservations
        reservas_result = await self.session.execute(
            select(func.count(ReservaColoquio.id)).where(
                ReservaColoquio.tenant_id == self.tenant_id,
            )
        )
        total_reservas_activas = reservas_result.scalar_one() or 0

        # Total registered results
        resultados_result = await self.session.execute(
            select(func.count(ResultadoColoquio.id)).where(
                ResultadoColoquio.tenant_id == self.tenant_id,
            )
        )
        total_resultados_registrados = resultados_result.scalar_one() or 0

        return {
            "total_convocatorias": total_convocatorias,
            "total_alumnos_importados": total_alumnos_importados,
            "total_reservas_activas": total_reservas_activas,
            "total_resultados_registrados": total_resultados_registrados,
        }
