"""Async worker for processing the communications queue (D-07).

The worker is a standalone async loop that polls the queue at a configurable
interval, processes ready lotes, sends emails via SMTP, and updates statuses.

Worker loop (every N seconds, default 30):
  1. Query Lote where estado = Pendiente (or AprobacionPendiente -> skip)
  2. For each ready Lote:
     a. Set Lote.estado = Enviando
     b. Process all Pendiente communications for this lote
     c. Update counters and final estado

Retry policy:
  - Transient errors (connection, timeout): retry up to WORKER_MAX_RETRIES
  - Permanent errors (auth, invalid email): mark as Error, no retry
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models.comunicacion import (
    Comunicacion,
    EstadoComunicacion,
    EstadoLote,
    LoteComunicacion,
)
from app.services.email_sender import (
    PermanentEmailError,
    TransientEmailError,
    send_email,
)

logger = logging.getLogger("communication_worker")


async def process_lote(
    session: AsyncSession,
    lote: LoteComunicacion,
    max_retries: int = 3,
) -> tuple[int, int]:
    """Process all pending communications for a single lote.

    Steps:
    1. Fetch all Pendiente communications for this lote.
    2. For each, attempt to send via SMTP.
    3. Update Comunicacion status after each attempt.
    4. Return aggregated (enviados, fallidos) counts.

    Args:
        session: Active DB session.
        lote: The LoteComunicacion to process.
        max_retries: Maximum retry attempts for transient failures.

    Returns:
        Tuple of (enviados, fallidos) counts.
    """
    # Fetch pending communications for this lote
    result = await session.execute(
        select(Comunicacion).where(
            Comunicacion.lote_id == lote.id,
            Comunicacion.estado == EstadoComunicacion.pendiente.value,
        )
    )
    comunicaciones: list[Comunicacion] = list(result.scalars().all())

    if not comunicaciones:
        logger.info("Lote %s has no pending communications", lote.id)
        return 0, 0

    enviados = 0
    fallidos = 0

    for com in comunicaciones:
        try:
            # Set to Enviando
            com.estado = EstadoComunicacion.enviando.value
            await session.flush()

            # Send email
            await send_email(
                to=com.destinatario,  # EncryptedString auto-decrypts
                subject=com.asunto,
                body_html=com.cuerpo,
            )

            # Success
            com.estado = EstadoComunicacion.enviado.value
            com.enviado_at = datetime.now(timezone.utc)
            com.error_msg = None
            enviados += 1
            logger.debug("Sent communication %s for lote %s", com.id, lote.id)

        except PermanentEmailError as e:
            # Permanent failure — do not retry
            com.estado = EstadoComunicacion.error.value
            com.error_msg = f"Permanent: {e}"
            fallidos += 1
            logger.warning("Permanent failure for %s: %s", com.id, e)

        except TransientEmailError as e:
            # Transient failure — retry if under max_retries
            com.retry_count = com.retry_count + 1
            if com.retry_count >= max_retries:
                com.estado = EstadoComunicacion.error.value
                com.error_msg = f"Max retries ({max_retries}) exceeded: {e}"
                fallidos += 1
                logger.warning("Max retries exceeded for %s: %s", com.id, e)
            else:
                # Reset to Pendiente for next poll cycle
                com.estado = EstadoComunicacion.pendiente.value
                com.error_msg = f"Retry {com.retry_count}/{max_retries}: {e}"
                # Don't count as fallido yet — will be retried
                logger.info(
                    "Will retry %s (attempt %d/%d): %s",
                    com.id, com.retry_count, max_retries, e,
                )

        except Exception as e:
            # Unexpected error — mark as permanent
            com.estado = EstadoComunicacion.error.value
            com.error_msg = f"Unexpected: {e}"
            fallidos += 1
            logger.exception("Unexpected error for %s", com.id)

        await session.flush()

    return enviados, fallidos


async def process_queue(session: AsyncSession) -> None:
    """Process all ready lotes in the queue.

    Queries lotes in Pendiente or Enviando state and processes them.
    Lotes in AprobacionPendiente are skipped (awaiting admin decision).
    """
    settings = get_settings()
    max_retries = settings.worker_max_retries

    # Find ready lotes (Pendiente or Enviando)
    result = await session.execute(
        select(LoteComunicacion).where(
            LoteComunicacion.estado.in_([
                EstadoLote.pendiente.value,
                EstadoLote.enviando.value,
            ]),
        )
    )
    lotes: list[LoteComunicacion] = list(result.scalars().all())

    if not lotes:
        logger.debug("No ready lotes found")
        return

    logger.info("Found %d ready lotes to process", len(lotes))

    for lote in lotes:
        # Skip lotes pending approval
        if lote.estado == EstadoLote.aprobacion_pendiente.value:
            logger.debug("Skipping lote %s (pending approval)", lote.id)
            continue

        # Mark as Enviando
        if lote.estado != EstadoLote.enviando.value:
            lote.estado = EstadoLote.enviando.value
            await session.flush()

        # Process
        enviados, fallidos = await process_lote(session, lote, max_retries)

        # Update lote counters and final estado
        if enviados > 0 or fallidos > 0:
            new_enviados = lote.enviados + enviados
            new_fallidos = lote.fallidos + fallidos
            lote.enviados = new_enviados
            lote.fallidos = new_fallidos

            # Determine final estado
            total_processed = new_enviados + new_fallidos
            if total_processed >= lote.total:
                if new_fallidos == 0:
                    lote.estado = EstadoLote.completado.value
                elif new_enviados == 0:
                    lote.estado = EstadoLote.cancelado.value
                else:
                    lote.estado = EstadoLote.parcial.value
            # else: still processing, remain Enviando

            await session.flush()
            logger.info(
                "Lote %s: enviados=%d fallidos=%d estado=%s",
                lote.id, new_enviados, new_fallidos, lote.estado,
            )


async def run_worker(interval: int | None = None) -> None:
    """Main worker loop — polls the queue at a configurable interval.

    Runs indefinitely until cancelled. Handles graceful shutdown via
    asyncio.CancelledError.

    Args:
        interval: Poll interval in seconds. Defaults to WORKER_POLL_INTERVAL
            from settings.
    """
    settings = get_settings()
    poll_interval = interval or settings.worker_poll_interval

    logger.info(
        "Communication worker started (poll interval=%ds, max_retries=%d)",
        poll_interval, settings.worker_max_retries,
    )

    while True:
        try:
            async for session in get_session():
                try:
                    await process_queue(session)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        except asyncio.CancelledError:
            logger.info("Communication worker received shutdown signal")
            break
        except Exception as e:
            logger.exception("Communication worker error: %s", e)

        await asyncio.sleep(poll_interval)

    logger.info("Communication worker stopped")
