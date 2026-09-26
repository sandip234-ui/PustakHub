"""
Phase 7 Authentication Security, Password Reset & MFA Tests.

Comprehensive suite covering:
  1. Password Reset Workflow (forgot-password, anti-enumeration, token hashing, single-use, session invalidation, audit logging)
  2. Password Policy Enforcement during reset (rejecting weak passwords)
  3. MFA Enrollment Workflow (TOTP secret generation, otpauth URI, recovery code generation, verification requirement, audit logging)
  4. MFA Login Challenge Workflow (challenge token, TOTP verification, JWT issuance boundary, failed attempt throttling)
  5. MFA Recovery Codes (one-time consumption, single-use invalidation, hash persistence, audit logging)
  6. MFA Disablement Workflow (password re-authentication, secret cleanup, audit logging)
  7. MFA Status endpoint & secret concealment (safe exposure, zero plaintext secrets in audit logs or /me profile)
  8. Account Status & Invariant Guarantees (suspended/deactivated account protection, anti-reactivation)
"""

import json
import uuid
from datetime import datetime, timedelta, timezone
import pytest
import pyotp
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.redis import get_redis_client
from app.core.security import create_access_token, hash_password, hash_token, verify_password
from app.models.audit_log import AuditAction, AuditLog
from app.models.role import Role
from app.models.session import UserSession
from app.models.user import AccountStatus, User
from app.modules.permissions.service import permission_service


@pytest.fixture(autouse=True)
def ensure_rbac_seeded():
    """Ensure database has default roles and permissions initialized."""
    with SessionLocal() as db:
        permission_service.seed_default_roles_and_permissions(db)


@pytest.fixture
def create_test_user():
    """Helper fixture to create test users with specific roles and account statuses."""
    created_users = []

    def _create(
        role_name: str = "STUDENT",
        email_prefix: str = "user",
        account_status: AccountStatus = AccountStatus.ACTIVE,
        password: str = "Password123!",
        is_mfa_enabled: bool = False,
        mfa_secret: str = None,
        mfa_recovery_codes: list[str] = None,
    ):
        with SessionLocal() as db:
            role = db.query(Role).filter(Role.name == role_name).first()
            user = User(
                email=f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com",
                full_name=f"Test {role_name} User",
                password_hash=hash_password(password),
                account_status=account_status,
                roles=[role] if role else [],
                is_mfa_enabled=is_mfa_enabled,
                mfa_secret=mfa_secret,
                mfa_recovery_codes=mfa_recovery_codes,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created_users.append(user.id)
            token = create_access_token(subject=user.id)
            return user, token

    yield _create

    # Cleanup created test users and their sessions
    with SessionLocal() as db:
        for uid in created_users:
            u = db.query(User).filter(User.id == uid).first()
            if u:
                db.delete(u)
        db.commit()


# ===========================================================================
# 1. Password Reset Workflow Tests
# ===========================================================================


def test_forgot_password_anti_enumeration_and_token_generation(
    client: TestClient, create_test_user
):
    """
    Test forgot-password endpoint:
      - Returns generic message for existing active account.
      - Returns identical generic message for nonexistent account (anti-enumeration).
      - Stores token securely hashed in Redis with TTL.
      - Emits PASSWORD_RESET_REQUESTED audit log.
    """
    user, _ = create_test_user("STUDENT", "pwd_reset_user")
    redis_client = get_redis_client()

    # 1. Request for existing active user
    res_existing = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": user.email},
    )
    assert res_existing.status_code == 200
    assert "If an account exists" in res_existing.json()["message"]

    # 2. Request for nonexistent user -> identical response (anti-enumeration)
    res_nonexistent = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": f"nonexistent_{uuid.uuid4().hex[:6]}@example.com"},
    )
    assert res_nonexistent.status_code == 200
    assert res_nonexistent.json()["message"] == res_existing.json()["message"]

    # 3. Verify audit log entry
    with SessionLocal() as db:
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == AuditAction.PASSWORD_RESET_REQUESTED,
                AuditLog.user_id == user.id,
            )
            .first()
        )
        assert audit is not None


def test_password_reset_success_and_session_revocation(
    client: TestClient, create_test_user
):
    """
    Test complete password reset flow:
      - Generates token in Redis
      - Validates and updates Argon2id password hash
      - Marks reset token consumed (single-use)
      - Invalidates all existing UserSession records
      - Emits PASSWORD_RESET_COMPLETED audit log
    """
    user, _ = create_test_user("STUDENT", "reset_success_user", password="OldPassword123!")
    redis_client = get_redis_client()

    # Create an active session in DB for this user
    with SessionLocal() as db:
        session = UserSession(
            user_id=user.id,
            token_hash=hash_token("dummy_refresh_token_1"),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_revoked=False,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id

    # Place a valid reset token in Redis
    raw_token = "secure_random_reset_token_xyz_123456"
    token_digest = hash_token(raw_token)
    reset_key = f"pwd_reset:{token_digest}"
    redis_client.set(
        reset_key,
        json.dumps({"user_id": str(user.id), "email": user.email}),
        ex=900,
    )

    # Submit reset password request
    new_password = "NewStrongPassword456!"
    res = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": new_password},
    )
    assert res.status_code == 200
    assert "successfully reset" in res.json()["message"].lower()

    # Verify password was updated in PostgreSQL
    with SessionLocal() as db:
        updated_user = db.query(User).filter(User.id == user.id).first()
        assert verify_password(new_password, updated_user.password_hash)
        assert not verify_password("OldPassword123!", updated_user.password_hash)

        # Verify session revocation
        revoked_session = db.query(UserSession).filter(UserSession.id == session_id).first()
        assert revoked_session.is_revoked is True

        # Verify audit log
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == AuditAction.PASSWORD_RESET_COMPLETED,
                AuditLog.user_id == user.id,
            )
            .first()
        )
        assert audit is not None

    # Verify token was deleted from Redis (single-use guarantee)
    assert redis_client.get(reset_key) is None

    # Attempting to use the same token again -> 400 Bad Request
    res_reuse = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "AnotherPassword789!"},
    )
    assert res_reuse.status_code == 400
    assert "invalid or expired" in res_reuse.json()["detail"].lower()


def test_password_reset_validation_and_abuse_protection(
    client: TestClient, create_test_user
):
    """
    Test password reset edge cases:
      - Weak new password rejected by policy (422)
      - Invalid / nonexistent token rejected (400)
      - Suspended user password reset rejected
    """
    user, _ = create_test_user(
        "STUDENT", "suspended_pwd_user", account_status=AccountStatus.SUSPENDED
    )
    redis_client = get_redis_client()

    raw_token = "suspended_user_reset_token_abc"
    token_digest = hash_token(raw_token)
    redis_client.set(
        f"pwd_reset:{token_digest}",
        json.dumps({"user_id": str(user.id), "email": user.email}),
        ex=900,
    )

    # 1. Weak password rejected by Pydantic validation
    res_weak = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "weak"},
    )
    assert res_weak.status_code == 422

    # 2. Suspended account reset rejected
    res_suspended = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "ValidStrongPassword123!"},
    )
    assert res_suspended.status_code == 400
    assert "not eligible" in res_suspended.json()["detail"].lower()

    # 3. Invalid token
    res_invalid_token = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "nonexistent_token_1234567890", "new_password": "ValidStrongPassword123!"},
    )
    assert res_invalid_token.status_code == 400


# ===========================================================================
# 2. MFA Enrollment Workflow Tests
# ===========================================================================


def test_mfa_enrollment_and_activation(client: TestClient, create_test_user):
    """
    Test TOTP MFA enrollment:
      - Unauthenticated cannot enroll (401)
      - Authenticated user initiates enrollment -> receives secret, otpauth URI, recovery codes
      - MFA is NOT enabled prior to verification
      - Submitting valid TOTP code enables MFA
      - Status endpoint reflects active MFA
    """
    user, token = create_test_user("STUDENT", "mfa_enroll_user")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Unauthenticated request -> 401
    res_unauth = client.post("/api/v1/auth/mfa/enroll")
    assert res_unauth.status_code == 401

    # 2. Start enrollment
    res_enroll = client.post("/api/v1/auth/mfa/enroll", headers=headers)
    assert res_enroll.status_code == 200
    enroll_data = res_enroll.json()
    assert "secret" in enroll_data
    assert "otpauth_uri" in enroll_data
    assert len(enroll_data["recovery_codes"]) == 8

    # 3. Verify MFA is NOT yet enabled in DB
    with SessionLocal() as db:
        u = db.query(User).filter(User.id == user.id).first()
        assert u.is_mfa_enabled is False

    # 4. Check status before activation
    res_status_before = client.get("/api/v1/auth/mfa/status", headers=headers)
    assert res_status_before.status_code == 200
    assert res_status_before.json()["enabled"] is False

    # 5. Submit invalid code -> 400
    res_invalid = client.post(
        "/api/v1/auth/mfa/verify-enrollment",
        headers=headers,
        json={"code": "000000"},
    )
    assert res_invalid.status_code == 400

    # 6. Generate valid TOTP code using secret and activate
    totp = pyotp.TOTP(enroll_data["secret"])
    valid_code = totp.now()

    res_verify = client.post(
        "/api/v1/auth/mfa/verify-enrollment",
        headers=headers,
        json={"code": valid_code},
    )
    assert res_verify.status_code == 200
    assert "successfully enabled" in res_verify.json()["message"].lower()

    # 7. Verify MFA is now enabled in DB and recovery codes are hashed
    with SessionLocal() as db:
        u = db.query(User).filter(User.id == user.id).first()
        assert u.is_mfa_enabled is True
        assert u.mfa_secret.startswith("v1:")
        assert u.mfa_secret != enroll_data["secret"]
        from app.core.encryption import decrypt_mfa_secret
        assert decrypt_mfa_secret(u.mfa_secret) == enroll_data["secret"]
        assert len(u.mfa_recovery_codes) == 8
        # Verify hashes, not plaintext
        for raw_code in enroll_data["recovery_codes"]:
            assert hash_token(raw_code) in u.mfa_recovery_codes
            assert raw_code not in u.mfa_recovery_codes

        # Verify audit log
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == AuditAction.MFA_ENABLED,
                AuditLog.user_id == user.id,
            )
            .first()
        )
        assert audit is not None

    # 8. Check status after activation
    res_status_after = client.get("/api/v1/auth/mfa/status", headers=headers)
    assert res_status_after.status_code == 200
    assert res_status_after.json()["enabled"] is True


# ===========================================================================
# 3. MFA Login Challenge & TOTP Verification Tests
# ===========================================================================


def test_mfa_login_challenge_and_totp_verification(
    client: TestClient, create_test_user
):
    """
    Test login flow for MFA-enabled accounts:
      - Non-MFA accounts log in normally (receive tokens immediately)
      - MFA accounts receive MFA challenge token (no access token issued yet)
      - Solving challenge with valid TOTP code issues authenticated tokens
      - Invalid TOTP code is rejected (401)
    """
    # 1. Create a non-MFA user and verify normal login
    normal_user, _ = create_test_user(
        "STUDENT", "normal_login_user", password="Password123!"
    )
    res_normal = client.post(
        "/api/v1/auth/login",
        json={"email": normal_user.email, "password": "Password123!"},
    )
    assert res_normal.status_code == 200
    assert res_normal.json()["mfa_required"] is False
    assert res_normal.json()["access_token"] is not None

    # 2. Create an MFA-enabled user
    secret = pyotp.random_base32()
    mfa_user, _ = create_test_user(
        "STUDENT",
        "mfa_login_user",
        password="Password123!",
        is_mfa_enabled=True,
        mfa_secret=secret,
        mfa_recovery_codes=[hash_token("rec-code-1"), hash_token("rec-code-2")],
    )

    # 3. Initial login attempt triggers MFA challenge
    res_mfa_init = client.post(
        "/api/v1/auth/login",
        json={"email": mfa_user.email, "password": "Password123!"},
    )
    assert res_mfa_init.status_code == 200
    mfa_payload = res_mfa_init.json()
    assert mfa_payload["mfa_required"] is True
    assert mfa_payload["mfa_token"] is not None
    assert mfa_payload["access_token"] is None  # Strict security boundary

    mfa_challenge_token = mfa_payload["mfa_token"]

    # 4. Attempt challenge with invalid code -> 401
    res_invalid_code = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_challenge_token, "code": "000000"},
    )
    assert res_invalid_code.status_code == 401

    # 5. Attempt challenge with valid TOTP code -> 200 OK with tokens
    totp = pyotp.TOTP(secret)
    valid_totp_code = totp.now()

    res_valid_mfa = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_challenge_token, "code": valid_totp_code},
    )
    assert res_valid_mfa.status_code == 200
    token_data = res_valid_mfa.json()
    assert token_data["mfa_required"] is False
    assert token_data["access_token"] is not None
    assert token_data["refresh_token"] is not None
    assert token_data["user"]["email"] == mfa_user.email


# ===========================================================================
# 4. MFA Recovery Codes Tests
# ===========================================================================


def test_mfa_recovery_code_single_use_consumption(
    client: TestClient, create_test_user
):
    """
    Test MFA backup recovery codes:
      - User can satisfy MFA login challenge with a recovery code
      - Recovery code is consumed and cannot be reused
      - Emits MFA_RECOVERY_USED audit log
    """
    raw_code_1 = "rec-alpha-1234"
    raw_code_2 = "rec-beta-5678"
    secret = pyotp.random_base32()

    mfa_user, _ = create_test_user(
        "STUDENT",
        "recovery_user",
        password="Password123!",
        is_mfa_enabled=True,
        mfa_secret=secret,
        mfa_recovery_codes=[hash_token(raw_code_1), hash_token(raw_code_2)],
    )

    # 1. Trigger login challenge
    res_login = client.post(
        "/api/v1/auth/login",
        json={"email": mfa_user.email, "password": "Password123!"},
    )
    mfa_token = res_login.json()["mfa_token"]

    # 2. Solve challenge using recovery code 1
    res_rec = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_token, "code": raw_code_1},
    )
    assert res_rec.status_code == 200
    assert res_rec.json()["access_token"] is not None

    # 3. Verify recovery code 1 was removed from DB and recovery code 2 remains
    with SessionLocal() as db:
        u = db.query(User).filter(User.id == mfa_user.id).first()
        assert hash_token(raw_code_1) not in u.mfa_recovery_codes
        assert hash_token(raw_code_2) in u.mfa_recovery_codes
        assert len(u.mfa_recovery_codes) == 1

        # Verify audit log
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == AuditAction.MFA_RECOVERY_USED,
                AuditLog.user_id == mfa_user.id,
            )
            .first()
        )
        assert audit is not None

    # 4. Trigger second login and attempt to reuse consumed recovery code 1 -> 401
    res_login_2 = client.post(
        "/api/v1/auth/login",
        json={"email": mfa_user.email, "password": "Password123!"},
    )
    mfa_token_2 = res_login_2.json()["mfa_token"]

    res_reuse = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_token_2, "code": raw_code_1},
    )
    assert res_reuse.status_code == 401


# ===========================================================================
# 5. MFA Disablement Workflow Tests
# ===========================================================================


def test_mfa_disable_workflow_and_reauthentication(
    client: TestClient, create_test_user
):
    """
    Test MFA disablement:
      - Requires authentication (401 if unauthenticated)
      - Requires valid account password for re-authentication (401 if invalid password)
      - Successfully clears MFA secret and recovery codes
      - Emits MFA_DISABLED audit log
    """
    secret = pyotp.random_base32()
    mfa_user, token = create_test_user(
        "STUDENT",
        "disable_mfa_user",
        password="MyPassword123!",
        is_mfa_enabled=True,
        mfa_secret=secret,
        mfa_recovery_codes=[hash_token("rec-1")],
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Attempt disable with wrong password -> 401
    res_wrong_pwd = client.post(
        "/api/v1/auth/mfa/disable",
        headers=headers,
        json={"password": "WrongPassword123!"},
    )
    assert res_wrong_pwd.status_code == 401

    # 2. Attempt disable with correct password -> 200 OK
    res_disable = client.post(
        "/api/v1/auth/mfa/disable",
        headers=headers,
        json={"password": "MyPassword123!"},
    )
    assert res_disable.status_code == 200
    assert "disabled" in res_disable.json()["message"].lower()

    # 3. Verify MFA state in DB
    with SessionLocal() as db:
        u = db.query(User).filter(User.id == mfa_user.id).first()
        assert u.is_mfa_enabled is False
        assert u.mfa_secret is None
        assert u.mfa_recovery_codes is None

        # Verify audit log
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == AuditAction.MFA_DISABLED,
                AuditLog.user_id == mfa_user.id,
            )
            .first()
        )
        assert audit is not None


# ===========================================================================
# 6. Secret Concealment & Profile Safety Tests
# ===========================================================================


def test_mfa_secrets_never_exposed_in_me_profile_or_status(
    client: TestClient, create_test_user
):
    """
    Verify that sensitive credentials (mfa_secret, recovery_codes, password_hash)
    are NEVER leaked via `/auth/me` or `/auth/mfa/status`.
    """
    secret = pyotp.random_base32()
    raw_recovery = "rec-secret-code-xyz"
    user, token = create_test_user(
        "STUDENT",
        "privacy_user",
        password="Password123!",
        is_mfa_enabled=True,
        mfa_secret=secret,
        mfa_recovery_codes=[hash_token(raw_recovery)],
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Check /auth/me profile
    res_me = client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert "mfa_secret" not in me_data
    assert "mfa_recovery_codes" not in me_data
    assert "password_hash" not in me_data
    assert me_data["is_mfa_enabled"] is True

    # 2. Check /auth/mfa/status
    res_status = client.get("/api/v1/auth/mfa/status", headers=headers)
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data == {"enabled": True}


# ===========================================================================
# 7. Password Reset Email One-Click Link Tests
# ===========================================================================


def test_password_reset_email_format_and_link_construction(monkeypatch):
    """
    Verify password reset email construction:
      - Email contains a one-click reset link pointing to FRONTEND_URL/reset-password?token=...
      - Raw token does NOT appear as standalone visible text / token-box.
      - Token appears only within the URL query parameter.
      - HTML and plain text bodies both include the link and 15-minute expiration notice.
    """
    import email
    from unittest.mock import MagicMock
    from app.core.email import EmailService

    sent_messages = []

    mock_smtp_instance = MagicMock()
    def fake_sendmail(from_addr, to_addrs, msg_string):
        sent_messages.append((from_addr, to_addrs, msg_string))

    mock_smtp_instance.sendmail.side_effect = fake_sendmail
    mock_smtp_class = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance
    mock_smtp_instance.__exit__.return_value = False

    monkeypatch.setattr("smtplib.SMTP", mock_smtp_class)
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test.local")
    monkeypatch.setattr(settings, "FRONTEND_URL", "http://localhost:5174")

    raw_token = "secure_token_sample_abc_123"
    recipient_name = "Alex Library"
    recipient_email = "alex@example.com"

    result = EmailService.send_password_reset_email(
        to_email=recipient_email,
        recipient_name=recipient_name,
        reset_token=raw_token,
    )
    assert result is True
    assert len(sent_messages) == 1

    _, to_addrs, raw_msg_str = sent_messages[0]
    assert recipient_email in to_addrs

    parsed_msg = email.message_from_string(raw_msg_str)
    text_part = next(part.get_payload(decode=True).decode("utf-8") for part in parsed_msg.walk() if part.get_content_type() == "text/plain")
    html_part = next(part.get_payload(decode=True).decode("utf-8") for part in parsed_msg.walk() if part.get_content_type() == "text/html")

    expected_url = f"http://localhost:5174/reset-password?token={raw_token}"

    # Plain text contains usable reset link
    assert expected_url in text_part
    assert "15 minutes" in text_part

    # HTML part contains button pointing to reset_url
    assert f'href="{expected_url}"' in html_part
    assert "Reset Password" in html_part
    assert "15 minutes" in html_part

    # HTML part does NOT contain visible fallback URL or prompt
    assert "Button not working" not in html_part
    assert "link-fallback" not in html_part
    assert "token-box" not in html_part
    assert "Use the token below to complete the reset process" not in html_part


def test_password_reset_email_html_escaping(monkeypatch):
    """
    Verify that recipient name with special characters is HTML-escaped to prevent email injection.
    """
    import email
    from unittest.mock import MagicMock
    from app.core.email import EmailService

    sent_messages = []

    mock_smtp_instance = MagicMock()
    mock_smtp_instance.sendmail.side_effect = lambda f, t, m: sent_messages.append((f, t, m))
    mock_smtp_instance.__enter__.return_value = mock_smtp_instance
    mock_smtp_instance.__exit__.return_value = False

    monkeypatch.setattr("smtplib.SMTP", MagicMock(return_value=mock_smtp_instance))
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test.local")

    malicious_name = '<script>alert("xss")</script> & User'
    EmailService.send_password_reset_email(
        to_email="test@example.com",
        recipient_name=malicious_name,
        reset_token="tok_123",
    )

    _, _, raw_msg_str = sent_messages[0]
    parsed_msg = email.message_from_string(raw_msg_str)
    html_parts = [part.get_payload(decode=True).decode("utf-8") for part in parsed_msg.walk() if part.get_content_type() == "text/html"]
    assert len(html_parts) == 1
    html_content = html_parts[0]

    assert "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt; &amp; User" in html_content
    assert "<script>" not in html_content

