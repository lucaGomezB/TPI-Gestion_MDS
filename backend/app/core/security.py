"""AES-256-GCM encryption, Argon2id password hashing, and JWT functions.

Core security primitives for the activia-trace authentication system.

AES-256-GCM storage format: ``URL-safe base64(nonce || ciphertext || tag)``
- Nonce: 12 bytes (random, generated per encryption)
- Tag: 16 bytes (authentication)
- Ciphertext: variable length (same as plaintext)

**Key management:**
- ``get_encryption_key()`` reads ``ENCRYPTION_KEY`` from settings (must be 32 bytes).
- The key MUST NOT be rotated once data exists — existing ciphertext becomes unreadable.
"""

import base64
import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError as Argon2VerificationError

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

# ── AES constants ────────────────────────────────────────────────────────────
_NONCE_LENGTH = 12
_KEY_LENGTH = 32

# ── Argon2id constants (OWASP recommended minimums) ─────────────────────────
_ph = PasswordHasher(
    memory_cost=19456,
    time_cost=2,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


# ── AES helpers (existing) ────────────────────────────────────────────────────


def _validate_key(key: bytes) -> None:
    """Ensure the key is exactly 32 bytes (256 bits) for AES-256."""
    if len(key) != _KEY_LENGTH:
        raise ValueError(
            f"Key must be exactly {_KEY_LENGTH} bytes (got {len(key)}). "
            f"AES-256 requires a 256-bit key."
        )


def get_encryption_key() -> bytes:
    """Return the 32-byte AES-256 encryption key from application settings.

    Reads ``ENCRYPTION_KEY`` from ``Settings`` (set via environment variable
    or ``.env`` file). The key is expected to be a UTF-8 string of exactly
    32 characters, which is encoded to bytes.

    Returns:
        A 32-byte ``bytes`` object suitable for ``aes_encrypt`` / ``aes_decrypt``.
    """
    key_str = get_settings().encryption_key
    return key_str.encode("utf-8")


def aes_encrypt(plaintext: str, key: bytes) -> str:
    """Encrypt ``plaintext`` using AES-256-GCM.

    Generates a new random 12-byte nonce per call (ensuring different
    ciphertext for the same plaintext). Returns a URL-safe base64 string
    of ``nonce + ciphertext + tag``.

    Args:
        plaintext: The string to encrypt (UTF-8 encoded internally).
        key: A 32-byte AES-256 key.

    Returns:
        URL-safe base64-encoded ``(nonce || ciphertext || tag)`` string.

    Raises:
        ValueError: If ``key`` is not 32 bytes.
    """
    _validate_key(key)
    nonce = os.urandom(_NONCE_LENGTH)
    aesgcm = AESGCM(key)
    ciphertext_bytes = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Prepend nonce to ciphertext (AESGCM.encrypt returns ciphertext + tag)
    payload = nonce + ciphertext_bytes
    return base64.urlsafe_b64encode(payload).decode("ascii")


def aes_decrypt(ciphertext: str, key: bytes) -> str:
    """Decrypt a ciphertext produced by ``aes_encrypt``.

    Decodes the URL-safe base64 string, extracts the nonce (first 12 bytes),
    and decrypts with AES-256-GCM.

    Args:
        ciphertext: The base64-encoded ``(nonce || ciphertext || tag)`` string.
        key: A 32-byte AES-256 key (must match the encryption key).

    Returns:
        The original plaintext string.

    Raises:
        ValueError: If ``key`` is not 32 bytes.
        cryptography.exceptions.InvalidTag: If the key is wrong or data is corrupted.
    """
    _validate_key(key)
    payload = base64.urlsafe_b64decode(ciphertext)
    nonce = payload[:_NONCE_LENGTH]
    ciphertext_bytes = payload[_NONCE_LENGTH:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext_bytes, None).decode("utf-8")


# ── Argon2id password hashing (D-01) ─────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Hash a password using Argon2id.

    Args:
        plain: The plaintext password to hash.

    Returns:
        The PHC-formatted hash string (``$argon2id$v=19$...``).
    """
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against an Argon2id hash.

    Args:
        plain: The plaintext password to verify.
        hashed: The PHC-formatted Argon2id hash string.

    Returns:
        ``True`` if the password matches, ``False`` otherwise.
    """
    try:
        return _ph.verify(hashed, plain)
    except (Argon2VerificationError, ValueError, TypeError):
        return False


# ── JWT functions (D-02) ─────────────────────────────────────────────────────


def create_access_token(
    sub: str,
    tenant_id: str,
    roles: list[str],
) -> str:
    """Create a signed JWT access token.

    The token is signed with HS256 using the application's ``SECRET_KEY``.
    It expires after ``ACCESS_TOKEN_EXPIRE_MINUTES`` (default 15 minutes).

    Payload claims:
    - ``sub``: User UUID
    - ``tenant_id``: Tenant UUID
    - ``roles``: List of role name strings
    - ``exp``: Expiration timestamp (UTC)
    - ``iat``: Issued-at timestamp (UTC)
    - ``jti``: Unique token ID (UUID)

    Args:
        sub: The user UUID.
        tenant_id: The tenant UUID.
        roles: List of role names (e.g. ``["ADMIN"]``).

    Returns:
        A signed JWT string.
    """
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": sub,
        "tenant_id": tenant_id,
        "roles": roles,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload as a dictionary.

    Raises:
        jwt.ExpiredSignatureError: If the token has expired.
        jwt.InvalidSignatureError: If the signature is invalid.
        jwt.PyJWTError: For any other JWT-related error.
    """
    settings = get_settings()
    return pyjwt.decode(
        token,
        settings.secret_key,
        algorithms=["HS256"],
    )


# ── Refresh token functions (D-03) ───────────────────────────────────────────


def create_refresh_token() -> tuple[str, str, str]:
    """Create a cryptographically random refresh token.

    Returns:
        A tuple of ``(raw_token, token_hash, token_family_uuid)``:
        - ``raw_token``: 64-character hex string (32 random bytes)
        - ``token_hash``: SHA-256 hex digest of the raw token (64 chars)
        - ``token_family_uuid``: UUID string grouping tokens of the same session
    """
    raw_token = os.urandom(32).hex()
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    token_family = str(uuid.uuid4())
    return raw_token, token_hash, token_family


# ── Temporary token for TOTP handshake (D-04) ────────────────────────────────


# ── Dict-level encryption for Moodle config (D-04) ───────────────────────────

_MOODLE_ENCRYPT_FIELDS = {"ws_url", "ws_token"}


def encrypt_moodle_config(config: dict) -> dict:
    """Encrypt sensitive fields in a Moodle configuration dict.

    Encrypts ``ws_url`` and ``ws_token`` using AES-256-GCM. Non-sensitive
    fields (``ws_enabled``, ``moodle_version``, etc.) are left as-is.

    Args:
        config: The Moodle configuration dictionary.

    Returns:
        A new dict with sensitive fields encrypted (base64 strings).
    """
    key = get_encryption_key()
    encrypted = {}
    for field, value in config.items():
        if field in _MOODLE_ENCRYPT_FIELDS and isinstance(value, str) and value:
            encrypted[field] = aes_encrypt(value, key)
        else:
            encrypted[field] = value
    return encrypted


def decrypt_moodle_config(config: dict) -> dict:
    """Decrypt sensitive fields in a Moodle configuration dict.

    Args:
        config: The Moodle configuration dictionary (with encrypted fields).

    Returns:
        A new dict with sensitive fields decrypted to plaintext.
    """
    key = get_encryption_key()
    decrypted = {}
    for field, value in config.items():
        if field in _MOODLE_ENCRYPT_FIELDS and isinstance(value, str) and value:
            try:
                decrypted[field] = aes_decrypt(value, key)
            except Exception:
                # If decryption fails, return the raw value
                decrypted[field] = value
        else:
            decrypted[field] = value
    return decrypted


# ── Temporary token for TOTP handshake (D-04) ────────────────────────────────


def create_temp_token(sub: str, purpose: str, expiry_minutes: int = 2) -> str:
    """Create a short-lived JWT for the TOTP verification handshake.

    Args:
        sub: The user UUID.
        purpose: The purpose claim (e.g. ``"totp_verification"``).
        expiry_minutes: Token lifetime in minutes (default 2).

    Returns:
        A signed JWT string with very short expiry.
    """
    settings = get_settings()
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": sub,
        "purpose": purpose,
        "exp": now + timedelta(minutes=expiry_minutes),
        "iat": now,
        "jti": str(uuid.uuid4()),
    }
    return pyjwt.encode(payload, settings.secret_key, algorithm="HS256")
