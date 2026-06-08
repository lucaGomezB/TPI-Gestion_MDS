"""Service layer for encuentro management with business rules.

Encapsulates business logic:
- Slot recurrente creation with eager N-instance generation (RN-13)
- Unique encuentro creation (slot_id=null)
- Individual instance editing (estado, meet_url, video_url, comentario) (RN-14)
- HTML/Markdown embed snippet generation for Moodle
- Cross-tenant validation for referenced entities
"""

import html
from datetime import date, timedelta

from fastapi import HTTPException
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_404_NOT_FOUND,
)

from app.core.unit_of_work import UnitOfWork
from app.schemas.encuentros import (
    EmbedResponse,
    InstanciaEncuentroCreate,
    InstanciaEncuentroResponse,
    InstanciaEncuentroUpdate,
    SlotEncuentroCreate,
    SlotEncuentroResponse,
)

# ── Day-of-week mapping ──────────────────────────────────────────────────────

DIAS_SEMANA_MAP = {
    "Domingo": 0,
    "Lunes": 1,
    "Martes": 2,
    "Miercoles": 3,
    "Jueves": 4,
    "Viernes": 5,
    "Sabado": 6,
}


def _next_weekday(from_date: date, target_dow: int) -> date:
    """Return the next occurrence of ``target_dow`` on or after ``from_date``."""
    days_ahead = target_dow - from_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


class EncuentroService:
    """Business logic for encuentros (slots and instances)."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.tenant_id = uow._tenant_id or ""

    async def crear_slot_recurrente(
        self, data: SlotEncuentroCreate
    ) -> tuple[SlotEncuentroResponse, list[InstanciaEncuentroResponse]]:
        """Create a recurrent slot and eagerly generate N InstanciaEncuentro records.

        Args:
            data: The slot creation data with recurrence pattern.

        Returns:
            A tuple of (slot_response, list_of_instance_responses).

        Raises:
            HTTPException(404): If the referenced materia is not found.
            HTTPException(422): If the recurrence parameters are invalid.
        """
        # Verify materia exists in tenant
        materia = await self.uow.materia.get_by_id(data.materia_id)
        if materia is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )

        slot_data = data.model_dump()
        slot = await self.uow.slot_encuentro.create(slot_data)

        # Generate instances eagerly
        instances = []
        if slot.cant_semanas > 0:
            # Weekly recurrence: generate N instances starting from fecha_inicio
            target_dow = DIAS_SEMANA_MAP.get(slot.dia_semana, slot.fecha_inicio.weekday())
            current_date = _next_weekday(slot.fecha_inicio, target_dow)

            for _ in range(slot.cant_semanas):
                instances_data = {
                    "slot_id": slot.id,
                    "materia_id": slot.materia_id,
                    "fecha": current_date,
                    "hora": slot.hora,
                    "titulo": slot.titulo,
                    "meet_url": slot.meet_url,
                }
                instances.append(instances_data)
                current_date += timedelta(days=7)
        elif slot.fecha_unica is not None:
            # Single date (fecha_unica)
            instances_data = {
                "slot_id": slot.id,
                "materia_id": slot.materia_id,
                "fecha": slot.fecha_unica,
                "hora": slot.hora,
                "titulo": slot.titulo,
                "meet_url": slot.meet_url,
            }
            instances.append(instances_data)

        created_instances = await self.uow.instancia_encuentro.bulk_create(instances)

        return (
            SlotEncuentroResponse.model_validate(slot),
            [InstanciaEncuentroResponse.model_validate(i) for i in created_instances],
        )

    async def crear_encuentro_unico(
        self, data: InstanciaEncuentroCreate
    ) -> InstanciaEncuentroResponse:
        """Create a single encuentro instance without a slot (slot_id=null).

        Args:
            data: The instance creation data.

        Returns:
            The created InstanciaEncuentro response.

        Raises:
            HTTPException(404): If the referenced materia is not found.
        """
        materia = await self.uow.materia.get_by_id(data.materia_id)
        if materia is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Materia not found",
            )

        instance = await self.uow.instancia_encuentro.create(data.model_dump())
        return InstanciaEncuentroResponse.model_validate(instance)

    async def editar_instancia(
        self, id: str, data: InstanciaEncuentroUpdate
    ) -> InstanciaEncuentroResponse:
        """Update an individual instance's mutable fields per RN-14.

        Args:
            id: The instance UUID.
            data: The fields to update (estado, meet_url, video_url, comentario).

        Returns:
            The updated InstanciaEncuentro response.

        Raises:
            HTTPException(404): If the instance is not found.
        """
        update_dict = data.model_dump(exclude_unset=True)
        if not update_dict:
            # Nothing to update — return current state
            instance = await self.uow.instancia_encuentro.get_by_id(id)
            if instance is None:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail="Instancia de encuentro not found",
                )
            return InstanciaEncuentroResponse.model_validate(instance)

        instance = await self.uow.instancia_encuentro.update(id, update_dict)
        if instance is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Instancia de encuentro not found",
            )
        return InstanciaEncuentroResponse.model_validate(instance)

    async def generar_embed(
        self,
        materia_id: str,
        estado: str | None = None,
        limit: int = 20,
    ) -> EmbedResponse:
        """Generate HTML table and Markdown snippet for Moodle embedding.

        Args:
            materia_id: The materia UUID to generate embed for.
            estado: Optional estado filter.
            limit: Maximum instances to include.

        Returns:
            An EmbedResponse with html, markdown, and total fields.
        """
        instances = await self.uow.instancia_encuentro.list_by_materia(
            materia_id=materia_id,
            estado=estado,
        )
        instances = instances[:limit]

        if not instances:
            return EmbedResponse(
                html="<p>No hay encuentros programados.</p>",
                markdown="_No hay encuentros programados._",
                total=0,
            )

        # HTML table
        rows_html = ""
        for inst in instances:
            estado_class = "programado"
            if inst.estado == "Realizado":
                estado_class = "realizado"
            elif inst.estado == "Cancelado":
                estado_class = "cancelado"
            meet = (
                f'<a href="{html.escape(inst.meet_url)}">Enlace</a>'
                if inst.meet_url else "—"
            )
            rows_html += (
                f"<tr>"
                f"<td>{html.escape(inst.titulo)}</td>"
                f"<td>{inst.fecha.isoformat()}</td>"
                f"<td>{inst.hora.isoformat()[:5]}</td>"
                f"<td class=\"{estado_class}\">{html.escape(inst.estado)}</td>"
                f"<td>{meet}</td>"
                f"</tr>\n"
            )

        html_table = (
            f"<table>\n"
            f"<thead><tr><th>Titulo</th><th>Fecha</th><th>Hora</th>"
            f"<th>Estado</th><th>Enlace</th></tr></thead>\n"
            f"<tbody>\n{rows_html}</tbody>\n</table>"
        )

        # Markdown list
        md_items = ""
        for inst in instances:
            meet = f" ([Enlace]({inst.meet_url}))" if inst.meet_url else ""
            md_items += (
                f"- **{html.escape(inst.titulo)}** — "
                f"{inst.fecha.isoformat()} {inst.hora.isoformat()[:5]}"
                f" [{inst.estado}]{meet}\n"
            )

        markdown = f"### Proximos Encuentros\n\n{md_items}"

        return EmbedResponse(
            html=html_table,
            markdown=markdown,
            total=len(instances),
        )
