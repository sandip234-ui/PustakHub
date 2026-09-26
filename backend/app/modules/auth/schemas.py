"""
Pydantic schemas for the authentication module.

Enforces strict input validation, normalization, and sanitized response representations.

SECURITY:
  - Extra fields on sensitive payloads are strictly forbidden.
  - Passwords and OTPs are never exposed in any response schema.
  - UserOut only contains non-sensitive account metadata and role names.
"""

import re
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Payload for initiating public student registration."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full legal name",
        examples=["Sandip Biswal"],
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address used as login identifier",
        examples=["sandip@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description=(
            "Password meeting security policy: minimum 8 characters, "
            "at least one uppercase letter, one lowercase letter, one digit, and one special character."
        ),
        examples=["SecurePass123!"],
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\[\]\\/~`]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


class RegisterResponse(BaseModel):
    """Response returned when registration is initiated and OTP is dispatched."""

    message: str
    email: str


class VerifyOtpRequest(BaseModel):
    """Payload for submitting the 6-digit registration verification OTP."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="Email address submitted during registration")
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit verification OTP",
        examples=["123456"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("otp")
    @classmethod
    def validate_otp_format(cls, v: str) -> str:
        cleaned = v.strip()
        if not re.match(r"^\d{6}$", cleaned):
            raise ValueError("OTP must be exactly 6 numeric digits.")
        return cleaned


class VerifyOtpResponse(BaseModel):
    """Response returned after successful OTP verification and User creation."""

    message: str
    email: str
    user_id: uuid.UUID


class LoginRequest(BaseModel):
    """Payload for user authentication."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserOut(BaseModel):
    """Safe user representation for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    account_status: str
    roles: list[str] = Field(default_factory=list)
    is_mfa_enabled: bool = False
    is_verified: bool = False
    created_at: datetime


class TokenResponse(BaseModel):
    """Access and refresh token response returned upon login or token refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds")
    user: UserOut


class LoginResponse(BaseModel):
    """Response returned upon login attempt. Supports MFA challenge when enabled."""

    mfa_required: bool = False
    mfa_token: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: Optional[str] = "bearer"
    expires_in: Optional[int] = None
    user: Optional[UserOut] = None


class RefreshTokenRequest(BaseModel):
    """Payload for refreshing an expired access token."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(..., description="Valid raw refresh token string")


class LogoutRequest(BaseModel):
    """Payload for logging out and revoking a session."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: Optional[str] = Field(
        default=None,
        description="Optional refresh token string to revoke specific session",
    )


class MessageResponse(BaseModel):
    """Generic message response schema."""

    message: str


# ===========================================================================
# Password Reset Schemas (Phase 7)
# ===========================================================================


class ForgotPasswordRequest(BaseModel):
    """Payload for requesting a password reset email."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="Account email address")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class ResetPasswordRequest(BaseModel):
    """Payload for setting a new password using a valid reset token."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., min_length=16, description="Single-use password reset token")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description=(
            "New password meeting security policy: minimum 8 characters, "
            "at least one uppercase letter, one lowercase letter, one digit, and one special character."
        ),
    )

    @field_validator("token")
    @classmethod
    def clean_token(cls, v: str) -> str:
        return v.strip()

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+\[\]\\/~`]", v):
            raise ValueError("Password must contain at least one special character.")
        return v


# ===========================================================================
# Multi-Factor Authentication (MFA) Schemas (Phase 7)
# ===========================================================================


class MfaEnrollResponse(BaseModel):
    """Response returned upon starting MFA enrollment."""

    secret: str = Field(description="Base32 TOTP secret key for manual entry")
    otpauth_uri: str = Field(description="otpauth:// URI for authenticator QR codes")
    recovery_codes: list[str] = Field(description="One-time recovery codes (plain, shown once)")


class MfaVerifyEnrollmentRequest(BaseModel):
    """Payload to confirm TOTP code and finalize MFA activation."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit TOTP code from authenticator app",
    )

    @field_validator("code")
    @classmethod
    def clean_code(cls, v: str) -> str:
        cleaned = v.strip()
        if not re.match(r"^\d{6}$", cleaned):
            raise ValueError("TOTP code must be exactly 6 digits.")
        return cleaned


class MfaVerifyRequest(BaseModel):
    """Payload to solve MFA challenge during login using TOTP code or recovery code."""

    model_config = ConfigDict(extra="forbid")

    mfa_token: str = Field(..., description="MFA challenge token issued during initial login")
    code: str = Field(..., min_length=4, max_length=64, description="6-digit TOTP code or backup recovery code")

    @field_validator("mfa_token")
    @classmethod
    def clean_token(cls, v: str) -> str:
        return v.strip()

    @field_validator("code")
    @classmethod
    def clean_code(cls, v: str) -> str:
        return v.strip()


class MfaDisableRequest(BaseModel):
    """Payload to disable MFA on account (requires password re-authentication)."""

    model_config = ConfigDict(extra="forbid")

    password: str = Field(..., min_length=1, description="Current account password for re-authentication")
    code: Optional[str] = Field(None, description="Optional 6-digit TOTP code for extra confirmation")


class MfaStatusResponse(BaseModel):
    """Non-sensitive MFA status representation."""

    enabled: bool = Field(description="True if TOTP MFA is currently enabled")
