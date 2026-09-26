"""
Application-layer authenticated encryption for sensitive data at rest (e.g. TOTP secrets).

Uses AES-256-GCM authenticated encryption with cryptographically random 96-bit nonces.
Supports versioned ciphertext format (v1:...) and graceful fallback for legacy secrets.
"""

import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _get_encryption_key(key_str: str | None = None) -> bytes:
    """
    Derive a 256-bit (32-byte) AES key from the configured MFA_ENCRYPTION_KEY.
    """
    raw_key = key_str or settings.MFA_ENCRYPTION_KEY
    if not raw_key:
        if settings.ENVIRONMENT == "production":
            raise ValueError("MFA_ENCRYPTION_KEY must be set in production environment")
        # Default development key
        raw_key = "dev-insecure-mfa-encryption-key-32-bytes-long!"

    # If key is provided as a 64-character hex string
    if len(raw_key) == 64:
        try:
            return bytes.fromhex(raw_key)
        except ValueError:
            pass

    key_bytes = raw_key.encode("utf-8")
    if len(key_bytes) == 32:
        return key_bytes

    # Derive 32-byte key deterministically using SHA-256
    return hashlib.sha256(key_bytes).digest()


def encrypt_mfa_secret(secret: str, key_override: str | None = None) -> str:
    """
    Encrypt a Base32 TOTP secret using AES-256-GCM.

    Returns:
        Versioned ciphertext string: 'v1:<b64_nonce>:<b64_ciphertext_and_tag>'
    """
    if not secret:
        return secret

    key = _get_encryption_key(key_override)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    secret_bytes = secret.encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, secret_bytes, None)

    nonce_b64 = base64.b64encode(nonce).decode("ascii")
    ciphertext_b64 = base64.b64encode(ciphertext).decode("ascii")

    return f"v1:{nonce_b64}:{ciphertext_b64}"


def decrypt_mfa_secret(stored_value: str, key_override: str | None = None) -> str:
    """
    Decrypt a stored MFA secret.

    If the value is in versioned ciphertext format ('v1:...'), decrypts it using AES-256-GCM.
    If the value is not versioned (legacy unencrypted Base32 secret), returns it as-is for backward compatibility.

    Raises:
        ValueError: If ciphertext is malformed, tampered with, or cannot be decrypted.
    """
    if not stored_value:
        return stored_value

    # Check for version prefix
    if not stored_value.startswith("v1:"):
        # Legacy plaintext secret fallback
        return stored_value

    parts = stored_value.split(":")
    if len(parts) != 3:
        raise ValueError("Malformed MFA ciphertext envelope")

    _, nonce_b64, ciphertext_b64 = parts
    try:
        nonce = base64.b64decode(nonce_b64.encode("ascii"))
        ciphertext = base64.b64decode(ciphertext_b64.encode("ascii"))
    except Exception as exc:
        raise ValueError(f"Invalid base64 encoding in MFA ciphertext: {exc}") from exc

    key = _get_encryption_key(key_override)
    aesgcm = AESGCM(key)

    try:
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode("utf-8")
    except Exception as exc:
        raise ValueError("Failed to decrypt MFA secret: authentication tag mismatch or corrupted ciphertext") from exc
