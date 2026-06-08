"""Async email sender using SMTP (D-08).

Provides an async function to send emails via SMTP using the configured
settings from ``core/config.py``. Handles connection, TLS, authentication,
and distinguishes transient vs permanent failures.

Transient failures (connection errors, timeouts) — caller should retry.
Permanent failures (invalid email, auth rejected) — caller should NOT retry.
"""

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TransientEmailError(Exception):
    """A transient error occurred during email sending (should retry)."""


class PermanentEmailError(Exception):
    """A permanent error occurred during email sending (should NOT retry)."""


def _build_message(to: str, subject: str, body_html: str) -> str:
    """Build an RFC-compliant MIME email message.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body_html: HTML body content.

    Returns:
        The formatted message as a string.
    """
    settings = get_settings()
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html", "utf-8"))
    return msg.as_string()


async def send_email(to: str, subject: str, body_html: str) -> None:
    """Send an email via SMTP (async wrapper around synchronous smtplib).

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body_html: HTML body content.

    Raises:
        TransientEmailError: If a connection/timeout error occurs (retryable).
        PermanentEmailError: If auth fails or recipient is rejected (not retryable).
    """
    settings = get_settings()
    message = _build_message(to, subject, body_html)

    def _send() -> None:
        """Synchronous SMTP send (runs in thread pool)."""
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                # TLS
                if settings.smtp_use_tls:
                    server.starttls()

                # Authentication (if credentials provided)
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)

                # Send
                server.sendmail(settings.smtp_from_email, [to], message)
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPRecipientsRefused) as e:
            raise PermanentEmailError(str(e)) from e
        except (TimeoutError, ConnectionRefusedError, OSError, smtplib.SMTPException) as e:
            raise TransientEmailError(str(e)) from e

    try:
        await asyncio.to_thread(_send)
        logger.info("Email sent to %s (subject: %s)", _mask_email(to), subject)
    except (TransientEmailError, PermanentEmailError):
        raise


def _mask_email(email: str) -> str:
    """Mask an email for logging and API responses (D-13).

    Pattern: first char + *** + domain.
    E.g. ``j***@example.com``

    If the email has no ``@`` or the local part is empty, returns the original.

    Args:
        email: The email address to mask.

    Returns:
        Masked email string.
    """
    if "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if not local:
        return email
    return local[0] + "***@" + domain
