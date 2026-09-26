"""
Phase 9 Security Remediation & Hardening Test Suite.

Verifies:
  - SEC-001: AES-256-GCM TOTP Secret Encryption at rest (round-trip, nonces, tamper resistance, legacy fallback)
  - SEC-002: Request size streaming and chunked transfer protection (Content-Length and chunked streams)
  - SEC-003: CSP header verification (removal of external QR provider api.qrserver.com)
"""

import os
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.encryption import (
    _get_encryption_key,
    decrypt_mfa_secret,
    encrypt_mfa_secret,
)
from app.core.security import hash_password, hash_token
from app.models.user import AccountStatus, User


# ===========================================================================
# SEC-001: AES-256-GCM MFA Secret Encryption at Rest
# ===========================================================================


def test_encryption_roundtrip_basic() -> None:
    """Plaintext TOTP secret encrypts and decrypts accurately."""
    secret = "JBSWY3DPEHPK3PXP"
    ciphertext = encrypt_mfa_secret(secret)

    assert ciphertext.startswith("v1:")
    assert ciphertext != secret
    decrypted = decrypt_mfa_secret(ciphertext)
    assert decrypted == secret


def test_encryption_unique_nonces() -> None:
    """Encrypting the same plaintext twice produces distinct ciphertexts due to random 96-bit nonces."""
    secret = "JBSWY3DPEHPK3PXP"
    c1 = encrypt_mfa_secret(secret)
    c2 = encrypt_mfa_secret(secret)

    assert c1 != c2
    assert decrypt_mfa_secret(c1) == secret
    assert decrypt_mfa_secret(c2) == secret


def test_encryption_tamper_detection() -> None:
    """Tampering with ciphertext bytes triggers AES-GCM tag mismatch ValueError."""
    secret = "JBSWY3DPEHPK3PXP"
    ciphertext = encrypt_mfa_secret(secret)

    parts = ciphertext.split(":")
    # Alter the last character of the base64 ciphertext
    altered_b64 = parts[2][:-2] + ("AA" if parts[2][-2:] != "AA" else "BB")
    tampered = f"{parts[0]}:{parts[1]}:{altered_b64}"

    with pytest.raises(ValueError, match="Failed to decrypt MFA secret"):
        decrypt_mfa_secret(tampered)


def test_encryption_malformed_envelope_rejection() -> None:
    """Malformed ciphertext envelopes are rejected."""
    with pytest.raises(ValueError, match="Malformed MFA ciphertext envelope"):
        decrypt_mfa_secret("v1:onlyonepart")


def test_encryption_wrong_key_rejection() -> None:
    """Attempting decryption with a different key fails tag verification."""
    secret = "JBSWY3DPEHPK3PXP"
    key1 = "11111111111111111111111111111111"
    key2 = "22222222222222222222222222222222"

    ciphertext = encrypt_mfa_secret(secret, key_override=key1)
    with pytest.raises(ValueError, match="Failed to decrypt MFA secret"):
        decrypt_mfa_secret(ciphertext, key_override=key2)


def test_encryption_legacy_plaintext_fallback() -> None:
    """Legacy unencrypted Base32 secret without 'v1:' prefix is returned as-is for backward compatibility."""
    legacy_secret = "JBSWY3DPEHPK3PXP"
    decrypted = decrypt_mfa_secret(legacy_secret)
    assert decrypted == legacy_secret


def test_mfa_login_flow_with_encrypted_db_secret(client: TestClient) -> None:
    """MFA login flow successfully verifies TOTP when secret is stored encrypted in PostgreSQL."""
    import pyotp

    email = "mfa_enc_test@example.com"
    raw_password = "Password123!"
    secret = pyotp.random_base32()
    encrypted_secret = encrypt_mfa_secret(secret)
    recovery_code = "1111-2222"

    from app.models.role import Role

    with SessionLocal() as db:
        role = db.query(Role).filter(Role.name == "STUDENT").first()
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                full_name="MFA Encryption Test",
                password_hash=hash_password(raw_password),
                account_status=AccountStatus.ACTIVE,
                roles=[role] if role else [],
                is_mfa_enabled=True,
                mfa_secret=encrypted_secret,
                mfa_recovery_codes=[hash_token(recovery_code)],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.password_hash = hash_password(raw_password)
            user.account_status = AccountStatus.ACTIVE
            if role and role not in user.roles:
                user.roles.append(role)
            user.is_mfa_enabled = True
            user.mfa_secret = encrypted_secret
            user.mfa_recovery_codes = [hash_token(recovery_code)]
            db.commit()

    # 1. Step 1 Login -> triggers MFA challenge
    res1 = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": raw_password},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1.get("mfa_required") is True
    mfa_token = data1.get("mfa_token")
    assert mfa_token is not None

    # 2. Step 2 Login with valid TOTP generated from plaintext secret
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    res2 = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": valid_code},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert "access_token" in data2
    assert data2.get("token_type") == "bearer"


# ===========================================================================
# SEC-002: Request Size Streaming & Chunked Transfer Protection
# ===========================================================================


def test_request_size_under_limit(client: TestClient) -> None:
    """Normal request under payload size limit succeeds."""
    payload = {"email": "nonexistent@pustakhub.local", "password": "Password123!"}
    response = client.post("/api/v1/auth/login", json=payload)
    # Must not return 413
    assert response.status_code != 413


def test_request_size_oversized_content_length_rejected(client: TestClient) -> None:
    """Request with explicit Content-Length exceeding limit is rejected with 413."""
    headers = {"Content-Length": str(settings.MAX_REQUEST_BODY_SIZE + 1024)}
    response = client.post("/api/v1/auth/login", content=b"x", headers=headers)
    assert response.status_code == 413
    body = response.json()
    assert body["error"] == "payload_too_large"
    assert "exceeds the maximum permitted size" in body["message"]


def test_request_size_streaming_chunked_over_limit(client: TestClient) -> None:
    """Streaming request exceeding payload limit without Content-Length is rejected with 413."""
    chunk_size = 64 * 1024  # 64 KB
    total_chunks = (settings.MAX_REQUEST_BODY_SIZE // chunk_size) + 2

    def data_stream():
        for _ in range(total_chunks):
            yield b"a" * chunk_size

    # When streaming generator with client, Content-Length is omitted
    response = client.post("/api/v1/auth/login", content=data_stream())
    assert response.status_code == 413
    body = response.json()
    assert body["error"] == "payload_too_large"


# ===========================================================================
# SEC-003: Content Security Policy Hardening
# ===========================================================================


def test_csp_header_excludes_external_qr_provider(client: TestClient) -> None:
    """Content Security Policy img-src strictly excludes external api.qrserver.com."""
    response = client.get("/api/health")
    csp = response.headers.get("Content-Security-Policy", "")

    assert "https://api.qrserver.com" not in csp
    assert "img-src 'self' data:" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    assert "script-src 'self'" in csp
    assert "default-src 'self'" in csp
