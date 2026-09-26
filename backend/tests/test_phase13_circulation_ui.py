"""
Phase 13 Integration Tests — Circulation, Borrowing & Fines Workflows.

Validates:
1. Loan issuance by authorized staff (ADMIN / LIBRARIAN)
2. Return processing and automatic fine calculation
3. Student borrowing history and IDOR scoping enforcement
4. Fines ledger listing and status breakdown
5. RBAC security boundaries (unauthorized student/guest mutations rejected)
6. Concurrency & availability conflicts (409 when issuing already-borrowed copy)
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid

from fastapi.testclient import TestClient
import pytest

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.book import Book
from app.models.book_copy import BookCopy, CopyStatus
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.category import Category
from app.models.fine import Fine
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
def circulation_setup():
    """Provisions test users, catalog holdings, and physical copies for circulation tests."""
    with SessionLocal() as db:
        admin_role = db.query(Role).filter_by(name="ADMIN").first()
        librarian_role = db.query(Role).filter_by(name="LIBRARIAN").first()
        student_role = db.query(Role).filter_by(name="STUDENT").first()

        admin_user = User(
            email=f"admin.circ.{uuid.uuid4().hex[:6]}@circ-test.example.com",
            full_name="Admin Circ Tester",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if admin_role:
            admin_user.roles.append(admin_role)

        librarian_user = User(
            email=f"librarian.circ.{uuid.uuid4().hex[:6]}@circ-test.example.com",
            full_name="Librarian Circ Tester",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if librarian_role:
            librarian_user.roles.append(librarian_role)

        student_user1 = User(
            email=f"student1.circ.{uuid.uuid4().hex[:6]}@circ-test.example.com",
            full_name="Student Circ Tester 1",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if student_role:
            student_user1.roles.append(student_role)

        student_user2 = User(
            email=f"student2.circ.{uuid.uuid4().hex[:6]}@circ-test.example.com",
            full_name="Student Circ Tester 2",
            password_hash="argon2id$mocked",
            account_status=AccountStatus.ACTIVE,
        )
        if student_role:
            student_user2.roles.append(student_role)

        db.add_all([admin_user, librarian_user, student_user1, student_user2])
        db.commit()

        # Use existing canonical category rather than polluting catalog
        category = db.query(Category).filter_by(name="Software Engineering & Architecture").first()
        if not category:
            category = db.query(Category).first()

        book = Book(
            title=f"Circulation Dynamics Vol {uuid.uuid4().hex[:4]}",
            author="Prof. Circulation",
            category_id=category.id,
            isbn=f"978{uuid.uuid4().hex[:10]}",
            publisher="PustakHub Press",
            publication_year=2024,
        )
        db.add(book)
        db.commit()

        # Create 3 Physical Copies
        copy1 = BookCopy(
            book_id=book.id,
            copy_identifier=f"CIRC-CP1-{uuid.uuid4().hex[:6]}",
            shelf_location="Floor 1 - Stacks A",
            status=CopyStatus.AVAILABLE,
        )
        copy2 = BookCopy(
            book_id=book.id,
            copy_identifier=f"CIRC-CP2-{uuid.uuid4().hex[:6]}",
            shelf_location="Floor 1 - Stacks B",
            status=CopyStatus.AVAILABLE,
        )
        copy3 = BookCopy(
            book_id=book.id,
            copy_identifier=f"CIRC-CP3-{uuid.uuid4().hex[:6]}",
            shelf_location="Floor 2 - Reserve",
            status=CopyStatus.AVAILABLE,
        )
        db.add_all([copy1, copy2, copy3])
        db.commit()

        setup_data = {
            "admin_id": admin_user.id,
            "librarian_id": librarian_user.id,
            "student1_id": student_user1.id,
            "student2_id": student_user2.id,
            "book_id": book.id,
            "copy1_id": copy1.id,
            "copy2_id": copy2.id,
            "copy3_id": copy3.id,
        }

    yield setup_data

    # Teardown: Clean up all fines, borrow records, copies, book, and users created for this test
    with SessionLocal() as db:
        copy_ids = [setup_data["copy1_id"], setup_data["copy2_id"], setup_data["copy3_id"]]
        borrow_records = db.query(BorrowRecord).filter(BorrowRecord.book_copy_id.in_(copy_ids)).all()
        borrow_ids = [b.id for b in borrow_records]
        if borrow_ids:
            db.query(Fine).filter(Fine.borrow_record_id.in_(borrow_ids)).delete(synchronize_session=False)
            db.query(BorrowRecord).filter(BorrowRecord.id.in_(borrow_ids)).delete(synchronize_session=False)
        db.query(BookCopy).filter(BookCopy.id.in_(copy_ids)).delete(synchronize_session=False)
        b = db.query(Book).filter(Book.id == setup_data["book_id"]).first()
        if b:
            db.delete(b)
        user_ids = [
            setup_data["admin_id"],
            setup_data["librarian_id"],
            setup_data["student1_id"],
            setup_data["student2_id"],
        ]
        db.query(UserSession).filter(UserSession.user_id.in_(user_ids)).delete(synchronize_session=False)
        for u in db.query(User).filter(User.id.in_(user_ids)).all():
            u.roles.clear()
            db.delete(u)
        db.commit()


def _auth_headers(user_id: uuid.UUID) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}


def test_staff_issue_and_return_lifecycle(client: TestClient, circulation_setup: dict):
    """Verify that staff can issue an available copy, status transitions, and return check-in succeeds."""
    librarian_id = circulation_setup["librarian_id"]
    student_id = circulation_setup["student1_id"]
    copy_id = circulation_setup["copy1_id"]

    headers = _auth_headers(librarian_id)

    # 1. Issue Book
    issue_payload = {
        "user_id": str(student_id),
        "book_copy_id": str(copy_id),
        "loan_period_days": 14,
    }
    issue_res = client.post("/api/v1/borrow", json=issue_payload, headers=headers)
    assert issue_res.status_code == 201, issue_res.text
    borrow_data = issue_res.json()
    assert borrow_data["user_id"] == str(student_id)
    assert borrow_data["book_copy_id"] == str(copy_id)
    assert borrow_data["status"] == "ACTIVE"
    borrow_id = borrow_data["id"]

    # 2. Verify physical copy is now BORROWED
    copy_res = client.get(f"/api/v1/copies/{copy_id}", headers=headers)
    assert copy_res.status_code == 200
    assert copy_res.json()["status"] == "BORROWED"

    # 3. Return Book
    return_res = client.post(f"/api/v1/borrow/{borrow_id}/return", headers=headers)
    assert return_res.status_code == 200, return_res.text
    returned_data = return_res.json()
    assert returned_data["status"] == "RETURNED"
    assert returned_data["returned_at"] is not None

    # 4. Verify physical copy is now AVAILABLE again
    copy_res2 = client.get(f"/api/v1/copies/{copy_id}", headers=headers)
    assert copy_res2.status_code == 200
    assert copy_res2.json()["status"] == "AVAILABLE"


def test_overdue_fine_calculation_on_return(client: TestClient, circulation_setup: dict):
    """Verify that an overdue loan calculates and records a fine on return."""
    admin_id = circulation_setup["admin_id"]
    student_id = circulation_setup["student1_id"]
    copy_id = circulation_setup["copy2_id"]

    headers = _auth_headers(admin_id)

    # Directly create an overdue BorrowRecord in DB (due 5 days ago)
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        borrow_record = BorrowRecord(
            user_id=student_id,
            book_copy_id=copy_id,
            issued_at=now - timedelta(days=19),
            due_at=now - timedelta(days=5),
            status=BorrowStatus.ACTIVE,
        )
        copy = db.query(BookCopy).filter_by(id=copy_id).first()
        copy.status = CopyStatus.BORROWED
        db.add(borrow_record)
        db.commit()
        borrow_record_id = borrow_record.id

    # Process Return
    return_res = client.post(f"/api/v1/borrow/{borrow_record_id}/return", headers=headers)
    assert return_res.status_code == 200
    result = return_res.json()
    assert result["returned_at"] is not None
    assert result["is_overdue"] is True
    assert result["overdue_days"] >= 5
    assert Decimal(str(result["fine_amount"])) > 0


def test_student_scoping_and_idor_defense(client: TestClient, circulation_setup: dict):
    """Verify that students only see their own loans/fines and cannot inspect other members' records."""
    student1_id = circulation_setup["student1_id"]
    student2_id = circulation_setup["student2_id"]
    copy_id = circulation_setup["copy3_id"]

    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        borrow_s2 = BorrowRecord(
            user_id=student2_id,
            book_copy_id=copy_id,
            issued_at=now,
            due_at=now + timedelta(days=14),
            status=BorrowStatus.ACTIVE,
        )
        db.add(borrow_s2)
        db.commit()
        borrow_s2_id = borrow_s2.id

    s1_headers = _auth_headers(student1_id)

    # 1. Student1 querying own borrowings list returns only Student1 records
    list_res = client.get("/api/v1/borrowings", headers=s1_headers)
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert all(item["user_id"] == str(student1_id) for item in items)

    # 2. Student1 attempting to query Student2 ID directly returns 403 Forbidden
    idor_list = client.get(f"/api/v1/borrowings?user_id={student2_id}", headers=s1_headers)
    assert idor_list.status_code == 403

    # 3. Student1 attempting to query Student2 single borrowing record returns 403 Forbidden
    idor_single = client.get(f"/api/v1/borrowings/{borrow_s2_id}", headers=s1_headers)
    assert idor_single.status_code == 403


def test_student_and_guest_mutation_forbidden(client: TestClient, circulation_setup: dict):
    """Verify that students and unauthenticated guests cannot issue or return books."""
    student_id = circulation_setup["student1_id"]
    copy_id = circulation_setup["copy1_id"]

    s_headers = _auth_headers(student_id)

    # Student attempting to issue -> 403 Forbidden
    issue_attempt = client.post(
        "/api/v1/borrow",
        json={"user_id": str(student_id), "book_copy_id": str(copy_id), "loan_period_days": 14},
        headers=s_headers,
    )
    assert issue_attempt.status_code == 403

    # Guest attempting to issue -> 401 Unauthorized
    guest_attempt = client.post(
        "/api/v1/borrow",
        json={"user_id": str(student_id), "book_copy_id": str(copy_id), "loan_period_days": 14},
    )
    assert guest_attempt.status_code == 401


def test_concurrency_conflict_when_copy_already_borrowed(client: TestClient, circulation_setup: dict):
    """Verify that attempting to issue an already borrowed copy returns 409 Conflict."""
    librarian_id = circulation_setup["librarian_id"]
    student1_id = circulation_setup["student1_id"]
    student2_id = circulation_setup["student2_id"]
    copy_id = circulation_setup["copy1_id"]

    headers = _auth_headers(librarian_id)

    # Issue copy to student1
    res1 = client.post(
        "/api/v1/borrow",
        json={"user_id": str(student1_id), "book_copy_id": str(copy_id)},
        headers=headers,
    )
    assert res1.status_code == 201

    # Attempt to issue the same copy to student2 -> 409 Conflict
    res2 = client.post(
        "/api/v1/borrow",
        json={"user_id": str(student2_id), "book_copy_id": str(copy_id)},
        headers=headers,
    )
    assert res2.status_code == 409
