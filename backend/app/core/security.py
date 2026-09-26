"""
Security primitives for PustakHub.

Provides:
  - Argon2id password hashing and verification
  - Secure 6-digit OTP generation, hashing, and verification
  - JWT access and refresh token creation and verification
  - Cryptographic token hashing (SHA-256) for UserSession storage

SECURITY:
  - Argon2id is explicitly configured for password hashing.
  - Never log raw passwords, OTPs, or JWT secrets.
  - Token secrets are read exclusively from application configuration.
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Argon2id Password Hasher
# ---------------------------------------------------------------------------

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using Argon2id.

    Args:
        password: Raw password string.

    Returns:
        Argon2id encoded hash string.
    """
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """
    Verify a plaintext password against an Argon2id hash.

    Args:
        password: Raw password string to test.
        password_hash: Stored Argon2id hash.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    if not password_hash:
        return False
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception as exc:
        logger.warning("Password verification error: %s", type(exc).__name__)
        return False


# ---------------------------------------------------------------------------
# OTP Primitives (6-digit cryptographically secure)
# ---------------------------------------------------------------------------


def generate_otp(length: int = 6) -> str:
    """
    Generate a cryptographically secure numeric OTP string.

    Args:
        length: Number of digits (default 6).

    Returns:
        Zero-padded string of numbers, e.g. "482910".
    """
    # Generate an integer in [0, 10^length - 1]
    limit = 10**length
    number = secrets.randbelow(limit)
    return f"{number:0{length}d}"


def hash_otp(otp: str) -> str:
    """
    Produce a SHA-256 hex digest of an OTP string.

    Args:
        otp: 6-digit OTP string.

    Returns:
        64-character hex digest.
    """
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def verify_otp_hash(otp: str, stored_hash: str) -> bool:
    """
    Constant-time comparison between a provided OTP and a stored SHA-256 hash.

    Args:
        otp: Raw 6-digit OTP candidate.
        stored_hash: Expected SHA-256 hex digest.

    Returns:
        True if match, False otherwise.
    """
    computed = hash_otp(otp)
    return hmac.compare_digest(computed, stored_hash)


# ---------------------------------------------------------------------------
# Token Hashing (for UserSession refresh tokens)
# ---------------------------------------------------------------------------


def hash_token(token: str) -> str:
    """
    Compute the SHA-256 hex digest of a token string.

    Used to store refresh token digests in the `user_sessions` table.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# JWT Tokens (Access & Refresh)
# ---------------------------------------------------------------------------


def create_access_token(
    subject: str | uuid.UUID,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Generate a signed JWT access token.

    Args:
        subject: Unique identifier of the user (UUID as string).
        extra_claims: Optional dictionary of non-authorization claims.
        expires_delta: Optional custom lifetime (defaults to config).

    Returns:
        Encoded JWT access token string.
    """
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "access",
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str | uuid.UUID,
    expires_delta: timedelta | None = None,
) -> tuple[str, str, datetime]:
    """
    Generate a signed JWT refresh token and its SHA-256 hash.

    Args:
        subject: Unique identifier of the user (UUID as string).
        expires_delta: Optional custom lifetime (defaults to config).

    Returns:
        tuple of (raw_jwt_token, token_hash, expires_at_datetime)
    """
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    raw_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    token_hash = hash_token(raw_token)

    return raw_token, token_hash, expire


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token's signature and expiration.

    Args:
        token: Raw JWT string.

    Returns:
        Decoded payload dictionary.

    Raises:
        JWTError: If signature is invalid, expired, or malformed.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[settings.JWT_ALGORITHM],
    )
