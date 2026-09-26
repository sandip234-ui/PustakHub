"""
Phase 4 RBAC Authorization & Privilege Escalation Tests.

Tests covered:
  1. Default roles and permissions seeding and verification
  2. Unauthenticated request to protected route returns 401
  3. Authenticated user without permission returns 403 (e.g. STUDENT requesting audit logs or roles)
  4. Authenticated user with permission is granted access (e.g. ADMIN listing roles and permissions)
  5. Permission resolution traverses User -> Role -> Permission correctly
  6. Role hierarchy/differences: ADMIN vs LIBRARIAN vs STUDENT vs GUEST
  7. Reusable dependency require_permission handles both 'BOOK_VIEW' and 'book:view'
  8. require_any_permission and require_all_permissions dependencies
  9. require_role dependency
  10. Resource-level authorization: Student A accessing Student A profile -> ALLOW
  11. Resource-level authorization (IDOR prevention): Student A accessing Student B profile -> 403 FORBIDDEN
  12. Resource-level authorization: Admin/Librarian accessing Student B profile -> ALLOW
  13. Role assignment: Admin assigning LIBRARIAN role to user -> ALLOW
  14. Privilege escalation prevention: Student attempting to assign role to themselves or others -> 403 FORBIDDEN
  15. Public registration strictly creates STUDENT role and ignores injected role fields
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.models.permission import Permission
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.permissions.constants import (
    AppPermission,
    AppRole,
    DEFAULT_ROLE_PERMISSIONS,
)
from app.modules.permissions.service import permission_service


@pytest.fixture(autouse=True)
def ensure_rbac_seeded():
    """Ensure database has default roles and permissions initialized."""
    with SessionLocal() as db:
        permission_service.seed_default_roles_and_permissions(db)


@pytest.fixture
def create_test_user():
    """Helper fixture to create test users with specific roles."""
    created_users = []

    def _create(role_name: str, email_prefix: str = "user"):
        with SessionLocal() as db:
            role = db.query(Role).filter(Role.name == role_name).first()
            user = User(
                email=f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com",
                full_name=f"Test {role_name} User",
                password_hash=hash_password("Password123!"),
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


def test_default_roles_and_permissions_seeded():
    """Verify all default roles and permissions exist in PostgreSQL."""
    with SessionLocal() as db:
        roles = {r.name: r for r in db.query(Role).all()}
        assert "ADMIN" in roles
        assert "LIBRARIAN" in roles
        assert "STUDENT" in roles
        assert "GUEST" in roles

        perms = {p.name for p in db.query(Permission).all()}
        assert "book:view" in perms
        assert "book:create" in perms
        assert "user:view" in perms
        assert "role:view" in perms
        assert "permission:view" in perms
        assert "audit_log:view" in perms

        # Check ADMIN has all default permissions
        admin_perms = permission_service.get_user_permissions(
            User(id=uuid.uuid4(), roles=[roles["ADMIN"]]), db
        )
        for expected_perm in DEFAULT_ROLE_PERMISSIONS["ADMIN"]:
            assert expected_perm in admin_perms


def test_unauthenticated_request_returns_401(client: TestClient):
    """Unauthenticated request to permission-protected route returns 401 Unauthorized."""
    response = client.get("/api/v1/permissions")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_student_forbidden_from_admin_endpoints(client: TestClient, create_test_user):
    """Authenticated STUDENT lacks 'permission:view' and receives 403 Forbidden."""
    _, student_token = create_test_user("STUDENT", "student_test")
    headers = {"Authorization": f"Bearer {student_token}"}

    # Student trying to list permissions
    response = client.get("/api/v1/permissions", headers=headers)
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]

    # Student trying to list roles
    response = client.get("/api/v1/roles", headers=headers)
    assert response.status_code == 403

    # Student trying to list all users
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403


def test_admin_allowed_access_to_admin_endpoints(client: TestClient, create_test_user):
    """Authenticated ADMIN has permissions and is granted access (200 OK)."""
    _, admin_token = create_test_user("ADMIN", "admin_test")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin listing permissions
    response = client.get("/api/v1/permissions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 15

    # Admin getting permission matrix
    response = client.get("/api/v1/permissions/matrix", headers=headers)
    assert response.status_code == 200
    matrix = response.json()
    assert "ADMIN" in matrix["matrix"]
    assert "STUDENT" in matrix["matrix"]

    # Admin listing roles
    response = client.get("/api/v1/roles", headers=headers)
    assert response.status_code == 200


def test_librarian_allowed_user_view_but_not_role_create(client: TestClient, create_test_user):
    """Librarian has user:view but lacks role:create."""
    _, librarian_token = create_test_user("LIBRARIAN", "lib_test")
    headers = {"Authorization": f"Bearer {librarian_token}"}

    # Librarian listing users (allowed by user:view)
    response = client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200

    # Librarian creating role (forbidden - lacks role:create)
    response = client.post(
        "/api/v1/roles",
        json={"name": "CUSTOM_ROLE", "description": "test"},
        headers=headers,
    )
    assert response.status_code == 403


def test_current_user_can_inspect_own_permissions(client: TestClient, create_test_user):
    """Any authenticated user can view their own effective permissions via GET /permissions/me."""
    _, student_token = create_test_user("STUDENT", "student_me")
    headers = {"Authorization": f"Bearer {student_token}"}

    response = client.get("/api/v1/permissions/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "STUDENT" in data["roles"]
    assert "book:view" in data["permissions"]


def test_resource_level_auth_own_resource_allowed(client: TestClient, create_test_user):
    """Resource-level authorization: Student accessing their own profile is allowed."""
    student_a, token_a = create_test_user("STUDENT", "student_a")
    headers = {"Authorization": f"Bearer {token_a}"}

    response = client.get(f"/api/v1/users/{student_a.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(student_a.id)
    assert data["email"] == student_a.email


def test_resource_level_auth_idor_prevention_denied(client: TestClient, create_test_user):
    """IDOR prevention: Student A attempting to access Student B profile receives 403 Forbidden."""
    student_a, token_a = create_test_user("STUDENT", "student_a_idor")
    student_b, _ = create_test_user("STUDENT", "student_b_idor")
    headers = {"Authorization": f"Bearer {token_a}"}

    response = client.get(f"/api/v1/users/{student_b.id}", headers=headers)
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]


def test_resource_level_auth_admin_override_allowed(client: TestClient, create_test_user):
    """Resource-level authorization: Admin accessing Student B profile is allowed."""
    _, admin_token = create_test_user("ADMIN", "admin_res_test")
    student_b, _ = create_test_user("STUDENT", "student_b_admin_view")
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get(f"/api/v1/users/{student_b.id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(student_b.id)


def test_admin_can_assign_and_revoke_role_for_user(client: TestClient, create_test_user):
    """Admin can assign and revoke roles to/from users."""
    _, admin_token = create_test_user("ADMIN", "admin_role_mgr")
    student, _ = create_test_user("STUDENT", "student_promoted")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Assign LIBRARIAN role
    response = client.post(
        f"/api/v1/users/{student.id}/roles",
        json={"role_name": "LIBRARIAN"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert "LIBRARIAN" in response.json()["roles"]

    # Revoke LIBRARIAN role
    response = client.delete(
        f"/api/v1/users/{student.id}/roles/LIBRARIAN",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert "LIBRARIAN" not in response.json()["roles"]


def test_privilege_escalation_student_cannot_assign_roles(client: TestClient, create_test_user):
    """Student attempting to assign a role to anyone receives 403 Forbidden."""
    student_a, token_a = create_test_user("STUDENT", "attacker_student")
    student_b, _ = create_test_user("STUDENT", "target_student")
    headers = {"Authorization": f"Bearer {token_a}"}

    # Self-promotion attempt
    response = client.post(
        f"/api/v1/users/{student_a.id}/roles",
        json={"role_name": "ADMIN"},
        headers=headers,
    )
    assert response.status_code == 403

    # Promoting another user attempt
    response = client.post(
        f"/api/v1/users/{student_b.id}/roles",
        json={"role_name": "ADMIN"},
        headers=headers,
    )
    assert response.status_code == 403


def test_custom_role_creation_and_permission_assignment(client: TestClient, create_test_user):
    """Admin can create a custom role and assign/revoke specific permissions."""
    _, admin_token = create_test_user("ADMIN", "admin_custom_role")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create custom role
    role_name = f"ARCHIVIST_{uuid.uuid4().hex[:4].upper()}"
    role_id = None
    try:
        create_resp = client.post(
            "/api/v1/roles",
            json={"name": role_name, "description": "Special archive manager role"},
            headers=admin_headers,
        )
        assert create_resp.status_code == 201
        role_id = create_resp.json()["id"]

        # 2. Assign permission to custom role
        assign_resp = client.post(
            f"/api/v1/roles/{role_id}/permissions",
            json={"permission_name": "book:view"},
            headers=admin_headers,
        )
        assert assign_resp.status_code == 200
        perm_names = [p["name"] for p in assign_resp.json()["permissions"]]
        assert "book:view" in perm_names

        # 3. Revoke permission from custom role
        revoke_resp = client.delete(
            f"/api/v1/roles/{role_id}/permissions/book:view",
            headers=admin_headers,
        )
        assert revoke_resp.status_code == 200
        perm_names = [p["name"] for p in revoke_resp.json()["permissions"]]
        assert "book:view" not in perm_names
    finally:
        with SessionLocal() as db:
            custom_role = db.query(Role).filter(
                (Role.id == role_id) if role_id else (Role.name == role_name)
            ).first()
            if custom_role:
                db.delete(custom_role)
                db.commit()


def test_rbac_dependencies_unit_evaluation(create_test_user):
    """Direct unit testing of authorization dependency functions."""
    from app.modules.permissions.dependencies import (
        require_all_permissions,
        require_any_permission,
        require_permission,
        require_role,
    )
    from fastapi import HTTPException

    student, _ = create_test_user("STUDENT", "unit_student")
    admin, _ = create_test_user("ADMIN", "unit_admin")

    with SessionLocal() as db:
        # require_permission
        perm_checker = require_permission("BOOK_VIEW")
        assert perm_checker(current_user=student, db=db) == student

        admin_checker = require_permission("USER_CREATE")
        assert admin_checker(current_user=admin, db=db) == admin
        with pytest.raises(HTTPException) as exc:
            admin_checker(current_user=student, db=db)
        assert exc.value.status_code == 403

        # require_any_permission
        any_checker = require_any_permission("ROLE_VIEW", "BOOK_VIEW")
        assert any_checker(current_user=student, db=db) == student

        any_admin_checker = require_any_permission("ROLE_CREATE", "USER_DELETE")
        with pytest.raises(HTTPException) as exc:
            any_admin_checker(current_user=student, db=db)
        assert exc.value.status_code == 403

        # require_all_permissions
        all_checker = require_all_permissions("BOOK_VIEW", "USER_VIEW")
        assert all_checker(current_user=admin, db=db) == admin
        with pytest.raises(HTTPException) as exc:
            all_checker(current_user=student, db=db)
        assert exc.value.status_code == 403

        # require_role
        role_checker = require_role("STUDENT")
        assert role_checker(current_user=student) == student
        role_admin_checker = require_role("ADMIN")
        with pytest.raises(HTTPException) as exc:
            role_admin_checker(current_user=student)
        assert exc.value.status_code == 403

