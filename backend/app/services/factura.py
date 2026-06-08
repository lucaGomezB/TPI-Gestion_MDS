"""FacturaService — invoice upload, history, admin management, and lifecycle.

Encapsulates:
- RN-35: Facturadores excluded from liquidacion general (flag checked here)
- RN-39: Only Pendiente and Abonada states
- RN-40: Factura structure: docente, periodo, detalle, archivo, fecha carga,
  tamano, estado, fecha pago

File storage follows the same pattern as ProgramaMateria (E16): local filesystem
with UUID-based filenames and opaque references.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
)

from app.core.config import get_settings
from app.core.unit_of_work import UnitOfWork
from app.models.factura import EstadoFactura, Factura
from app.models.usuario import Usuario
from app.schemas.factura import (
    FacturaCreate,
    FacturaDetailResponse,
    FacturaListResponse,
    FacturaResponse,
)

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────

ALLOWED_CONTENT_TYPE = "application/pdf"
MAX_UPLOAD_SIZE_MB = 10


# ── Pure helper functions ────────────────────────────────────────────────


def _generate_file_path(original_filename: str) -> tuple[str, str]:
    """Generate a storage path and filename for an uploaded PDF.

    Args:
        original_filename: The original filename from the upload.

    Returns:
        Tuple of (directory_path, stored_filename).
    """
    upload_dir = os.path.join(
        get_settings().upload_dir,
        "facturas",
    )
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    ext = ".pdf"  # Always preserve PDF extension
    saved_name = f"{file_id}{ext}"
    return upload_dir, saved_name


def _validate_pdf(filename: str, content: bytes) -> None:
    """Validate that the uploaded file is a valid PDF.

    Checks:
    - File extension is .pdf (case-insensitive)
    - Content starts with PDF magic bytes (%PDF)
    - File size does not exceed max limit

    Args:
        filename: The original filename.
        content: The raw file bytes.

    Raises:
        HTTPException(400): If validation fails.
    """
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="File content does not appear to be a valid PDF",
        )

    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {MAX_UPLOAD_SIZE_MB} MB",
        )


def _iso_or_str(val) -> str:
    """Convert a datetime-like value to ISO string."""
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


def _as_date_str(dt: datetime | None) -> str | None:
    """Convert a datetime to ISO string, or None."""
    if dt is None:
        return None
    return dt.isoformat()


# ── Model → Schema helpers ───────────────────────────────────────────────


def _to_response(factura: Factura) -> FacturaResponse:
    """Convert a Factura ORM instance to a response schema."""
    return FacturaResponse(
        id=factura.id,
        tenant_id=factura.tenant_id,
        usuario_id=factura.usuario_id,
        periodo=factura.periodo,
        detalle=factura.detalle,
        referencia_archivo=factura.referencia_archivo,
        tamano_kb=float(factura.tamano_kb),
        estado=factura.estado,
        cargada_at=_iso_or_str(factura.cargada_at),
        abonada_at=_as_date_str(factura.abonada_at),
    )


def _to_detail_response(
    factura: Factura,
    descargar_url: str | None = None,
) -> FacturaDetailResponse:
    """Convert a Factura ORM instance to a detail response with download URL."""
    base = _to_response(factura)
    return FacturaDetailResponse(
        **base.model_dump(),
        descargar_url=descargar_url,
    )


# ── Service class ────────────────────────────────────────────────────────


class FacturaService:
    """Business logic for teacher invoice management.

    Args:
        uow: The ``UnitOfWork`` instance for data access.
        actor_id: The current user's UUID (for audit logging).
    """

    def __init__(self, uow: UnitOfWork, actor_id: str | None = None):
        self.uow = uow
        self.actor_id = actor_id
        self.repo = uow.factura

    # ── Upload (RF-61) ────────────────────────────────────────────────

    async def subir_factura(
        self,
        usuario_id: str,
        periodo: str,
        detalle: str,
        archivo_bytes: bytes,
        nombre_archivo: str,
    ) -> FacturaResponse:
        """Upload a new invoice PDF for a teacher.

        Validates:
        1. The user has ``facturador=true`` in the DB (RN-35 gate).
        2. The file is a valid PDF (content type and size).
        3. Saves the file to local storage with UUID name.
        4. Creates a Factura record with estado=Pendiente.

        Args:
            usuario_id: The teacher's UUID.
            periodo: Period in YYYY-MM format.
            detalle: Description of the invoice.
            archivo_bytes: Raw PDF file bytes.
            nombre_archivo: Original filename from upload.

        Returns:
            The created FacturaResponse.

        Raises:
            HTTPException(403): If the user is not a facturador.
            HTTPException(400): If the file is not a valid PDF or exceeds size.
        """
        # 1. Validate facturador flag (RN-35)
        stmt = select(Usuario).where(
            Usuario.id == usuario_id,
            Usuario.tenant_id == self.uow._tenant_id,
        )
        result = await self.uow._session.execute(stmt)
        usuario = result.scalar_one_or_none()

        if usuario is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail="Usuario not found",
            )

        if not usuario.facturador:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="User is not authorized to upload invoices (facturador=false)",
            )

        # 2. Validate PDF
        _validate_pdf(nombre_archivo, archivo_bytes)

        # 3. Store file
        upload_dir, saved_name = _generate_file_path(nombre_archivo)
        file_path = os.path.join(upload_dir, saved_name)
        with open(file_path, "wb") as f:
            f.write(archivo_bytes)

        # 4. Create Factura record
        tamano_kb = round(len(archivo_bytes) / 1024, 2)

        create_data = FacturaCreate(
            usuario_id=usuario_id,
            periodo=periodo,
            detalle=detalle,
            referencia_archivo=file_path,
            tamano_kb=tamano_kb,
        )
        instance = await self.repo.create(create_data.model_dump())
        logger.info(
            "Factura created: id=%s usuario=%s periodo=%s size=%.2fKB",
            instance.id, usuario_id, periodo, tamano_kb,
        )

        return _to_response(instance)

    # ── Own history ───────────────────────────────────────────────────

    async def get_historial(
        self,
        usuario_id: str,
        periodo: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> FacturaListResponse:
        """Return paginated factura history for the authenticated teacher.

        Args:
            usuario_id: The teacher's UUID.
            periodo: Optional YYYY-MM filter.
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Paginated list of FacturaResponse items.
        """
        items, total = await self.repo.find_by_usuario(
            usuario_id=usuario_id,
            periodo=periodo,
            page=page,
            page_size=page_size,
        )

        responses = [_to_response(f) for f in items]

        return FacturaListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── Admin view (F10.5) ────────────────────────────────────────────

    async def get_admin_view(
        self,
        estado: str | None = None,
        periodo: str | None = None,
        usuario_id: str | None = None,
        q: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> FacturaListResponse:
        """Return paginated facturas for admin with combinable filters.

        Args:
            estado: Filter by estado (Pendiente/Abonada).
            periodo: Filter by YYYY-MM period.
            usuario_id: Filter by specific usuario.
            q: Search on detalle (LIKE %q%).
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Paginated list of FacturaResponse items.
        """
        items, total = await self.repo.find_all(
            estado=estado,
            periodo=periodo,
            usuario_id=usuario_id,
            q=q,
            page=page,
            page_size=page_size,
        )

        responses = [_to_response(f) for f in items]

        return FacturaListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── Single lookup ────────────────────────────────────────────────

    async def get_factura(self, id: str) -> Factura:
        """Return a single factura by ID, scoped by tenant.

        Args:
            id: The factura UUID.

        Returns:
            The Factura instance.

        Raises:
            HTTPException(404): If not found.
        """
        factura = await self.repo.find_by_id(id)
        if factura is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Factura[{id}] not found",
            )
        return factura

    # ── Abonar lifecycle (RN-39) ──────────────────────────────────────

    async def abonar(
        self,
        id: str,
        descargar: bool = False,
    ) -> FacturaResponse | FacturaDetailResponse:
        """Mark a factura as Abonada, setting abonada_at.

        Sets ``estado=Abonada`` and ``abonada_at=now()``.
        Raises 409 if already Abonada, 404 if not found.

        If ``descargar=True``, returns a FacturaDetailResponse with
        a download URL for the PDF file.

        Args:
            id: The factura UUID.
            descargar: If True, include download URL in response.

        Returns:
            The updated FacturaResponse or FacturaDetailResponse.
        """
        factura = await self.repo.find_by_id(id)
        if factura is None:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND,
                detail=f"Factura[{id}] not found",
            )

        if factura.estado == EstadoFactura.ABONADA.value:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT,
                detail=f"Factura[{id}] is already paid",
            )

        factura.estado = EstadoFactura.ABONADA.value
        factura.abonada_at = datetime.now(timezone.utc)
        await self.repo.save(factura)

        logger.info(
            "Factura abonada: id=%s usuario=%s periodo=%s",
            factura.id, factura.usuario_id, factura.periodo,
        )

        if descargar:
            descargar_url = f"/api/admin/facturas/{factura.id}/descargar"
            return _to_detail_response(factura, descargar_url=descargar_url)

        return _to_response(factura)
