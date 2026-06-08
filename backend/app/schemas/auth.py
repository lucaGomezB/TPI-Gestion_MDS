"""Pydantic schemas for authentication requests and responses.

All schemas use ``extra='forbid'`` to reject unexpected fields
(project convention for security-sensitive schemas).

Schemas:
- ``LoginRequest``: email + password for initial login
- ``LoginTotpRequest``: temp_token + totp_code for 2FA completion
- ``TokenResponse``: access_token + refresh_token after successful auth
- ``TwoFactorRequired``: returned when user has TOTP enabled (HTTP 202)
- ``RefreshRequest``: refresh_token for token rotation
- ``ForgotPasswordRequest``: email for password recovery
- ``ResetPasswordRequest``: token + new_password to complete reset
- ``UserMeResponse``: current user profile (no sensitive fields)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    """Email and password for initial authentication."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class LoginTotpRequest(BaseModel):
    """Temp token and TOTP code to complete 2FA flow."""

    model_config = ConfigDict(extra="forbid")

    temp_token: str = Field(..., min_length=1)
    totp_code: str = Field(..., min_length=6, max_length=6)


class TokenResponse(BaseModel):
    """JWT access token and opaque refresh token."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TwoFactorRequired(BaseModel):
    """Response when user has TOTP 2FA enabled."""

    model_config = ConfigDict(extra="forbid")

    requires_2fa: bool = True
    temp_token: str


class RefreshRequest(BaseModel):
    """Refresh token for rotation."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., min_length=1)


class ForgotPasswordRequest(BaseModel):
    """Email for password recovery."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(..., min_length=3, max_length=255)


class ResetPasswordRequest(BaseModel):
    """Token and new password to complete password reset."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class UserMeResponse(BaseModel):
    """Current user profile — safe for API exposure."""

    model_config = ConfigDict(extra="forbid")

    id: str
    nombre: str
    apellidos: str
    email: str
    roles: list[str]
    tenant_id: str
