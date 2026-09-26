"""
Phase 16 Integration Tests — Audit Management & Forensics Security Verification.

Validates:
1. AUTHORIZATION: ADMIN access to audit logs, single log detail, and action metadata; STUDENT receives 403; unauthenticated receives 401.
2. FILTERING & SEARCH: Querying by action, status, resource_type, search keyword, and date range.
3. PAGINATION: Page boundaries, page size adjustments, and accurate total record counts.
4. SINGLE LOG INSPECTION & IDOR DEFENSE: Valid UUID lookup, 404 on nonexistent record, 403 for unauthorized users.
5. SENSITIVE DATA EXCLUSION: Verification that audit payloads strictly omit secrets, passwords, MFA keys, and token hashes.
6. READ-ONLY IMMUTABILITY: Guarantee that audit log entries cannot be modified or deleted via HTTP.
"""

from datetime import datetime, timedelta, timezone
import uuid
from fastapi.testclient import TestClient
import pytest

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.main import app
from app.models.audit_log import AuditAction, AuditLog, AuditStatus
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.permissions.service import permission_service


@pytest.fixture(autouse=True)
def ensure_rbac_seeded():
    """Ensure database has default roles and permissions initialized."""
    with SessionLocal() as db:
        permission_service.seed_default_roles_and_permissions(db)


@pytest.fixture
def audit_test_context():
    """Provisions Admin and Student users and sample audit records for testing."""
    with SessionLocal() as db:
        admin_role = db.query(Role).filter_by(name="ADMIN").first()
        student_role = db.query(Role).filter_by(name="STUDENT").first()

        admin_user = User(
            email=f"admin.audit.{uuid.uuid4().hex[:6]}@audit-test.example.com",
            full_name="Audit Administrator",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if admin_role:
            admin_user.roles.append(admin_role)

        student_user = User(
            email=f"student.audit.{uuid.uuid4().hex[:6]}@audit-test.example.com",
            full_name="Audit Student Member",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if student_role:
            student_user.roles.append(student_role)

        db.add_all([admin_user, student_user])
        db.flush()

        # Seed specific test audit records
        log1 = AuditLog(
            user_id=admin_user.id,
            action=AuditAction.LOGIN_SUCCESS,
            resource_type="User",
            resource_id=str(admin_user.id),
            status=AuditStatus.SUCCESS,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 PustakHub-TestClient",
        )
        log2 = AuditLog(
            user_id=admin_user.id,
            action=AuditAction.USER_DEACTIVATED,
            resource_type="User",
            resource_id=f"{student_user.id}:DEACTIVATED",
            status=AuditStatus.SUCCESS,
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0 PustakHub-TestClient",
        )
        log3 = AuditLog(
            user_id=None,
            action=AuditAction.LOGIN_FAILURE,
            resource_type="User",
            resource_id="unknown@threat-actor.example",
            status=AuditStatus.FAILURE,
            ip_address="203.0.113.42",
            user_agent="curl/8.1.0",
        )

        db.add_all([log1, log2, log3])
        db.commit()

        return {
            "admin_id": admin_user.id,
            "student_id": student_user.id,
            "log1_id": log1.id,
            "log2_id": log2.id,
            "log3_id": log3.id,
        }


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


class TestAuditAuthorization:
    """Tests authorization gates for audit management endpoints."""

    def test_admin_can_list_audit_logs(self, client, audit_test_context):
        res = client.get("/api/v1/audit/logs", headers=auth_headers(audit_test_context["admin_id"]))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 3

    def test_admin_can_get_audit_actions(self, client, audit_test_context):
        res = client.get("/api/v1/audit/actions", headers=auth_headers(audit_test_context["admin_id"]))
        assert res.status_code == 200
        data = res.json()
        assert "actions" in data
        assert "categories" in data
        assert len(data["actions"]) >= 10
        assert "Authentication" in data["categories"]

    def test_admin_can_get_single_audit_log(self, client, audit_test_context):
        log_id = audit_test_context["log1_id"]
        res = client.get(f"/api/v1/audit/logs/{log_id}", headers=auth_headers(audit_test_context["admin_id"]))
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == str(log_id)
        assert data["action"] == "LOGIN_SUCCESS"
        assert data["status"] == "SUCCESS"
        assert data["ip_address"] == "192.168.1.100"

    def test_student_cannot_access_audit_logs(self, client, audit_test_context):
        res = client.get("/api/v1/audit/logs", headers=auth_headers(audit_test_context["student_id"]))
        assert res.status_code == 403

    def test_student_cannot_get_single_audit_log(self, client, audit_test_context):
        log_id = audit_test_context["log1_id"]
        res = client.get(f"/api/v1/audit/logs/{log_id}", headers=auth_headers(audit_test_context["student_id"]))
        assert res.status_code == 403

    def test_unauthenticated_cannot_access_audit_logs(self, client):
        res = client.get("/api/v1/audit/logs")
        assert res.status_code == 401


class TestAuditFilteringAndSearch:
    """Tests multi-parameter filtering and search on audit logs."""

    def test_filter_by_action(self, client, audit_test_context):
        res = client.get(
            "/api/v1/audit/logs?action=LOGIN_FAILURE",
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert all(item["action"] == "LOGIN_FAILURE" for item in data["items"])

    def test_filter_by_status(self, client, audit_test_context):
        res = client.get(
            "/api/v1/audit/logs?status=FAILURE",
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert all(item["status"] == "FAILURE" for item in data["items"])

    def test_filter_by_resource_type(self, client, audit_test_context):
        res = client.get(
            "/api/v1/audit/logs?resource_type=User",
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2
        assert all(item["resource_type"] == "User" for item in data["items"])

    def test_search_by_ip_address(self, client, audit_test_context):
        res = client.get(
            "/api/v1/audit/logs?search=203.0.113.42",
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1
        assert any(item["ip_address"] == "203.0.113.42" for item in data["items"])

    def test_search_by_actor_email(self, client, audit_test_context):
        res = client.get(
            "/api/v1/audit/logs?search=admin.audit",
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 2

    def test_filter_by_time_range(self, client, audit_test_context):
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=1)).isoformat()
        end = (now + timedelta(hours=1)).isoformat()

        res = client.get(
            "/api/v1/audit/logs",
            params={"start_time": start, "end_time": end},
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 3


class TestAuditPaginationAndBoundaries:
    """Tests server-side pagination for audit trails."""

    def test_pagination_page_size(self, client, audit_test_context):
        res = client.get(
            "/api/v1/audit/logs?page=1&page_size=2",
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) <= 2

    def test_pagination_empty_high_page(self, client, audit_test_context):
        res = client.get(
            "/api/v1/audit/logs?page=9999&page_size=50",
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["items"] == []


class TestAuditDetailsAndIdor:
    """Tests single audit event inspection, 404 handling, and IDOR protection."""

    def test_get_nonexistent_audit_log_returns_404(self, client, audit_test_context):
        fake_uuid = uuid.uuid4()
        res = client.get(
            f"/api/v1/audit/logs/{fake_uuid}",
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_invalid_uuid_returns_422(self, client, audit_test_context):
        res = client.get(
            "/api/v1/audit/logs/invalid-uuid-string",
            headers=auth_headers(audit_test_context["admin_id"]),
        )
        assert res.status_code == 422


class TestSensitiveDataProtectionAndImmutability:
    """Verifies that audit endpoints never leak secrets and reject mutations."""

    def test_audit_logs_never_leak_sensitive_fields(self, client, audit_test_context):
        res = client.get("/api/v1/audit/logs", headers=auth_headers(audit_test_context["admin_id"]))
        assert res.status_code == 200
        for item in res.json()["items"]:
            assert "password" not in item
            assert "password_hash" not in item
            assert "mfa_secret" not in item
            assert "refresh_token" not in item
            assert "token" not in item
            assert "recovery_codes" not in item

    def test_audit_logs_endpoints_are_read_only(self, client, audit_test_context):
        headers = auth_headers(audit_test_context["admin_id"])
        # POST to /logs is not allowed
        assert client.post("/api/v1/audit/logs", json={}, headers=headers).status_code in (404, 405)
        # DELETE on /logs is not allowed
        assert client.delete("/api/v1/audit/logs", headers=headers).status_code in (404, 405)
        # PUT on /logs/{id} is not allowed
        log_id = audit_test_context["log1_id"]
        assert client.put(f"/api/v1/audit/logs/{log_id}", json={}, headers=headers).status_code in (404, 405)
        assert client.delete(f"/api/v1/audit/logs/{log_id}", headers=headers).status_code in (404, 405)
