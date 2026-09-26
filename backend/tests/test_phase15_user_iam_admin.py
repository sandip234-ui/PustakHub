"""
Phase 15 Integration Tests — User & IAM Administration Backend Security & Workflow Verification.

Validates:
1. ADMIN access to user listing with search, account_status, and role query filters.
2. User details and dynamic effective permissions resolution (/api/v1/users/{id}/permissions).
3. Account status lifecycle updates (ACTIVE -> SUSPENDED -> DEACTIVATED -> ACTIVE) and audit logging.
4. Defenses against Self-Lockout (Admin cannot deactivate, suspend, or revoke own ADMIN role).
5. Strict RBAC privilege escalation prevention (Student & Librarian 403 on IAM mutations).
6. Strict zero-exposure of sensitive authentication credentials (password_hash, mfa_secret, tokens).
7. Audit log generation for all security-sensitive IAM events.
"""

import uuid
from fastapi.testclient import TestClient
import pytest

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.main import app
from app.models.audit_log import AuditAction, AuditLog
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.permissions.service import permission_service


@pytest.fixture(autouse=True)
def ensure_rbac_seeded():
    """Ensure database has default roles and permissions initialized."""
    with SessionLocal() as db:
        permission_service.seed_default_roles_and_permissions(db)


@pytest.fixture
def iam_users():
    """Provisions Admin, Librarian, Student, and a Target Test User for IAM testing."""
    with SessionLocal() as db:
        admin_role = db.query(Role).filter_by(name="ADMIN").first()
        librarian_role = db.query(Role).filter_by(name="LIBRARIAN").first()
        student_role = db.query(Role).filter_by(name="STUDENT").first()

        admin_user = User(
            email=f"admin.iam.{uuid.uuid4().hex[:6]}@iam-test.example.com",
            full_name="Admin IAM Administrator",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if admin_role:
            admin_user.roles.append(admin_role)

        librarian_user = User(
            email=f"librarian.iam.{uuid.uuid4().hex[:6]}@iam-test.example.com",
            full_name="Librarian IAM Tester",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if librarian_role:
            librarian_user.roles.append(librarian_role)

        student_user = User(
            email=f"student.iam.{uuid.uuid4().hex[:6]}@iam-test.example.com",
            full_name="Student IAM Tester",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if student_role:
            student_user.roles.append(student_role)

        target_user = User(
            email=f"target.iam.{uuid.uuid4().hex[:6]}@iam-test.example.com",
            full_name="Target Member Under Management",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if student_role:
            target_user.roles.append(student_role)

        db.add_all([admin_user, librarian_user, student_user, target_user])
        db.commit()

        return {
            "admin_id": admin_user.id,
            "admin_email": admin_user.email,
            "librarian_id": librarian_user.id,
            "librarian_email": librarian_user.email,
            "student_id": student_user.id,
            "student_email": student_user.email,
            "target_id": target_user.id,
            "target_email": target_user.email,
        }


@pytest.fixture
def client():
    return TestClient(app)


def auth_headers(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


class TestUserListingAndFilters:
    """Tests for GET /api/v1/users with search and filtering."""

    def test_admin_can_list_users(self, client, iam_users):
        res = client.get("/api/v1/users", headers=auth_headers(iam_users["admin_id"]))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 4

    def test_admin_can_filter_users_by_search(self, client, iam_users):
        res = client.get(
            "/api/v1/users?search=Target Member",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(u["id"] == str(iam_users["target_id"]) for u in data)

    def test_admin_can_filter_users_by_status(self, client, iam_users):
        res = client.get(
            "/api/v1/users?account_status=ACTIVE",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert all(u["account_status"] == "ACTIVE" for u in data)

    def test_admin_can_filter_users_by_role(self, client, iam_users):
        res = client.get(
            "/api/v1/users?role=ADMIN",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any("ADMIN" in u["roles"] for u in data)

    def test_student_cannot_list_users(self, client, iam_users):
        res = client.get("/api/v1/users", headers=auth_headers(iam_users["student_id"]))
        assert res.status_code == 403

    def test_unauthenticated_cannot_list_users(self, client):
        res = client.get("/api/v1/users")
        assert res.status_code == 401


class TestUserDetailsAndPermissions:
    """Tests for GET /api/v1/users/{id} and /api/v1/users/{id}/permissions."""

    def test_admin_can_view_user_details(self, client, iam_users):
        res = client.get(
            f"/api/v1/users/{iam_users['target_id']}",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == str(iam_users["target_id"])
        assert data["email"] == iam_users["target_email"]
        assert "STUDENT" in data["roles"]
        assert data["is_verified"] is True

    def test_user_details_reports_email_verification_status(self, client, iam_users):
        """Active user is verified; PENDING_VERIFICATION user is not verified."""
        with SessionLocal() as db:
            pending_user = User(
                email=f"pending.{uuid.uuid4().hex[:6]}@iam-test.example.com",
                full_name="Pending Verification User",
                password_hash="argon2id$mocked",
                account_status=AccountStatus.PENDING_VERIFICATION,
            )
            db.add(pending_user)
            db.commit()
            pending_id = pending_user.id

        # Target user is ACTIVE -> is_verified must be True
        res_active = client.get(
            f"/api/v1/users/{iam_users['target_id']}",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res_active.status_code == 200
        assert res_active.json()["is_verified"] is True

        # Pending user is PENDING_VERIFICATION -> is_verified must be False
        res_pending = client.get(
            f"/api/v1/users/{pending_id}",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res_pending.status_code == 200
        assert res_pending.json()["is_verified"] is False
        assert res_pending.json()["account_status"] == "PENDING_VERIFICATION"

    def test_admin_can_view_effective_permissions(self, client, iam_users):
        res = client.get(
            f"/api/v1/users/{iam_users['target_id']}/permissions",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 200
        data = res.json()
        assert "permissions" in data
        assert "book:view" in data["permissions"]

    def test_student_cannot_view_other_user_permissions(self, client, iam_users):
        res = client.get(
            f"/api/v1/users/{iam_users['target_id']}/permissions",
            headers=auth_headers(iam_users["student_id"]),
        )
        assert res.status_code == 403


class TestAccountStatusTransitionsAndSelfLockout:
    """Tests for PATCH /api/v1/users/{id}/status and self-lockout prevention."""

    def test_admin_can_suspend_and_reactivate_user(self, client, iam_users):
        target_id = iam_users["target_id"]

        # Suspend
        res = client.patch(
            f"/api/v1/users/{target_id}/status",
            json={"account_status": "SUSPENDED"},
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 200
        assert res.json()["account_status"] == "SUSPENDED"

        # Verify audit log recorded
        with SessionLocal() as db:
            log = (
                db.query(AuditLog)
                .filter(
                    AuditLog.resource_id.like(f"{target_id}%"),
                    AuditLog.action == AuditAction.USER_SUSPENDED,
                )
                .first()
            )
            assert log is not None
            assert log.user_id == iam_users["admin_id"]

        # Reactivate
        res2 = client.patch(
            f"/api/v1/users/{target_id}/status",
            json={"account_status": "ACTIVE"},
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res2.status_code == 200
        assert res2.json()["account_status"] == "ACTIVE"

    def test_admin_can_deactivate_user(self, client, iam_users):
        target_id = iam_users["target_id"]
        res = client.patch(
            f"/api/v1/users/{target_id}/status",
            json={"account_status": "DEACTIVATED"},
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 200
        assert res.json()["account_status"] == "DEACTIVATED"

        with SessionLocal() as db:
            log = (
                db.query(AuditLog)
                .filter(
                    AuditLog.resource_id.like(f"{target_id}%"),
                    AuditLog.action == AuditAction.USER_DEACTIVATED,
                )
                .first()
            )
            assert log is not None
            assert log.user_id == iam_users["admin_id"]

    def test_admin_self_lockout_deactivate_prevention(self, client, iam_users):
        """Admin must NOT be allowed to deactivate their own account."""
        admin_id = iam_users["admin_id"]
        res = client.patch(
            f"/api/v1/users/{admin_id}/status",
            json={"account_status": "DEACTIVATED"},
            headers=auth_headers(admin_id),
        )
        assert res.status_code == 400
        assert "Self-lockout protection" in res.json()["detail"]

    def test_admin_self_lockout_suspend_prevention(self, client, iam_users):
        """Admin must NOT be allowed to suspend their own account."""
        admin_id = iam_users["admin_id"]
        res = client.patch(
            f"/api/v1/users/{admin_id}/status",
            json={"account_status": "SUSPENDED"},
            headers=auth_headers(admin_id),
        )
        assert res.status_code == 400
        assert "Self-lockout protection" in res.json()["detail"]

    def test_student_cannot_change_account_status(self, client, iam_users):
        res = client.patch(
            f"/api/v1/users/{iam_users['target_id']}/status",
            json={"account_status": "SUSPENDED"},
            headers=auth_headers(iam_users["student_id"]),
        )
        assert res.status_code == 403


class TestRoleAssignmentRevocationAndSelfLockout:
    """Tests for Role assignment, revocation, and self-lockout protections."""

    def test_admin_can_assign_and_revoke_role(self, client, iam_users):
        target_id = iam_users["target_id"]

        # Assign LIBRARIAN role
        res = client.post(
            f"/api/v1/users/{target_id}/roles",
            json={"role_name": "LIBRARIAN"},
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 200
        assert "LIBRARIAN" in res.json()["roles"]

        # Verify audit log recorded
        with SessionLocal() as db:
            log = (
                db.query(AuditLog)
                .filter(
                    AuditLog.resource_id.like(f"{target_id}%"),
                    AuditLog.action == AuditAction.ROLE_ASSIGNED,
                )
                .first()
            )
            assert log is not None

        # Revoke LIBRARIAN role
        res2 = client.delete(
            f"/api/v1/users/{target_id}/roles/LIBRARIAN",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res2.status_code == 200
        assert "LIBRARIAN" not in res2.json()["roles"]

        # Verify audit log recorded
        with SessionLocal() as db:
            log2 = (
                db.query(AuditLog)
                .filter(
                    AuditLog.resource_id.like(f"{target_id}%"),
                    AuditLog.action == AuditAction.ROLE_REVOKED,
                )
                .first()
            )
            assert log2 is not None

    def test_grant_additional_role_to_student_preserves_student_role(self, client, iam_users):
        """Granting an additional role to a student patron retains STUDENT and appends the new role."""
        target_id = iam_users["target_id"]

        # Ensure user starts with only STUDENT role
        get_res = client.get(
            f"/api/v1/users/{target_id}",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert get_res.status_code == 200
        assert get_res.json()["roles"] == ["STUDENT"]
        assert get_res.json()["is_verified"] is True

        # Grant additional LIBRARIAN role
        assign_res = client.post(
            f"/api/v1/users/{target_id}/roles",
            json={"role_name": "LIBRARIAN"},
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert assign_res.status_code == 200
        assigned_roles = assign_res.json()["roles"]
        assert "STUDENT" in assigned_roles
        assert "LIBRARIAN" in assigned_roles
        assert assign_res.json()["is_verified"] is True

        # Verify persisted state via GET
        verify_res = client.get(
            f"/api/v1/users/{target_id}",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert verify_res.status_code == 200
        persisted_roles = verify_res.json()["roles"]
        assert "STUDENT" in persisted_roles
        assert "LIBRARIAN" in persisted_roles
        assert verify_res.json()["is_verified"] is True

        # Clean up: revoke LIBRARIAN role
        client.delete(
            f"/api/v1/users/{target_id}/roles/LIBRARIAN",
            headers=auth_headers(iam_users["admin_id"]),
        )

    def test_admin_cannot_revoke_own_admin_role(self, client, iam_users):
        """Admin must NOT be allowed to revoke their own ADMIN role."""
        admin_id = iam_users["admin_id"]
        res = client.delete(
            f"/api/v1/users/{admin_id}/roles/ADMIN",
            headers=auth_headers(admin_id),
        )
        assert res.status_code == 400
        assert "Self-lockout protection" in res.json()["detail"]

    def test_student_cannot_assign_roles(self, client, iam_users):
        res = client.post(
            f"/api/v1/users/{iam_users['target_id']}/roles",
            json={"role_name": "ADMIN"},
            headers=auth_headers(iam_users["student_id"]),
        )
        assert res.status_code == 403

    def test_student_cannot_revoke_roles(self, client, iam_users):
        res = client.delete(
            f"/api/v1/users/{iam_users['target_id']}/roles/STUDENT",
            headers=auth_headers(iam_users["student_id"]),
        )
        assert res.status_code == 403

    def test_list_roles_returns_only_supported_application_roles(self, client, iam_users):
        """GET /api/v1/roles must only return supported application roles (ADMIN, LIBRARIAN, STUDENT, GUEST)."""
        res = client.get("/api/v1/roles", headers=auth_headers(iam_users["admin_id"]))
        assert res.status_code == 200
        roles = res.json()
        role_names = [r["name"] for r in roles]
        assert set(role_names) == {"ADMIN", "LIBRARIAN", "STUDENT", "GUEST"}
        assert not any(name.startswith("ARCHIVIST_") for name in role_names)

    def test_list_roles_assignable_only_excludes_guest(self, client, iam_users):
        """GET /api/v1/roles?assignable_only=true must only return assignable roles (ADMIN, LIBRARIAN, STUDENT), excluding GUEST."""
        res = client.get(
            "/api/v1/roles?assignable_only=true",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 200
        roles = res.json()
        role_names = [r["name"] for r in roles]
        assert set(role_names) == {"ADMIN", "LIBRARIAN", "STUDENT"}
        assert "GUEST" not in role_names

    def test_assign_guest_role_to_user_is_rejected(self, client, iam_users):
        """Assigning GUEST role to a user account is forbidden (public unauthenticated concept only)."""
        target_id = iam_users["target_id"]
        res = client.post(
            f"/api/v1/users/{target_id}/roles",
            json={"role_name": "GUEST"},
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 400
        assert "GUEST is a public, unauthenticated role concept" in res.json()["detail"]

    def test_assign_unsupported_role_is_rejected(self, client, iam_users):
        """Assigning unsupported/custom role (e.g. ARCHIVIST_TEST) is rejected with 400."""
        target_id = iam_users["target_id"]
        res = client.post(
            f"/api/v1/users/{target_id}/roles",
            json={"role_name": "ARCHIVIST_TEST"},
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert res.status_code == 400
        assert "not a supported assignable application role" in res.json()["detail"]


class TestSensitiveFieldExposurePrevention:
    """Verifies that sensitive credentials and secrets are NEVER exposed."""

    def test_user_responses_never_expose_secrets(self, client, iam_users):
        # 1. User List
        list_res = client.get("/api/v1/users", headers=auth_headers(iam_users["admin_id"]))
        assert list_res.status_code == 200
        for user_item in list_res.json():
            assert "password" not in user_item
            assert "password_hash" not in user_item
            assert "mfa_secret" not in user_item
            assert "refresh_token" not in user_item
            assert "refresh_token_hash" not in user_item
            assert "recovery_codes" not in user_item
            assert "password_reset_token" not in user_item

        # 2. User Detail
        detail_res = client.get(
            f"/api/v1/users/{iam_users['target_id']}",
            headers=auth_headers(iam_users["admin_id"]),
        )
        assert detail_res.status_code == 200
        target_dict = detail_res.json()
        assert "password" not in target_dict
        assert "password_hash" not in target_dict
        assert "mfa_secret" not in target_dict
        assert "refresh_token" not in target_dict
        assert "recovery_codes" not in target_dict
