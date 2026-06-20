"""Service layer for Coloquio management with business rules.

Encapsulates business logic:
- Creacion de convocatorias con validacion de materia y dias
- Importacion de alumnos desde padron activo
- Reserva de turnos con cupos auto-decrecientes
- Agenda consolidada con reservas por dia
- Registro de resultados
- Metricas admin
"""

from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_409_CONFLICT

from app.core.action_codes import AccionAuditoria
from app.core.unit_of_work import UnitOfWork
from app.schemas.coloquios import (
    AgendaColoquioResponse,
    AlumnoImportado,
    ConvocatoriaEnAgenda,
    DiaAgenda,
    DiaColoquioResponse,
    EvaluacionColoquioCreate,
    EvaluacionColoquioResponse,
    ImportarAlumnosRequest,
    ImportarAlumnosResponse,
    MetricasColoquioResponse,
    ReservaColoquioCreate,
    ReservaColoquioResponse,
    ReservaEnAgenda,
    ResultadoColoquioCreate,
    ResultadoColoquioResponse,
)


class ColoquioService:
    """Business logic for coloquio CRUD and operations."""

    def __init__(self, uow: UnitOfWork, current_user: dict):
        self.uow = uow
        self.current_user = current_user
        self.tenant_id = current_user.get("tenant_id", "")

    # ── Crear convocatoria ────────────────────────────────────────────────

    async def crear_convocatoria(
        self, materia_id: str, data: EvaluacionColoquioCreate
    ) -> EvaluacionColoquioResponse:
        """Create a new coloquio convocatoria.

        Args:
            materia_id: The materia UUID.
            data: The convocatoria creation data.

        Returns:
            The created EvaluacionColoquioResponse.

        Raises:
            HTTPException(404): If the materia is not found.
        """
        # Verify materia exists in tenant
        materia = await self.uow.materia.get_by_id(materia_id)
        if materia is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )

        # Build dias data with reservados=0 for each day
        dias_data = [
            {
                "fecha": d.fecha,
                "cupos": d.cupos,
                "reservados": 0,
            }
            for d in data.dias
        ]

        create_data = {
            "materia_id": materia_id,
            "titulo": data.titulo,
            "dias": dias_data,
            "creado_por": self.current_user.get("id"),
            "activa": data.activa,
        }
        instance = await self.uow.coloquio_evaluacion.create(create_data)

        # Log audit
        await self.uow.audit.create(
            {
                "accion": AccionAuditoria.COLOQUIO_CREAR.value,
                "actor_id": self.current_user.get("id"),
                "tenant_id": self.tenant_id,
                "materia_id": materia_id,
                "filas_afectadas": 1,
            }
        )

        return EvaluacionColoquioResponse.model_validate(instance)

    # ── Listar convocatorias ──────────────────────────────────────────────

    async def listar_convocatorias(
        self, materia_id: str
    ) -> list[EvaluacionColoquioResponse]:
        """List active coloquio convocatorias for a materia."""
        instances = await self.uow.coloquio_evaluacion.list_by_materia(
            materia_id=materia_id, activa=True
        )
        return [
            EvaluacionColoquioResponse.model_validate(i) for i in instances
        ]

    # ── Importar alumnos ──────────────────────────────────────────────────

    async def importar_alumnos(
        self, materia_id: str, data: ImportarAlumnosRequest
    ) -> ImportarAlumnosResponse:
        """Import students from the active materia padron into a coloquio.

        Reads the active padron entries for the materia and links them
        to the specified evaluacion.

        Args:
            materia_id: The materia UUID.
            data: Request with evaluacion_id.

        Returns:
            ImportarAlumnosResponse with list of imported alumnos.

        Raises:
            HTTPException(404): If materia or evaluacion not found.
            HTTPException(400): If materia has no active padron.
        """
        # Verify materia exists
        materia = await self.uow.materia.get_by_id(materia_id)
        if materia is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )

        # Verify evaluacion exists and belongs to this materia
        evaluacion = await self.uow.coloquio_evaluacion.get_by_id(
            data.evaluacion_id
        )
        if evaluacion is None or evaluacion.materia_id != materia_id:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Evaluacion not found for this materia",
            )

        # Get active padron entries
        entries = await self.uow.padron.get_active_entries(materia_id)
        if not entries:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="La materia no tiene un padron activo",
            )

        alumnos = [
            AlumnoImportado(
                usuario_id=e.usuario_id,
                nombre=e.nombre,
                apellidos=e.apellidos,
                email=e.email,
            )
            for e in entries
        ]

        return ImportarAlumnosResponse(
            evaluacion_id=data.evaluacion_id,
            alumnos_importados=alumnos,
            total_importados=len(alumnos),
        )

    # ── Reservar turno ────────────────────────────────────────────────────

    async def reservar_turno(
        self, evaluacion_id: str, data: ReservaColoquioCreate
    ) -> ReservaColoquioResponse:
        """Reserve a coloquio turn for the current student.

        Validates cupos disponibles, no duplicate reservation, creates the
        reservation and decrements the cupos counter in the JSONB dias field.

        Args:
            evaluacion_id: The evaluacion UUID.
            data: The reservation data with dia.

        Returns:
            The created ReservaColoquioResponse.

        Raises:
            HTTPException(404): If evaluacion not found.
            HTTPException(409): If no cupos available or duplicate reservation.
        """
        # Verify evaluacion exists
        evaluacion = await self.uow.coloquio_evaluacion.get_by_id(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Evaluacion not found",
            )

        # Check no duplicate reservation
        alumno_id = self.current_user.get("id", "")
        existing = await self.uow.coloquio_reserva.get_by_alumno_y_evaluacion(
            evaluacion_id, alumno_id
        )
        if existing is not None:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail="El alumno ya tiene una reserva para esta convocatoria",
            )

        # Find the day in the evaluacion's dias JSONB and check cupos
        target_date = data.dia
        dias = list(evaluacion.dias) if evaluacion.dias else []
        dia_encontrado = None
        dias_actualizados: list[dict] = []

        for dia_entry in dias:
            entry = dict(dia_entry)
            if entry["fecha"] == target_date:
                if entry.get("reservados", 0) >= entry.get("cupos", 0):
                    raise HTTPException(
                        status_code=HTTP_409_CONFLICT,
                        detail="No hay cupos disponibles para esa fecha",
                    )
                entry["reservados"] = entry.get("reservados", 0) + 1
                dia_encontrado = entry
            dias_actualizados.append(entry)

        if dia_encontrado is None:
            raise HTTPException(
                status_code=HTTP_400_BAD_REQUEST,
                detail="La fecha solicitada no esta disponible en esta convocatoria",
            )

        # Update the evaluacion dias
        await self.uow.coloquio_evaluacion.update_dias(
            evaluacion_id, dias_actualizados
        )

        # Create reservation
        create_data = {
            "evaluacion_id": evaluacion_id,
            "alumno_id": alumno_id,
            "dia": target_date,
            "confirmada": False,
        }
        instance = await self.uow.coloquio_reserva.create(create_data)

        # Log audit
        await self.uow.audit.create(
            {
                "accion": AccionAuditoria.COLOQUIO_RESERVAR.value,
                "actor_id": alumno_id,
                "tenant_id": self.tenant_id,
                "materia_id": evaluacion.materia_id,
                "filas_afectadas": 1,
            }
        )

        return ReservaColoquioResponse.model_validate(instance)

    # ── Obtener agenda ────────────────────────────────────────────────────

    async def obtener_agenda(
        self, evaluacion_id: str
    ) -> AgendaColoquioResponse:
        """Get consolidated agenda with reservas per day.

        Args:
            evaluacion_id: The evaluacion UUID.

        Returns:
            AgendaColoquioResponse with days and reservations.

        Raises:
            HTTPException(404): If evaluacion not found.
        """
        evaluacion = await self.uow.coloquio_evaluacion.get_by_id(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Evaluacion not found",
            )

        # ── Materia name ─────────────────────────────────────────────────
        materia = await self.uow.materia.get_by_id(evaluacion.materia_id)
        materia_nombre = materia.nombre if materia else "Sin materia"

        # Get all reservations for this evaluacion
        reservas = await self.uow.coloquio_reserva.list_by_evaluacion(
            evaluacion_id
        )

        # ── Build alumno name lookup ──────────────────────────────────────
        alumno_ids = {r.alumno_id for r in reservas}
        alumno_lookup: dict[str, dict[str, str]] = {}
        for alumno_id in alumno_ids:
            usuario = await self.uow.admin_usuarios.get(alumno_id)
            if usuario:
                alumno_lookup[alumno_id] = {
                    "nombre": usuario.nombre,
                    "apellido": usuario.apellidos,
                }

        # Group reservations by fecha
        reservas_por_fecha: dict[str, list[ReservaEnAgenda]] = {}
        for reserva in reservas:
            fecha_str = (
                reserva.dia.isoformat()
                if hasattr(reserva.dia, "isoformat")
                else str(reserva.dia)
            )
            if fecha_str not in reservas_por_fecha:
                reservas_por_fecha[fecha_str] = []
            alumno_info = alumno_lookup.get(reserva.alumno_id, {})
            reservas_por_fecha[fecha_str].append(
                ReservaEnAgenda(
                    id=reserva.id,
                    alumno_id=reserva.alumno_id,
                    alumno_nombre=alumno_info.get("nombre"),
                    alumno_apellido=alumno_info.get("apellido"),
                    confirmada=reserva.confirmada,
                )
            )

        # Build days from evaluacion.dias JSONB
        dias_list: list[DiaAgenda] = []
        for dia_entry in (evaluacion.dias or []):
            entry = dict(dia_entry)
            fecha_str = str(entry["fecha"])
            cupos = entry.get("cupos", 0)
            reservados = entry.get("reservados", 0)
            day_reservas = reservas_por_fecha.get(fecha_str, [])
            dias_list.append(
                DiaAgenda(
                    id=fecha_str,
                    fecha=fecha_str,
                    cupos=cupos,
                    reservados=reservados,
                    libre=cupos - reservados,
                    reservas=day_reservas,
                )
            )

        # Sort by fecha ascending
        dias_list.sort(key=lambda d: d.fecha)

        return AgendaColoquioResponse(
            convocatoria=ConvocatoriaEnAgenda(
                id=evaluacion_id,
                materia_nombre=materia_nombre,
                titulo=evaluacion.titulo,
                activa=evaluacion.activa,
            ),
            dias=dias_list,
        )

    # ── Registrar resultado ───────────────────────────────────────────────

    async def registrar_resultado(
        self, evaluacion_id: str, data: ResultadoColoquioCreate
    ) -> ResultadoColoquioResponse:
        """Register a student's coloquio result.

        Args:
            evaluacion_id: The evaluacion UUID.
            data: The result data (alumno_id, nota, aprobado).

        Returns:
            The created ResultadoColoquioResponse.

        Raises:
            HTTPException(404): If evaluacion not found.
            HTTPException(409): If duplicate result.
        """
        # Verify evaluacion exists
        evaluacion = await self.uow.coloquio_evaluacion.get_by_id(evaluacion_id)
        if evaluacion is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Evaluacion not found",
            )

        # Check no duplicate result
        existing = await self.uow.coloquio_resultado.get_by_alumno_y_evaluacion(
            evaluacion_id, data.alumno_id
        )
        if existing is not None:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail="El alumno ya tiene un resultado registrado",
            )

        create_data = {
            "evaluacion_id": evaluacion_id,
            "alumno_id": data.alumno_id,
            "nota": data.nota,
            "aprobado": data.aprobado,
            "registrado_por": self.current_user.get("id"),
        }
        instance = await self.uow.coloquio_resultado.create(create_data)

        # Log audit
        await self.uow.audit.create(
            {
                "accion": AccionAuditoria.COLOQUIO_RESULTADO.value,
                "actor_id": self.current_user.get("id"),
                "tenant_id": self.tenant_id,
                "materia_id": evaluacion.materia_id,
                "filas_afectadas": 1,
            }
        )

        return ResultadoColoquioResponse.model_validate(instance)

    # ── Obtener metricas ──────────────────────────────────────────────────

    async def obtener_metricas(self) -> MetricasColoquioResponse:
        """Get admin metrics for coloquio overview.

        Returns:
            MetricasColoquioResponse with aggregated counts.
        """
        metricas = await self.uow.coloquio_admin.get_metricas()
        return MetricasColoquioResponse(**metricas)
