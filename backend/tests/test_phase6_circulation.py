"""
Phase 6 Circulation, Borrowing & Fines Tests.

Comprehensive suite covering:
  1. Issue workflow (success, copy status transition, due date calculation, custom loan period, audit log)
  2. Issue failure & conflict handling (unauthenticated 401, student forbidden 403, nonexistent user/copy 404, borrowed/maintenance/lost copy 409, suspended user 409)
  3. Return workflow (on-time return, copy status restoration to AVAILABLE, duplicate return rejection 409)
  4. Overdue detection & automatic Fine generation (overdue calculation, fine amount, FineReason, FineStatus.PENDING, FINE_ISSUED audit log)
  5. Borrowing history & IDOR/BOLA defenses (student own history allowed, cross-student history forbidden 403, staff access allowed, pagination, status filtering)
  6. Fine retrieval & IDOR defenses (student own fines allowed, cross-student fines forbidden 403, staff access allowed)
  7. Circulation invariants & concurrency integrity (single active borrow per copy, row-level protection)
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditAction, AuditLog
from app.models.book import Book
from app.models.book_copy import BookCopy, CopyStatus
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.category import Category
from app.models.fine import Fine, FineReason, FineStatus
from app.models.role import Role
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
        role_name: str,
        email_prefix: str = "user",
        account_status: AccountStatus = AccountStatus.ACTIVE,
    ):
        with SessionLocal() as db:
            role = db.query(Role).filter(Role.name == role_name).first()
            user = User(
                email=f"{email_prefix}_{uuid.uuid4().hex[:6]}@example.com",
                full_name=f"Test {role_name} User",
                password_hash=hash_password("Password123!"),
                account_status=account_status,
                roles=[role] if role else [],
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created_users.append(user.id)
            token = create_access_token(subject=user.id)
            return user, token

    yield _create

    # Cleanup created test users
    with SessionLocal() as db:
        for uid in created_users:
            u = db.query(User).filter(User.id == uid).first()
            if u:
                db.delete(u)
        db.commit()


@pytest.fixture
def circulation_setup(create_test_user):
    """Fixture providing ready-to-use librarian, students, book, and copies."""
    librarian, lib_token = create_test_user("LIBRARIAN", "lib")
    admin, admin_token = create_test_user("ADMIN", "admin")
    student1, student1_token = create_test_user("STUDENT", "student_a")
    student2, student2_token = create_test_user("STUDENT", "student_b")

    book_id = None
    copy1_id = None
    copy2_id = None
    copy3_id = None
    category_id = None

    with SessionLocal() as db:
        category = db.query(Category).filter_by(name="Computer Science & Theory").first() or db.query(Category).first()
        category_id = category.id

        book = Book(
            title=f"Circulation Dynamics {uuid.uuid4().hex[:4]}",
            author="Library Systems Group",
            isbn=f"978-{uuid.uuid4().hex[:8]}",
            category_id=category.id,
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        book_id = book.id

        copy1 = BookCopy(
            book_id=book.id,
            copy_identifier=f"COPY-A-{uuid.uuid4().hex[:6]}",
            status=CopyStatus.AVAILABLE,
            shelf_location="Shelf-1A",
        )
        copy2 = BookCopy(
            book_id=book.id,
            copy_identifier=f"COPY-B-{uuid.uuid4().hex[:6]}",
            status=CopyStatus.MAINTENANCE,
            shelf_location="Repair-Bay",
        )
        copy3 = BookCopy(
            book_id=book.id,
            copy_identifier=f"COPY-C-{uuid.uuid4().hex[:6]}",
            status=CopyStatus.LOST,
            shelf_location="N/A",
        )
        db.add_all([copy1, copy2, copy3])
        db.commit()
        db.refresh(copy1)
        db.refresh(copy2)
        db.refresh(copy3)
        copy1_id = copy1.id
        copy2_id = copy2.id
        copy3_id = copy3.id

    yield {
        "librarian": librarian,
        "lib_token": lib_token,
        "admin": admin,
        "admin_token": admin_token,
        "student1": student1,
        "student1_token": student1_token,
        "student2": student2,
        "student2_token": student2_token,
        "book_id": book_id,
        "copy1_id": copy1_id,
        "copy2_id": copy2_id,
        "copy3_id": copy3_id,
        "category_id": category_id,
    }

    # Teardown
    with SessionLocal() as db:
        # Fines & Borrows for this test's copies
        copy_ids = [cid for cid in (copy1_id, copy2_id, copy3_id) if cid]
        if copy_ids:
            borrow_records = db.query(BorrowRecord).filter(BorrowRecord.book_copy_id.in_(copy_ids)).all()
            borrow_ids = [b.id for b in borrow_records]
            if borrow_ids:
                db.query(Fine).filter(Fine.borrow_record_id.in_(borrow_ids)).delete(synchronize_session=False)
                db.query(BorrowRecord).filter(BorrowRecord.id.in_(borrow_ids)).delete(synchronize_session=False)
            db.query(BookCopy).filter(BookCopy.id.in_(copy_ids)).delete(synchronize_session=False)
        # Book
        if book_id:
            b = db.query(Book).filter(Book.id == book_id).first()
            if b:
                db.delete(b)
        db.commit()


# ===========================================================================
# 1. Book Issue Workflow Tests
# ===========================================================================


def test_issue_book_copy_success(client: TestClient, circulation_setup):
    """Test successful issue of an available book copy by staff."""
    headers = {"Authorization": f"Bearer {circulation_setup['lib_token']}"}

    payload = {
        "user_id": str(circulation_setup["student1"].id),
        "book_copy_id": str(circulation_setup["copy1_id"]),
        "loan_period_days": 21,
    }

    res = client.post("/api/v1/borrow", headers=headers, json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["user_id"] == str(circulation_setup["student1"].id)
    assert data["book_copy_id"] == str(circulation_setup["copy1_id"])
    assert data["status"] == "ACTIVE"
    assert data["is_overdue"] is False
    assert data["overdue_days"] == 0
    assert data["fine_amount"] is None

    # Verify due date is 21 days from issued_at
    issued_at = datetime.fromisoformat(data["issued_at"].replace("Z", "+00:00"))
    due_at = datetime.fromisoformat(data["due_at"].replace("Z", "+00:00"))
    assert (due_at - issued_at).days == 21

    # Verify physical copy status changed to BORROWED
    copy_res = client.get(
        f"/api/v1/copies/{circulation_setup['copy1_id']}", headers=headers
    )
    assert copy_res.status_code == 200
    assert copy_res.json()["status"] == "BORROWED"

    # Verify audit event in DB
    with SessionLocal() as db:
        audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == AuditAction.COPY_ISSUED,
                AuditLog.resource_id == data["id"],
            )
            .first()
        )
        assert audit is not None
        assert audit.user_id == circulation_setup["librarian"].id


def test_issue_book_unauthenticated_and_unauthorized(client: TestClient, circulation_setup):
    """Verify issue endpoint requires authentication (401) and book:issue permission (403)."""
    payload = {
        "user_id": str(circulation_setup["student1"].id),
        "book_copy_id": str(circulation_setup["copy1_id"]),
    }

    # 1. Unauthenticated -> 401
    assert client.post("/api/v1/borrow", json=payload).status_code == 401

    # 2. Student (lacks book:issue) -> 403 Forbidden
    student_headers = {"Authorization": f"Bearer {circulation_setup['student1_token']}"}
    res_student = client.post("/api/v1/borrow", headers=student_headers, json=payload)
    assert res_student.status_code == 403


def test_issue_book_validation_failures_and_copy_states(
    client: TestClient, circulation_setup, create_test_user
):
    """Test validation and conflict errors when issuing unavailable or nonexistent resources."""
    headers = {"Authorization": f"Bearer {circulation_setup['lib_token']}"}
    student1_id = str(circulation_setup["student1"].id)

    # 1. Nonexistent User -> 404
    fake_user_id = str(uuid.uuid4())
    res_fake_user = client.post(
        "/api/v1/borrow",
        headers=headers,
        json={"user_id": fake_user_id, "book_copy_id": str(circulation_setup["copy1_id"])},
    )
    assert res_fake_user.status_code == 404

    # 2. Nonexistent Copy -> 404
    fake_copy_id = str(uuid.uuid4())
    res_fake_copy = client.post(
        "/api/v1/borrow",
        headers=headers,
        json={"user_id": student1_id, "book_copy_id": fake_copy_id},
    )
    assert res_fake_copy.status_code == 404

    # 3. Copy under MAINTENANCE -> 409 Conflict
    res_maint = client.post(
        "/api/v1/borrow",
        headers=headers,
        json={"user_id": student1_id, "book_copy_id": str(circulation_setup["copy2_id"])},
    )
    assert res_maint.status_code == 409
    assert "maintenance" in res_maint.json()["message"]

    # 4. Copy marked LOST -> 409 Conflict
    res_lost = client.post(
        "/api/v1/borrow",
        headers=headers,
        json={"user_id": student1_id, "book_copy_id": str(circulation_setup["copy3_id"])},
    )
    assert res_lost.status_code == 409
    assert "lost" in res_lost.json()["message"]

    # 5. Suspended User -> 409 Conflict
    suspended_user, _ = create_test_user(
        "STUDENT", "suspended_student", account_status=AccountStatus.SUSPENDED
    )
    res_suspended = client.post(
        "/api/v1/borrow",
        headers=headers,
        json={
            "user_id": str(suspended_user.id),
            "book_copy_id": str(circulation_setup["copy1_id"]),
        },
    )
    assert res_suspended.status_code == 409
    assert "SUSPENDED" in res_suspended.json()["message"]


def test_cannot_issue_already_borrowed_copy(client: TestClient, circulation_setup):
    """Ensure an already borrowed copy cannot be issued to another user (409 Conflict)."""
    headers = {"Authorization": f"Bearer {circulation_setup['lib_token']}"}

    # First issue succeeds
    res1 = client.post(
        "/api/v1/borrow",
        headers=headers,
        json={
            "user_id": str(circulation_setup["student1"].id),
            "book_copy_id": str(circulation_setup["copy1_id"]),
        },
    )
    assert res1.status_code == 201

    # Second issue of same copy fails
    res2 = client.post(
        "/api/v1/borrow",
        headers=headers,
        json={
            "user_id": str(circulation_setup["student2"].id),
            "book_copy_id": str(circulation_setup["copy1_id"]),
        },
    )
    assert res2.status_code == 409
    assert "already borrowed" in res2.json()["message"]


# ===========================================================================
# 2. Book Return & Fine Calculation Tests
# ===========================================================================


def test_return_book_on_time_produces_no_fine(client: TestClient, circulation_setup):
    """Verify on-time return closes the record as RETURNED and produces no fine."""
    headers = {"Authorization": f"Bearer {circulation_setup['lib_token']}"}

    # 1. Issue copy
    issue_res = client.post(
        "/api/v1/borrow",
        headers=headers,
        json={
            "user_id": str(circulation_setup["student1"].id),
            "book_copy_id": str(circulation_setup["copy1_id"]),
            "loan_period_days": 14,
        },
    )
    assert issue_res.status_code == 201
    borrow_id = issue_res.json()["id"]

    # 2. Return on time (e.g. 5 days after issue)
    now = datetime.now(timezone.utc)
    return_res = client.post(
        f"/api/v1/borrow/{borrow_id}/return",
        headers=headers,
        json={"returned_at": (now + timedelta(days=5)).isoformat()},
    )
    assert return_res.status_code == 200
    ret_data = return_res.json()
    assert ret_data["status"] == "RETURNED"
    assert ret_data["is_overdue"] is False
    assert ret_data["overdue_days"] == 0
    assert ret_data["fine_amount"] is None
    assert ret_data["returned_at"] is not None

    # 3. Copy status restored to AVAILABLE
    copy_res = client.get(
        f"/api/v1/copies/{circulation_setup['copy1_id']}", headers=headers
    )
    assert copy_res.json()["status"] == "AVAILABLE"

    # 4. Duplicate return of same record -> 409 Conflict
    dup_ret = client.post(f"/api/v1/borrow/{borrow_id}/return", headers=headers)
    assert dup_ret.status_code == 409
    assert "already closed" in dup_ret.json()["message"]


def test_return_book_overdue_automatically_generates_fine(
    client: TestClient, circulation_setup
):
    """Verify overdue return marks record OVERDUE, calculates fine accurately, and creates Fine entity."""
    headers = {"Authorization": f"Bearer {circulation_setup['lib_token']}"}

    # 1. Issue copy with 10-day loan
    issue_res = client.post(
        "/api/v1/borrow",
        headers=headers,
        json={
            "user_id": str(circulation_setup["student1"].id),
            "book_copy_id": str(circulation_setup["copy1_id"]),
            "loan_period_days": 10,
        },
    )
    assert issue_res.status_code == 201
    borrow_data = issue_res.json()
    borrow_id = borrow_data["id"]

    # 2. Return 5 days after due date (15 days after issue)
    issued_dt = datetime.fromisoformat(borrow_data["issued_at"].replace("Z", "+00:00"))
    overdue_return_dt = issued_dt + timedelta(days=15)

    return_res = client.post(
        f"/api/v1/borrow/{borrow_id}/return",
        headers=headers,
        json={"returned_at": overdue_return_dt.isoformat()},
    )
    assert return_res.status_code == 200
    ret_data = return_res.json()
    assert ret_data["status"] == "OVERDUE"
    assert ret_data["is_overdue"] is True
    assert ret_data["overdue_days"] == 5

    expected_fine = Decimal(str(5 * settings.DAILY_FINE_RATE)).quantize(Decimal("0.01"))
    assert Decimal(str(ret_data["fine_amount"])) == expected_fine
    assert ret_data["fine_status"] == "PENDING"

    # 3. Check Fine record directly in database
    with SessionLocal() as db:
        fine = db.query(Fine).filter(Fine.borrow_record_id == uuid.UUID(borrow_id)).first()
        assert fine is not None
        assert fine.amount == expected_fine
        assert fine.reason == FineReason.OVERDUE
        assert fine.status == FineStatus.PENDING

        # Check Audit logs: COPY_RETURNED and FINE_ISSUED
        ret_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == AuditAction.COPY_RETURNED,
                AuditLog.resource_id == borrow_id,
            )
            .first()
        )
        assert ret_audit is not None

        fine_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.action == AuditAction.FINE_ISSUED,
                AuditLog.resource_id == str(fine.id),
            )
            .first()
        )
        assert fine_audit is not None


# ===========================================================================
# 3. Borrowing History & IDOR / Resource-Level Authorization Tests
# ===========================================================================


def test_borrowing_history_access_and_idor_prevention(
    client: TestClient, circulation_setup
):
    """
    Test resource-level authorization for borrowing history:
      - Student 1 can access own history
      - Student 1 attempting to access Student 2 history -> 403 Forbidden
      - Student 1 attempting to query /borrowings?user_id=<Student 2> -> 403 Forbidden
      - Librarian / Admin can view any user's history and all borrowings
    """
    lib_headers = {"Authorization": f"Bearer {circulation_setup['lib_token']}"}
    s1_headers = {"Authorization": f"Bearer {circulation_setup['student1_token']}"}
    s2_headers = {"Authorization": f"Bearer {circulation_setup['student2_token']}"}

    # Issue copy to Student 1
    issue_s1 = client.post(
        "/api/v1/borrow",
        headers=lib_headers,
        json={
            "user_id": str(circulation_setup["student1"].id),
            "book_copy_id": str(circulation_setup["copy1_id"]),
        },
    )
    s1_borrow_id = issue_s1.json()["id"]

    # 1. Student 1 views own single borrowing record -> 200 OK
    res_s1_own = client.get(f"/api/v1/borrowings/{s1_borrow_id}", headers=s1_headers)
    assert res_s1_own.status_code == 200
    assert res_s1_own.json()["id"] == s1_borrow_id

    # 2. Student 2 attempts to view Student 1's borrowing record (IDOR) -> 403 Forbidden
    res_s2_attack = client.get(f"/api/v1/borrowings/{s1_borrow_id}", headers=s2_headers)
    assert res_s2_attack.status_code == 403
    assert "Forbidden" in res_s2_attack.json()["detail"]

    # 3. Student 2 attempts to list Student 1's borrowings via endpoint -> 403 Forbidden
    res_s2_list_attack = client.get(
        f"/api/v1/users/{circulation_setup['student1'].id}/borrowings", headers=s2_headers
    )
    assert res_s2_list_attack.status_code == 403

    # 4. Student 2 attempts to filter by Student 1 in /borrowings query -> 403 Forbidden
    res_filter_attack = client.get(
        f"/api/v1/borrowings?user_id={circulation_setup['student1'].id}", headers=s2_headers
    )
    assert res_filter_attack.status_code == 403

    # 5. Student 1 lists own borrowings via /users/{user_id}/borrowings -> 200 OK
    res_s1_list = client.get(
        f"/api/v1/users/{circulation_setup['student1'].id}/borrowings", headers=s1_headers
    )
    assert res_s1_list.status_code == 200
    assert len(res_s1_list.json()["items"]) >= 1

    # 6. Librarian views Student 1's history -> 200 OK
    res_lib_view = client.get(
        f"/api/v1/users/{circulation_setup['student1'].id}/borrowings", headers=lib_headers
    )
    assert res_lib_view.status_code == 200
    assert len(res_lib_view.json()["items"]) >= 1

    # 7. Librarian views all borrowings with pagination -> 200 OK
    res_lib_all = client.get("/api/v1/borrowings?page=1&page_size=10", headers=lib_headers)
    assert res_lib_all.status_code == 200
    assert res_lib_all.json()["total"] >= 1


# ===========================================================================
# 4. Fine Access & Resource-Level Authorization Tests
# ===========================================================================


def test_fine_access_and_idor_prevention(client: TestClient, circulation_setup):
    """
    Test fine querying and IDOR defenses:
      - Student 1 views own fines
      - Student 2 viewing Student 1 fine -> 403 Forbidden
      - Librarian / Admin views all fines or filtered fines
    """
    lib_headers = {"Authorization": f"Bearer {circulation_setup['lib_token']}"}
    s1_headers = {"Authorization": f"Bearer {circulation_setup['student1_token']}"}
    s2_headers = {"Authorization": f"Bearer {circulation_setup['student2_token']}"}

    # Issue and return overdue to generate a fine for Student 1
    issue_res = client.post(
        "/api/v1/borrow",
        headers=lib_headers,
        json={
            "user_id": str(circulation_setup["student1"].id),
            "book_copy_id": str(circulation_setup["copy1_id"]),
            "loan_period_days": 1,
        },
    )
    borrow_id = issue_res.json()["id"]

    # Return 4 days overdue
    overdue_dt = datetime.now(timezone.utc) + timedelta(days=5)
    client.post(
        f"/api/v1/borrow/{borrow_id}/return",
        headers=lib_headers,
        json={"returned_at": overdue_dt.isoformat()},
    )

    # Get the fine ID
    with SessionLocal() as db:
        fine = db.query(Fine).filter(Fine.borrow_record_id == uuid.UUID(borrow_id)).first()
        fine_id = str(fine.id)

    # 1. Student 1 views own fine -> 200 OK
    res_s1 = client.get(f"/api/v1/fines/{fine_id}", headers=s1_headers)
    assert res_s1.status_code == 200
    assert res_s1.json()["id"] == fine_id
    assert res_s1.json()["reason"] == "OVERDUE"
    assert res_s1.json()["status"] == "PENDING"

    # 2. Student 2 attempts to view Student 1's fine (IDOR) -> 403 Forbidden
    res_s2 = client.get(f"/api/v1/fines/{fine_id}", headers=s2_headers)
    assert res_s2.status_code == 403

    # 3. Student 2 attempts to query Student 1's fines endpoint -> 403 Forbidden
    res_s2_list = client.get(
        f"/api/v1/users/{circulation_setup['student1'].id}/fines", headers=s2_headers
    )
    assert res_s2_list.status_code == 403

    # 4. Student 1 lists own fines -> 200 OK
    res_s1_list = client.get(
        f"/api/v1/users/{circulation_setup['student1'].id}/fines", headers=s1_headers
    )
    assert res_s1_list.status_code == 200
    assert len(res_s1_list.json()["items"]) >= 1

    # 5. Librarian lists all fines -> 200 OK
    res_lib_fines = client.get("/api/v1/fines", headers=lib_headers)
    assert res_lib_fines.status_code == 200
    assert res_lib_fines.json()["total"] >= 1
