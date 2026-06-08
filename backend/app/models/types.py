"""Custom SQLAlchemy TypeDecorators and domain enums.

Currently provides:
- ``EncryptedString``: Transparent AES-256-GCM encryption at the ORM layer.
  Plaintext is encrypted on write (via ``process_bind_param``) and
  decrypted on read (via ``process_result_value``).
- ``RolDocente``: Enum of valid teaching team roles matching the existing
  :mod:`app.models.rol` role names.
"""

import enum

from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator

from app.core.security import aes_decrypt, aes_encrypt, get_encryption_key


class EncryptedString(TypeDecorator):
    """SQLAlchemy type that transparently encrypts/decrypts string values.

    Uses AES-256-GCM via ``core.security``. Values are stored as ``TEXT``
    columns in the database (base64-encoded nonce + ciphertext + tag).

    Usage in model declarations::

        email: Mapped[str] = mapped_column(EncryptedString)

    The field can be assigned plaintext and read back as plaintext —
    encryption and decryption happen automatically during flush/load.

    ``None`` values are passed through (stored as NULL).
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: str | None, dialect) -> str | None:
        """Encrypt ``value`` before writing to the database.

        Args:
            value: The plaintext string to encrypt, or ``None``.
            dialect: The database dialect (unused).

        Returns:
            Base64-encoded encrypted string, or ``None``.
        """
        if value is None:
            return None
        key = get_encryption_key()
        return aes_encrypt(value, key)

    def process_result_value(self, value: str | None, dialect) -> str | None:
        """Decrypt ``value`` after reading from the database.

        Args:
            value: The base64-encoded encrypted string, or ``None``.
            dialect: The database dialect (unused).

        Returns:
            Original plaintext string, or ``None``.
        """
        if value is None:
            return None
        key = get_encryption_key()
        return aes_decrypt(value, key)


class RolDocente(str, enum.Enum):
    """Roles available for teaching team assignments.

    These match the string values used in ``usuario_roles`` (C-03) so that
    the ``rol`` column in ``asignaciones`` can be compared directly with
    the existing role system.  New values can be added without schema
    changes since the DB stores raw strings.
    """

    PROFESOR = "PROFESOR"
    TUTOR = "TUTOR"
    COORDINADOR = "COORDINADOR"
    NEXO = "NEXO"
    ADMIN = "ADMIN"
    FINANZAS = "FINANZAS"
