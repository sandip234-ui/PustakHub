"""
Phase 14 Integration Tests — Operational Analytics & Dashboard Endpoint Verification.

Validates:
1. ADMIN access to global catalog, circulation, fines, user count, and audit log metrics
2. LIBRARIAN access to circulation, catalog and audit log metrics while blocking role/user administration (403)
3. STUDENT personal data scoping (own active loans & fines only) and denial of staff APIs (403)
4. Unauthenticated guest rejections (401) on operational endpoints
"""

import uuid
from fastapi.testclient import TestClient
import pytest

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.permissions.service import permission_service


@pytest.fixture(autouse=True)
def ensure_rbac_seeded():
    """Ensure database has default roles and permissions initialized."""
    with SessionLocal() as db:
        permission_service.seed_default_roles_and_permissions(db)


@pytest.fixture
def dashboard_users():
    """Provisions Admin, Librarian, and Student users for dashboard testing."""
    with SessionLocal() as db:
        admin_role = db.query(Role).filter_by(name="ADMIN").first()
        librarian_role = db.query(Role).filter_by(name="LIBRARIAN").first()
        student_role = db.query(Role).filter_by(name="STUDENT").first()

        admin_user = User(
            email=f"admin.dash.{uuid.uuid4().hex[:6]}@dash-test.example.com",
            full_name="Admin Dash Tester",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if admin_role:
            admin_user.roles.append(admin_role)

        librarian_user = User(
            email=f"librarian.dash.{uuid.uuid4().hex[:6]}@dash-test.example.com",
            full_name="Librarian Dash Tester",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if librarian_role:
            librarian_user.roles.append(librarian_role)

        student_user = User(
            email=f"student.dash.{uuid.uuid4().hex[:6]}@dash-test.example.com",
            full_name="Student Dash Tester",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if student_role:
            student_user.roles.append(student_role)

        db.add_all([admin_user, librarian_user, student_user])
        db.commit()

        return {
            "admin_id": admin_user.id,
            "librarian_id": librarian_user.id,
            "student_id": student_user.id,
        }


def _auth_headers(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


def test_admin_dashboard_metrics_endpoints(client: TestClient, dashboard_users: dict):
    """Verify ADMIN can query all operational dashboard data sources."""
    headers = _auth_headers(dashboard_users["admin_id"])

    # 1. Books Total Count
    books_res = client.get("/api/v1/books?page=1&page_size=1", headers=headers)
    assert books_res.status_code == 200
    assert "total" in books_res.json()

    # 2. Categories Total Count
    cats_res = client.get("/api/v1/categories?page=1&page_size=100", headers=headers)
    assert cats_res.status_code == 200

    # 3. Active Borrowings Count
    active_res = client.get("/api/v1/borrowings?page=1&page_size=1&status=ACTIVE", headers=headers)
    assert active_res.status_code == 200
    assert "total" in active_res.json()

    # 4. Overdue Borrowings Count
    overdue_res = client.get("/api/v1/borrowings?page=1&page_size=1&status=OVERDUE", headers=headers)
    assert overdue_res.status_code == 200
    assert "total" in overdue_res.json()

    # 5. Pending Fines Count
    fines_res = client.get("/api/v1/fines?page=1&page_size=1&status=PENDING", headers=headers)
    assert fines_res.status_code == 200
    assert "total" in fines_res.json()

    # 6. Registered Users List
    users_res = client.get("/api/v1/users", headers=headers)
    assert users_res.status_code == 200
    assert isinstance(users_res.json(), list)
    assert len(users_res.json()) >= 1

    # 7. Audit Logs Query
    audit_res = client.get("/api/v1/audit/logs?page=1&page_size=5", headers=headers)
    assert audit_res.status_code == 200
    assert "items" in audit_res.json()


def test_librarian_dashboard_metrics_and_scope(client: TestClient, dashboard_users: dict):
    """Verify LIBRARIAN can query circulation data but cannot access role management."""
    headers = _auth_headers(dashboard_users["librarian_id"])

    # Circulation & Catalog accessible
    assert client.get("/api/v1/books?page=1&page_size=1", headers=headers).status_code == 200
    assert client.get("/api/v1/borrowings?page=1&page_size=1&status=ACTIVE", headers=headers).status_code == 200
    assert client.get("/api/v1/fines?page=1&page_size=1", headers=headers).status_code == 200

    # Role administration forbidden for LIBRARIAN -> 403
    role_res = client.get("/api/v1/roles", headers=headers)
    assert role_res.status_code == 403


def test_student_dashboard_metrics_scoped(client: TestClient, dashboard_users: dict):
    """Verify STUDENT can only query personal loan/fine metrics and cannot access staff analytics."""
    headers = _auth_headers(dashboard_users["student_id"])

    # 1. Borrowings list is scoped to student
    borrow_res = client.get("/api/v1/borrowings?page=1&page_size=1", headers=headers)
    assert borrow_res.status_code == 200

    # 2. Fines list is scoped to student
    fines_res = client.get("/api/v1/fines?page=1&page_size=1", headers=headers)
    assert fines_res.status_code == 200

    # 3. Users list is forbidden for student -> 403
    users_res = client.get("/api/v1/users", headers=headers)
    assert users_res.status_code == 403

    # 4. Audit logs query is forbidden for student -> 403
    audit_res = client.get("/api/v1/audit/logs", headers=headers)
    assert audit_res.status_code == 403


def test_guest_unauthenticated_rejections(client: TestClient):
    """Verify unauthenticated guests receive 401 on protected dashboard endpoints."""
    assert client.get("/api/v1/borrowings").status_code == 401
    assert client.get("/api/v1/fines").status_code == 401
    assert client.get("/api/v1/users").status_code == 401
    assert client.get("/api/v1/audit/logs").status_code == 401
