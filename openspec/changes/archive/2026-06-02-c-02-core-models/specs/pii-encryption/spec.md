## ADDED Requirements

### Requirement: The system SHALL provide AES-256-GCM encryption and decryption for PII data at rest

The system MUST provide two core functions in `core/security.py`:

- `aes_encrypt(plaintext: str, key: bytes) -> str` — Encrypts a plaintext string using AES-256-GCM. Returns a URL-safe base64-encoded string that contains nonce + ciphertext + authentication tag.
- `aes_decrypt(ciphertext: str, key: bytes) -> str` — Decrypts a ciphertext string (produced by `aes_encrypt`) using the same key. Returns the original plaintext.

The key MUST be exactly 32 bytes (256 bits). The implementation MUST use the `cryptography` library's `AESGCM` class.

#### Scenario: Encrypt and decrypt roundtrip
- **WHEN** `aes_encrypt("sensitive-data", key)` is called with a valid 32-byte key
- **THEN** it returns a non-empty string, URL-safe base64-encoded
- **WHEN** `aes_decrypt(result, key)` is called with the same key
- **THEN** it returns `"sensitive-data"`

#### Scenario: Different ciphertext per encryption
- **WHEN** `aes_encrypt` is called twice with the same plaintext and key
- **THEN** the two output strings MUST be different (AES-GCM generates a random nonce each time)

#### Scenario: Decrypt with wrong key fails
- **WHEN** `aes_decrypt(ciphertext, wrong_key)` is called with a different key
- **THEN** it MUST raise an `AuthenticationError` (GCM authentication fails)

#### Scenario: Encrypt with invalid key length
- **WHEN** `aes_encrypt("data", b"short")` is called with a key that is not 32 bytes
- **THEN** it MUST raise a `ValueError`

### Requirement: The system SHALL provide an EncryptedString SQLAlchemy TypeDecorator

The system MUST provide an `EncryptedString` TypeDecorator in `models/types.py` that wraps `aes_encrypt` and `aes_decrypt`. This TypeDecorator automatically encrypts values when writing to the database and decrypts them when reading.

The TypeDecorator MUST use the `ENCRYPTION_KEY` from application settings (obtained via `get_settings().encryption_key`).

#### Scenario: EncryptedString transparent encrypt on write
- **WHEN** a model field declared as `EncryptedString` is assigned a plaintext value and flushed to the database
- **THEN** the stored column value SHALL be the encrypted base64-encoded string (not plaintext)

#### Scenario: EncryptedString transparent decrypt on read
- **WHEN** a model with an `EncryptedString` field is read from the database
- **THEN** the field attribute SHALL contain the original plaintext value

#### Scenario: EncryptedString with None value
- **WHEN** an `EncryptedString` field is assigned `None`
- **THEN** the stored column SHALL be `NULL`
- **THEN** reading it back SHALL return `None`
