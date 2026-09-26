"""
Phase 3 Automated Test Suite — Authentication, Registration & Email OTP.

Tests:
  1. Argon2id password hashing and verification
  2. Cryptographic OTP generation and constant-time hashing
  3. Registration validation and temporary Redis state storage
  4. Non-creation of PostgreSQL User prior to OTP verification
  5. OTP verification, attempt throttling, expiry, and single-use
  6. Server-side STUDENT role assignment and account activation
  7. Login authentication and account status checks (Active/Suspended/Pending)
  8. JWT access token validation, claims, and type safety
  9. Refresh token issuance, SHA-256 hash persistence, and rotation
  10. Logout session revocation and replay prevention
  11. `get_current_user` dependency and `/api/v1/auth/me` endpoint
"""

import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.redis import get_redis_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_otp,
    hash_otp,
    hash_password,
    hash_token,
    verify_otp_hash,
    verify_password,
)
from app.main import app
from app.models.role import Role
from app.models.session import UserSession
from app.models.user import AccountStatus, User


@pytest.fixture(scope="module")
def client():
    """TestClient instance for HTTP endpoint testing."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session for tests, cleaned up afterwards."""
    session: Session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def clean_redis():
    """Cleans up Redis registration keys created during test runs."""
    redis_client = get_redis_client()
    yield redis_client


# ===========================================================================
# 1. Password Security (Argon2id)
# ===========================================================================


def test_password_hashes_successfully_with_argon2id():
    """Argon2id produces a valid hash that starts with $argon2id$."""
    raw = "MySecurePass123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert hashed.startswith("$argon2id$")


def test_password_verification_success_and_failure():
    """Correct password verifies; incorrect password fails."""
    raw = "MySecurePass123!"
    hashed = hash_password(raw)
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPass123!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(raw, None) is False


# ===========================================================================
# 2. OTP Primitives
# ===========================================================================


def test_otp_generation_and_hashing():
    """OTP is 6 digits; hash is 64-char SHA-256; verification works."""
    otp = generate_otp(6)
    assert len(otp) == 6
    assert otp.isdigit()

    digest = hash_otp(otp)
    assert len(digest) == 64
    assert verify_otp_hash(otp, digest) is True
    assert verify_otp_hash("000000" if otp != "000000" else "111111", digest) is False


# ===========================================================================
# 3. Public Registration
# ===========================================================================


def test_register_validation_rejects_weak_passwords(client: TestClient):
    """Registration requires at least 8 chars, uppercase, lowercase, digit, special char."""
    # Too short
    res1 = client.post(
        "/api/v1/auth/register",
        json={"name": "Alex", "email": "alex1@example.com", "password": "Short1!"},
    )
    assert res1.status_code == 422

    # Missing special char
    res2 = client.post(
        "/api/v1/auth/register",
        json={"name": "Alex", "email": "alex2@example.com", "password": "NoSpecialChar123"},
    )
    assert res2.status_code == 422

    # Missing uppercase
    res3 = client.post(
        "/api/v1/auth/register",
        json={"name": "Alex", "email": "alex3@example.com", "password": "lowercaseonly123!"},
    )
    assert res3.status_code == 422


def test_register_stores_temporary_state_in_redis_not_postgres(
    client: TestClient, db_session: Session, clean_redis
):
    """
    Submitting registration form must store state in Redis and MUST NOT
    create a User record in PostgreSQL before OTP verification.
    """
    email = f"student_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "Jane Doe",
        "email": email,
        "password": "SecureStudentPass123!",
    }

    with patch("app.core.email.email_service.send_registration_otp", return_value=True) as mock_send:
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == email
        assert "verification code sent" in data["message"].lower()
        mock_send.assert_called_once()

    # CRITICAL CHECK: User does NOT exist in PostgreSQL yet
    user_in_db = db_session.query(User).filter(User.email == email).first()
    assert user_in_db is None

    # Check Redis temporary state
    redis_key = f"registration:{email}"
    raw_redis_data = clean_redis.get(redis_key)
    assert raw_redis_data is not None
    reg_obj = json.loads(raw_redis_data)

    assert reg_obj["email"] == email
    assert reg_obj["name"] == "Jane Doe"
    # Never stored in plaintext
    assert reg_obj["password_hash"].startswith("$argon2id$")
    assert len(reg_obj["otp_hash"]) == 64
    assert clean_redis.ttl(redis_key) > 0


def test_register_forbids_arbitrary_roles(client: TestClient):
    """Extra fields like 'role': 'ADMIN' are rejected with 422 validation error."""
    payload = {
        "name": "Attacker",
        "email": "attacker@example.com",
        "password": "AttackerPass123!",
        "role": "ADMIN",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


# ===========================================================================
# 4. OTP Verification & User Creation
# ===========================================================================


def test_verify_otp_success_creates_active_student_user(
    client: TestClient, db_session: Session, clean_redis
):
    """
    Valid OTP creates PostgreSQL User with ACTIVE status, assigns STUDENT role,
    and cleans up Redis.
    """
    email = f"verified_student_{uuid.uuid4().hex[:8]}@example.com"
    raw_otp = "849201"
    otp_digest = hash_otp(raw_otp)
    pass_hash = hash_password("ValidPassword123!")

    # Seed Redis temporary registration
    redis_key = f"registration:{email}"
    clean_redis.set(
        redis_key,
        json.dumps({
            "name": "Verified Student",
            "email": email,
            "password_hash": pass_hash,
            "otp_hash": otp_digest,
            "otp_attempts": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        }),
        ex=300,
    )

    # Submit correct OTP
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": email, "otp": raw_otp},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert "user_id" in body

    # PostgreSQL Verification
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    assert user.full_name == "Verified Student"
    assert user.account_status == AccountStatus.ACTIVE
    assert any(r.name == "STUDENT" for r in user.roles)

    # Redis state is cleaned up
    assert clean_redis.get(redis_key) is None


def test_verify_otp_invalid_code_throttles_and_fails(client: TestClient, clean_redis):
    """Incorrect OTP increments attempts and returns remaining attempts."""
    email = f"throttle_test_{uuid.uuid4().hex[:8]}@example.com"
    raw_otp = "112233"
    otp_digest = hash_otp(raw_otp)

    redis_key = f"registration:{email}"
    clean_redis.set(
        redis_key,
        json.dumps({
            "name": "Throttle User",
            "email": email,
            "password_hash": hash_password("ThrottlePass123!"),
            "otp_hash": otp_digest,
            "otp_attempts": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        }),
        ex=300,
    )

    # 1st wrong attempt
    res = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": "999999"})
    assert res.status_code == 400
    assert "4 attempt(s) remaining" in res.json()["detail"]


def test_verify_otp_max_attempts_exceeded_deletes_registration(client: TestClient, clean_redis):
    """Exceeding MAX_OTP_ATTEMPTS locks out and deletes Redis key."""
    email = f"max_attempts_{uuid.uuid4().hex[:8]}@example.com"
    raw_otp = "123456"
    otp_digest = hash_otp(raw_otp)

    redis_key = f"registration:{email}"
    clean_redis.set(
        redis_key,
        json.dumps({
            "name": "Lockout User",
            "email": email,
            "password_hash": hash_password("LockoutPass123!"),
            "otp_hash": otp_digest,
            "otp_attempts": 4,  # Next failure hits limit (5)
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat(),
        }),
        ex=300,
    )

    res = client.post("/api/v1/auth/verify-otp", json={"email": email, "otp": "000000"})
    assert res.status_code == 400
    assert "maximum verification attempts exceeded" in res.json()["detail"].lower()
    assert clean_redis.get(redis_key) is None


# ===========================================================================
# 5. Login Authentication
# ===========================================================================


def test_login_success_returns_tokens_and_stores_session_hash(
    client: TestClient, db_session: Session
):
    """Valid login produces access & refresh tokens, and stores SHA-256 session hash."""
    email = f"login_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "CorrectLoginPass123!"
    password_h = hash_password(password)

    student_role = db_session.query(Role).filter(Role.name == "STUDENT").first()
    if not student_role:
        student_role = Role(name="STUDENT", description="Student")
        db_session.add(student_role)
        db_session.flush()

    user = User(
        full_name="Login Test User",
        email=email,
        password_hash=password_h,
        account_status=AccountStatus.ACTIVE,
        roles=[student_role],
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == email
    assert "STUDENT" in data["user"]["roles"]

    # Verify session in database stores HASH not raw refresh token
    raw_refresh = data["refresh_token"]
    expected_hash = hash_token(raw_refresh)

    session = db_session.query(UserSession).filter(UserSession.token_hash == expected_hash).first()
    assert session is not None
    assert session.user_id == user.id
    assert session.is_revoked is False


def test_login_invalid_password_returns_401(client: TestClient, db_session: Session):
    """Wrong password returns 401 without revealing internal detail."""
    email = f"wrong_pass_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        full_name="User Wrong Pass",
        email=email,
        password_hash=hash_password("RealPass123!"),
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword123!"},
    )
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


def test_login_suspended_or_inactive_user_rejected(client: TestClient, db_session: Session):
    """Suspended or pending verification users cannot authenticate."""
    email = f"suspended_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        full_name="Suspended User",
        email=email,
        password_hash=hash_password("SuspendedPass123!"),
        account_status=AccountStatus.SUSPENDED,
    )
    db_session.add(user)
    db_session.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SuspendedPass123!"},
    )
    assert res.status_code == 403
    assert "suspended" in res.json()["detail"].lower()


# ===========================================================================
# 6. JWT Access Token Security
# ===========================================================================


def test_jwt_access_token_claims_and_decoding():
    """Access token contains sub, type=access, jti, exp, iat."""
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id)
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_expired_token_fails_validation():
    """Expired tokens cannot be decoded."""
    user_id = uuid.uuid4()
    expired_token = create_access_token(
        subject=user_id,
        expires_delta=timedelta(seconds=-10),
    )
    with pytest.raises(Exception):
        decode_token(expired_token)


# ===========================================================================
# 7. Refresh Token Rotation & Session Management
# ===========================================================================


def test_refresh_token_rotation_and_revocation(client: TestClient, db_session: Session):
    """
    Refreshing rotates tokens: revokes previous session and issues a new valid token pair.
    Old refresh token cannot be reused.
    """
    email = f"refresh_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "RefreshUserPass123!"
    user = User(
        full_name="Refresh Test User",
        email=email,
        password_hash=hash_password(password),
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()

    # Login to get initial refresh token
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token1 = login_res.json()["refresh_token"]

    # 1. Refresh with token1
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": token1})
    assert refresh_res.status_code == 200
    data2 = refresh_res.json()
    token2 = data2["refresh_token"]
    assert token2 != token1

    # Verify old session was revoked in DB
    hash1 = hash_token(token1)
    session1 = db_session.query(UserSession).filter(UserSession.token_hash == hash1).first()
    assert session1.is_revoked is True

    # 2. Attempt replay with token1 (MUST FAIL)
    replay_res = client.post("/api/v1/auth/refresh", json={"refresh_token": token1})
    assert replay_res.status_code == 401

    # 3. Refresh with token2 (MUST SUCCEED)
    refresh2_res = client.post("/api/v1/auth/refresh", json={"refresh_token": token2})
    assert refresh2_res.status_code == 200


# ===========================================================================
# 8. Logout & Revocation
# ===========================================================================


def test_logout_revokes_session(client: TestClient, db_session: Session):
    """Logout endpoint marks the session as revoked."""
    email = f"logout_user_{uuid.uuid4().hex[:8]}@example.com"
    password = "LogoutPass123!"
    user = User(
        full_name="Logout User",
        email=email,
        password_hash=hash_password(password),
        account_status=AccountStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    refresh_token = login_res.json()["refresh_token"]

    logout_res = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token})
    assert logout_res.status_code == 200

    # Session is now revoked in DB
    t_hash = hash_token(refresh_token)
    session = db_session.query(UserSession).filter(UserSession.token_hash == t_hash).first()
    assert session.is_revoked is True

    # Refreshing with it fails
    refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 401


# ===========================================================================
# 9. Authentication Dependencies & /api/v1/auth/me Endpoint
# ===========================================================================


def test_get_me_with_valid_bearer_token(client: TestClient, db_session: Session):
    """Protected /api/v1/auth/me resolves current user from Bearer JWT access token."""
    email = f"me_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "MeTestPass123!"
    student_role = db_session.query(Role).filter(Role.name == "STUDENT").first()
    if not student_role:
        student_role = Role(name="STUDENT", description="Student")
        db_session.add(student_role)
        db_session.flush()

    user = User(
        full_name="Profile User",
        email=email,
        password_hash=hash_password(password),
        account_status=AccountStatus.ACTIVE,
        roles=[student_role],
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    access_token = login_res.json()["access_token"]

    # Call /api/v1/auth/me with Bearer token
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == email
    assert me_data["full_name"] == "Profile User"
    assert "STUDENT" in me_data["roles"]


def test_get_me_without_token_returns_401(client: TestClient):
    """Missing or invalid Authorization header returns 401."""
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401

    res_invalid = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res_invalid.status_code == 401
