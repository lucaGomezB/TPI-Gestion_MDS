"""Tests for core.security — Argon2id password hashing and JWT functions."""

import time

import jwt
import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_temp_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    """Argon2id hash + verify roundtrip (Tasks 4.1, 4.2)."""

    def test_hash_password_returns_string(self):
        """hash_password should return a string starting with $argon2id$."""
        hashed = hash_password("secure-password-123")
        assert isinstance(hashed, str)
        assert hashed.startswith("$argon2id$")

    def test_hash_verify_roundtrip_correct(self):
        """verify_password should return True for correct password."""
        hashed = hash_password("secure-password-123")
        assert verify_password("secure-password-123", hashed) is True

    def test_hash_verify_incorrect_password(self):
        """verify_password should return False for wrong password."""
        hashed = hash_password("secure-password-123")
        assert verify_password("wrong-password", hashed) is False

    def test_hash_verify_empty_password(self):
        """verify_password should return False for empty password against hash."""
        hashed = hash_password("secure-password-123")
        assert verify_password("", hashed) is False

    def test_different_hashes_each_time(self):
        """Each hash_password call should produce different output (random salt)."""
        h1 = hash_password("same-password")
        h2 = hash_password("same-password")
        assert h1 != h2

    def test_hash_invalid_string_returns_false(self):
        """verify_password with invalid hash string should return False."""
        assert verify_password("test", "not-a-valid-hash") is False


class TestAccessTokenJWT:
    """JWT create + decode roundtrip (Tasks 4.3, 4.4)."""

    def test_create_access_token_returns_string(self):
        """create_access_token should return a JWT string with 3 parts."""
        token = create_access_token(
            sub="user-uuid-123",
            tenant_id="tenant-uuid-456",
            roles=["ADMIN"],
        )
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_decode_valid_token(self):
        """decode_access_token should return the original payload claims."""
        sub = "user-uuid-123"
        tenant_id = "tenant-uuid-456"
        roles = ["ADMIN", "COORDINADOR"]
        token = create_access_token(sub=sub, tenant_id=tenant_id, roles=roles)
        payload = decode_access_token(token)
        assert payload["sub"] == sub
        assert payload["tenant_id"] == tenant_id
        assert payload["roles"] == roles

    def test_jwt_contains_required_claims(self):
        """JWT payload should contain sub, tenant_id, roles, exp, iat, jti."""
        token = create_access_token(
            sub="user-uuid", tenant_id="tenant-uuid", roles=["ADMIN"]
        )
        payload = decode_access_token(token)
        assert "sub" in payload
        assert "tenant_id" in payload
        assert "roles" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_jwt_does_not_contain_permissions(self):
        """JWT payload should NOT contain a 'permissions' or 'perms' claim."""
        token = create_access_token(
            sub="user-uuid", tenant_id="tenant-uuid", roles=["ADMIN"]
        )
        payload = decode_access_token(token)
        assert "permissions" not in payload
        assert "perms" not in payload

    def test_decode_expired_token_raises(self):
        """decode_access_token should raise jwt.ExpiredSignatureError for expired tokens."""
        sub = "user-uuid"
        tenant_id = "tenant-uuid"
        roles = ["ADMIN"]
        # Create a token that expires in -1 second (already expired)
        import uuid

        from app.core.config import get_settings

        settings = get_settings()
        payload = {
            "sub": sub,
            "tenant_id": tenant_id,
            "roles": roles,
            "exp": int(time.time()) - 1,
            "iat": int(time.time()) - 10,
            "jti": str(uuid.uuid4()),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_access_token(token)

    def test_decode_invalid_signature_raises(self):
        """decode_access_token should raise jwt.InvalidSignatureError for wrong key."""
        token = create_access_token(
            sub="user-uuid", tenant_id="tenant-uuid", roles=["ADMIN"]
        )
        # Tamper the token (simulate different signature)
        parts = token.split(".")
        tampered = parts[0] + "." + parts[1] + ".invalidsignature"
        with pytest.raises(jwt.InvalidSignatureError):
            decode_access_token(tampered)

    def test_decode_malformed_token_raises(self):
        """decode_access_token should raise for malformed tokens."""
        with pytest.raises(jwt.PyJWTError):
            decode_access_token("not-a-jwt-token")

    def test_jti_is_uuid(self):
        """The jti claim should be a valid UUID string."""
        import uuid as uuid_mod

        token = create_access_token(
            sub="user-uuid", tenant_id="tenant-uuid", roles=["ADMIN"]
        )
        payload = decode_access_token(token)
        # Verify it's a valid UUID (doesn't raise)
        uuid_mod.UUID(payload["jti"])


class TestRefreshToken:
    """Refresh token creation (Task 4.5)."""

    def test_create_refresh_token_returns_tuple(self):
        """create_refresh_token should return (raw_token, token_hash, family_uuid)."""
        raw_token, token_hash, family_uuid = create_refresh_token()
        assert isinstance(raw_token, str)
        assert isinstance(token_hash, str)
        assert isinstance(family_uuid, str)

    def test_raw_token_is_64_hex_chars(self):
        """Raw refresh token should be 64 hex characters (32 bytes)."""
        raw_token, _, _ = create_refresh_token()
        assert len(raw_token) == 64
        int(raw_token, 16)  # Should be valid hex

    def test_token_hash_is_sha256(self):
        """Token hash should be a SHA-256 hex digest (64 chars)."""
        import hashlib

        raw_token, token_hash, _ = create_refresh_token()
        assert len(token_hash) == 64
        int(token_hash, 16)  # Valid hex
        # Verify it's actually the SHA-256 of the raw token
        assert token_hash == hashlib.sha256(raw_token.encode()).hexdigest()

    def test_family_uuid_is_uuid(self):
        """token_family should be a valid UUID string."""
        import uuid as uuid_mod

        _, _, family_uuid = create_refresh_token()
        uuid_mod.UUID(family_uuid)  # Should not raise

    def test_multiple_calls_produce_different_tokens(self):
        """Each call should produce a different raw_token."""
        t1, _, _ = create_refresh_token()
        t2, _, _ = create_refresh_token()
        assert t1 != t2


class TestTempToken:
    """Temporary token for TOTP handshake (Task 4.6)."""

    def test_create_temp_token_returns_string(self):
        """create_temp_token should return a JWT string."""
        token = create_temp_token(
            sub="user-uuid", purpose="totp_verification", expiry_minutes=2
        )
        assert isinstance(token, str)
        assert token.count(".") == 2

    def test_temp_token_has_purpose_claim(self):
        """Temp token should contain a 'purpose' claim."""
        token = create_temp_token(
            sub="user-uuid", purpose="totp_verification", expiry_minutes=2
        )
        payload = decode_access_token(token)
        assert payload["purpose"] == "totp_verification"
        assert payload["sub"] == "user-uuid"

    def test_temp_token_expires_quickly(self):
        """Temp token should have a very short expiry (2 min)."""
        import uuid

        from app.core.config import get_settings

        settings = get_settings()
        token = create_temp_token(
            sub="user-uuid", purpose="totp_verification", expiry_minutes=2
        )
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        exp = payload["exp"]
        iat = payload["iat"]
        # Expiry should be approximately 120 seconds from iat
        assert (exp - iat) <= 150  # Allow small tolerance
