"""Unit tests for email sender utility functions (C-11, Task 13.2).

Tests ``_mask_email`` from ``app.services.email_sender``.
"""

from app.services.email_sender import _mask_email


class TestMaskEmail:
    """_mask_email — email masking for API responses (D-13)."""

    def test_standard_email(self):
        """Standard email: j***@example.com."""
        result = _mask_email("juan@example.com")
        assert result == "j***@example.com"

    def test_short_local_part(self):
        """Single char local part: a***@test.com."""
        result = _mask_email("a@test.com")
        assert result == "a***@test.com"

    def test_long_local_part(self):
        """Long local part: m***@domain.com."""
        result = _mask_email("maria.lopez@domain.com")
        assert result == "m***@domain.com"

    def test_email_with_dots_in_domain(self):
        """Email with subdomain: j***@sub.domain.com."""
        result = _mask_email("juan@sub.domain.com")
        assert result == "j***@sub.domain.com"

    def test_no_at_sign(self):
        """String without @ should be returned unchanged."""
        result = _mask_email("notanemail")
        assert result == "notanemail"

    def test_empty_local_part(self):
        """Empty local part before @ should return original."""
        result = _mask_email("@domain.com")
        assert result == "@domain.com"

    def test_empty_string(self):
        """Empty string should return empty string."""
        result = _mask_email("")
        assert result == ""
