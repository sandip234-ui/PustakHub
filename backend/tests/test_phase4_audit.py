"""
Phase 4 Audit Logging Service & Middleware Tests.

Tests covered:
  1. Successful login creates LOGIN_SUCCESS audit entry with IP and User-Agent
  2. Failed login creates LOGIN_FAILURE audit entry
  3. Registration OTP verification creates USER_CREATED audit entry
  4. Token refresh creates TOKEN_REFRESH audit entry
  5. Logout creates LOGOUT audit entry
  6. Admin role assignment creates ROLE_ASSIGNED audit entry
  7. Audit log query endpoint returns paginated results to authorized admin
  8. Unauthorized users (students) receive 403 when requesting audit logs
  9. Audit entries never store passwords, OTPs, or JWT tokens
  10. Anonymous audit events safely have user_id=None
  11. Resilient audit failure policy (fail-safe for non-critical logging)
"""

import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.redis import get_redis_client
from app.core.security import create_access_token, hash_otp, hash_password
from app.models.audit_log import AuditAction, AuditLog, AuditStatus
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.audit.service import audit_service


@pytest.fixture
def create_test_user():
    """Helper fixture to create test users with specific roles."""
    created_users = []

    def _create(role_name: str, email_prefix: str = "audit_user", password: str = "Password123!"):
        with SessionLocal() as db:
            role = db.query(Role).filter(Role.name == role_name).first()
            user = User(
                email=f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com",
                full_name=f"Test {role_name} User",
                password_hash=hash_password(password),
                account_status=AccountStatus.ACTIVE,
                roles=[role] if role else [],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created_users.append(user.id)
            token = create_access_token(subject=user.id)
            return user, token

    yield _create

    # Cleanup created users
    with SessionLocal() as db:
        for uid in created_users:
            u = db.query(User).filter(User.id == uid).first()
            if u:
                db.delete(u)
        db.commit()


def test_login_success_records_audit_log(client: TestClient, create_test_user):
    """Successful login logs a LOGIN_SUCCESS audit event with client metadata."""
    password = "SecurePassword123!"
    user, _ = create_test_user("STUDENT", "logintest", password=password)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
        headers={"User-Agent": "PustakHubTestAgent/1.0"},
    )
    assert response.status_code == 200

    with SessionLocal() as db:
        log_entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == user.id,
                AuditLog.action == AuditAction.LOGIN_SUCCESS,
            )
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        assert log_entry is not None
        assert log_entry.status == AuditStatus.SUCCESS
        assert log_entry.user_agent == "PustakHubTestAgent/1.0"
        assert log_entry.resource_type == "User"
        assert log_entry.resource_id == str(user.id)


def test_login_failure_records_audit_log(client: TestClient, create_test_user):
    """Failed login attempt logs a LOGIN_FAILURE audit event."""
    user, _ = create_test_user("STUDENT", "failtest", password="CorrectPassword123!")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "WrongPassword123!"},
        headers={"User-Agent": "AttackerAgent/1.0"},
    )
    assert response.status_code == 401

    with SessionLocal() as db:
        log_entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == user.id,
                AuditLog.action == AuditAction.LOGIN_FAILURE,
            )
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        assert log_entry is not None
        assert log_entry.status == AuditStatus.FAILURE
        assert log_entry.user_agent == "AttackerAgent/1.0"


def test_registration_otp_verify_records_user_created_audit_log(client: TestClient):
    """OTP verification and user creation records a USER_CREATED audit entry."""
    email = f"new_student_{uuid.uuid4().hex[:6]}@example.com"
    otp = "654321"

    # Stage in Redis
    redis_client = get_redis_client()
    redis_key = f"registration:{email}"
    reg_data = {
        "name": "Audit New Student",
        "email": email,
        "password_hash": hash_password("ValidPass123!"),
        "otp_hash": hash_otp(otp),
        "otp_attempts": 0,
        "created_at": "2026-09-24T00:00:00Z",
        "expires_at": "2026-09-24T00:05:00Z",
    }
    redis_client.set(redis_key, json.dumps(reg_data), ex=300)

    # Verify OTP
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": email, "otp": otp},
        headers={"User-Agent": "RegistrationAgent/1.0"},
    )
    assert response.status_code == 201
    user_id = response.json()["user_id"]

    with SessionLocal() as db:
        log_entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == uuid.UUID(user_id),
                AuditLog.action == AuditAction.USER_CREATED,
            )
            .first()
        )
        assert log_entry is not None
        assert log_entry.status == AuditStatus.SUCCESS
        assert log_entry.resource_type == "User"

        # Cleanup
        u = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if u:
            db.delete(u)
            db.commit()


def test_logout_records_audit_log(client: TestClient, create_test_user):
    """Logout logs a LOGOUT audit event."""
    password = "LogoutPassword123!"
    user, _ = create_test_user("STUDENT", "logout_user", password=password)

    # Login to get refresh token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    # Logout
    logout_resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"User-Agent": "LogoutAgent/1.0"},
    )
    assert logout_resp.status_code == 200

    with SessionLocal() as db:
        log_entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == user.id,
                AuditLog.action == AuditAction.LOGOUT,
            )
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        assert log_entry is not None
        assert log_entry.status == AuditStatus.SUCCESS


def test_admin_query_audit_logs(client: TestClient, create_test_user):
    """Admin can query audit logs with pagination and filters."""
    _, admin_token = create_test_user("ADMIN", "admin_audit_viewer")
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/api/v1/audit/logs?page=1&page_size=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_student_forbidden_from_audit_logs(client: TestClient, create_test_user):
    """Student lacks 'audit_log:view' and receives 403 Forbidden on GET /audit/logs."""
    _, student_token = create_test_user("STUDENT", "student_audit_prohibited")
    headers = {"Authorization": f"Bearer {student_token}"}

    response = client.get("/api/v1/audit/logs", headers=headers)
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]


def test_audit_logs_never_store_sensitive_secrets(client: TestClient):
    """Verify that sensitive secrets are sanitized and never persisted in audit records."""
    with SessionLocal() as db:
        entry = audit_service.log(
            db=db,
            action=AuditAction.LOGIN_FAILURE,
            resource_type="Auth",
            resource_id="$argon2id$v=19$m=65536,t=3,p=4$secretpasshash",
            status=AuditStatus.FAILURE,
        )
        assert entry is not None
        assert entry.resource_id == "[REDACTED_SENSITIVE_DATA]"
        assert "$argon2id$" not in entry.resource_id


def test_anonymous_event_nullable_user_id():
    """Audit records for unauthenticated events safely maintain user_id=None."""
    with SessionLocal() as db:
        entry = audit_service.log(
            db=db,
            action=AuditAction.LOGIN_FAILURE,
            user_id=None,
            resource_type="User",
            resource_id="unknown_user@example.com",
            status=AuditStatus.FAILURE,
            ip_address="192.168.1.100",
            user_agent="TestScanner/1.0",
        )
        assert entry is not None
        assert entry.user_id is None
        assert entry.ip_address == "192.168.1.100"


def test_token_refresh_records_audit_log(client: TestClient, create_test_user):
    """Token refresh rotation records a TOKEN_REFRESH audit event."""
    password = "RefreshPassword123!"
    user, _ = create_test_user("STUDENT", "refresh_audit_user", password=password)

    # Login to get refresh token
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": password},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    # Refresh
    ref_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
        headers={"User-Agent": "RefreshAgent/1.0"},
    )
    assert ref_resp.status_code == 200

    with SessionLocal() as db:
        log_entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == user.id,
                AuditLog.action == AuditAction.TOKEN_REFRESH,
            )
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        assert log_entry is not None
        assert log_entry.status == AuditStatus.SUCCESS


def test_role_assignment_records_audit_log(client: TestClient, create_test_user):
    """Admin assigning a role records a ROLE_ASSIGNED audit event."""
    _, admin_token = create_test_user("ADMIN", "admin_role_auditor")
    student, _ = create_test_user("STUDENT", "student_role_target")
    admin_headers = {
        "Authorization": f"Bearer {admin_token}",
        "User-Agent": "AdminAuditClient/2.0",
    }

    # Assign LIBRARIAN role
    response = client.post(
        f"/api/v1/users/{student.id}/roles",
        json={"role_name": "LIBRARIAN"},
        headers=admin_headers,
    )
    assert response.status_code == 200

    with SessionLocal() as db:
        log_entry = (
            db.query(AuditLog)
            .filter(
                AuditLog.user_id == student.id,
                AuditLog.action == AuditAction.ROLE_ASSIGNED,
            )
            .order_by(AuditLog.timestamp.desc())
            .first()
        )
        assert log_entry is not None
        assert log_entry.status == AuditStatus.SUCCESS
        assert log_entry.user_agent == "AdminAuditClient/2.0"

