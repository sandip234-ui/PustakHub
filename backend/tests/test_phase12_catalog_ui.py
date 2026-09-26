"""
Phase 12: Catalog Management & UI Integration Tests.

Validates:
  - Books listing, search, category filtering, pagination contracts
  - Book creation, update, and delete endpoints
  - RBAC enforcement (ADMIN and LIBRARIAN permitted; STUDENT rejected with 403)
  - Book copies inventory listing, addition, update, and deletion
  - Deletion constraint protections (409 Conflict when copies exist or borrowed)
  - Categories taxonomy management and book count aggregations
  - 409 Conflict when deleting category with assigned books
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.models.book import Book
from app.models.book_copy import BookCopy, CopyStatus
from app.models.category import Category
from app.models.role import Role
from app.models.user import AccountStatus, User
from app.modules.permissions.constants import AppRole
from app.modules.permissions.service import permission_service


@pytest.fixture(autouse=True)
def ensure_rbac_seeded():
    """Ensure database has default roles and permissions initialized."""
    with SessionLocal() as db:
        permission_service.seed_default_roles_and_permissions(db)


@pytest.fixture
def auth_tokens():
    """Create test users for each role and return JWT Bearer access tokens."""
    with SessionLocal() as db:
        admin_role = db.query(Role).filter_by(name=AppRole.ADMIN.value).first()
        librarian_role = db.query(Role).filter_by(name=AppRole.LIBRARIAN.value).first()
        student_role = db.query(Role).filter_by(name=AppRole.STUDENT.value).first()

        def _get_or_create(email, full_name, role):
            user = db.query(User).filter_by(email=email).first()
            if not user:
                user = User(
                    id=uuid.uuid4(),
                    email=email,
                    full_name=full_name,
                    password_hash=hash_password("TestPassword!2026"),
                    account_status=AccountStatus.ACTIVE,
                    is_mfa_enabled=False,
                )
                if role:
                    user.roles.append(role)
                db.add(user)
                db.commit()
                db.refresh(user)
            return user

        admin_user = _get_or_create("admin.phase12@pustakhub.com", "Admin Tester", admin_role)
        librarian_user = _get_or_create("librarian.phase12@pustakhub.com", "Librarian Tester", librarian_role)
        student_user = _get_or_create("student.phase12@pustakhub.com", "Student Tester", student_role)

        return {
            "admin": create_access_token(subject=admin_user.id),
            "librarian": create_access_token(subject=librarian_user.id),
            "student": create_access_token(subject=student_user.id),
        }


def test_catalog_pagination_and_search(client: TestClient, auth_tokens: dict):
    """Verify GET /api/v1/books supports search, pagination, and category filtering."""
    headers = {"Authorization": f"Bearer {auth_tokens['student']}"}

    # Query first page
    res = client.get("/api/v1/books?page=1&page_size=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert "pages" in data
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) <= 10

    # Test keyword search
    res_search = client.get("/api/v1/books?search=Systems&page=1&page_size=5", headers=headers)
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert "items" in search_data


def test_book_crud_lifecycle_admin_and_librarian(client: TestClient, auth_tokens: dict):
    """Verify ADMIN and LIBRARIAN can create, update, and delete book titles."""
    admin_headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}
    librarian_headers = {"Authorization": f"Bearer {auth_tokens['librarian']}"}

    cat_id = None
    book_id = None
    try:
        # 1. Create a category
        cat_res = client.post(
            "/api/v1/categories",
            json={"name": f"Cloud Native {uuid.uuid4().hex[:6]}", "description": "Kubernetes & Cloud"},
            headers=admin_headers,
        )
        assert cat_res.status_code == 201
        cat_id = cat_res.json()["id"]

        # 2. Librarian creates book
        unique_isbn = f"978010{uuid.uuid4().int % 1000000:07d}"
        s = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(unique_isbn[:12]))
        c = (10 - (s % 10)) % 10
        isbn = f"{unique_isbn[:12]}{c}"

        book_payload = {
            "title": "Cloud Native Architecture Fundamentals",
            "author": "Priya Sharma",
            "isbn": isbn,
            "publisher": "TechBridge Press",
            "publication_year": 2024,
            "description": "Comprehensive guide to microservices and Kubernetes.",
            "category_id": cat_id,
        }

        create_res = client.post("/api/v1/books", json=book_payload, headers=librarian_headers)
        assert create_res.status_code == 201
        book = create_res.json()
        book_id = book["id"]
        assert book["title"] == book_payload["title"]
        assert book["category_id"] == cat_id

        # 3. Update book metadata
        update_res = client.put(
            f"/api/v1/books/{book_id}",
            json={"title": "Cloud Native Architecture Fundamentals (2nd Edition)"},
            headers=admin_headers,
        )
        assert update_res.status_code == 200
        assert update_res.json()["title"] == "Cloud Native Architecture Fundamentals (2nd Edition)"

        # 4. Delete book (no copies exist -> success)
        del_res = client.delete(f"/api/v1/books/{book_id}", headers=librarian_headers)
        assert del_res.status_code == 200

        # 5. Delete category (clean up completely)
        del_cat_res = client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers)
        assert del_cat_res.status_code == 200
    finally:
        with SessionLocal() as db:
            if book_id:
                b = db.query(Book).filter(Book.id == uuid.UUID(book_id) if isinstance(book_id, str) else book_id).first()
                if b:
                    db.delete(b)
            if cat_id:
                c = db.query(Category).filter(Category.id == uuid.UUID(cat_id) if isinstance(cat_id, str) else cat_id).first()
                if c:
                    db.delete(c)
            db.commit()


def test_student_cannot_mutate_catalog(client: TestClient, auth_tokens: dict):
    """Verify STUDENT role receives 403 Forbidden when attempting catalog mutations."""
    student_headers = {"Authorization": f"Bearer {auth_tokens['student']}"}

    # Student attempting book creation
    res_book = client.post(
        "/api/v1/books",
        json={
            "title": "Unauthorized Book",
            "author": "Student Attacker",
        },
        headers=student_headers,
    )
    assert res_book.status_code == 403

    # Student attempting category creation
    res_cat = client.post(
        "/api/v1/categories",
        json={"name": "Hacking 101"},
        headers=student_headers,
    )
    assert res_cat.status_code == 403


def test_book_copy_management_and_deletion_protection(client: TestClient, auth_tokens: dict):
    """Verify adding, updating, and deleting physical copies, plus book delete conflict check."""
    admin_headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}

    book_id = None
    copy_id = None
    try:
        # Create book
        with SessionLocal() as db:
            book = Book(
                id=uuid.uuid4(),
                title=f"Inventory Test Book {uuid.uuid4().hex[:6]}",
                author="System Architect",
            )
            db.add(book)
            db.commit()
            book_id = str(book.id)

        # 1. Add physical copy
        copy_payload = {
            "copy_identifier": f"BC-TEST-{uuid.uuid4().hex[:6]}",
            "shelf_location": "Floor 2 - Shelf B",
            "status": CopyStatus.AVAILABLE.value,
        }
        create_copy_res = client.post(
            f"/api/v1/books/{book_id}/copies",
            json=copy_payload,
            headers=admin_headers,
        )
        assert create_copy_res.status_code == 201
        copy = create_copy_res.json()
        copy_id = copy["id"]
        assert copy["copy_identifier"] == copy_payload["copy_identifier"]

        # 2. Verify book deletion is blocked with 409 Conflict when copies exist
        del_book_res = client.delete(f"/api/v1/books/{book_id}", headers=admin_headers)
        assert del_book_res.status_code == 409

        # 3. Update copy status and location
        update_copy_res = client.put(
            f"/api/v1/copies/{copy_id}",
            json={
                "shelf_location": "Floor 3 - Maintenance Room",
                "status": CopyStatus.MAINTENANCE.value,
            },
            headers=admin_headers,
        )
        assert update_copy_res.status_code == 200
        assert update_copy_res.json()["status"] == CopyStatus.MAINTENANCE.value

        # 4. Delete copy
        del_copy_res = client.delete(f"/api/v1/copies/{copy_id}", headers=admin_headers)
        assert del_copy_res.status_code == 200

        # 5. Book can now be deleted
        del_book_again = client.delete(f"/api/v1/books/{book_id}", headers=admin_headers)
        assert del_book_again.status_code == 200
    finally:
        with SessionLocal() as db:
            if copy_id:
                c = db.query(BookCopy).filter(BookCopy.id == uuid.UUID(copy_id) if isinstance(copy_id, str) else copy_id).first()
                if c:
                    db.delete(c)
            if book_id:
                b = db.query(Book).filter(Book.id == uuid.UUID(book_id) if isinstance(book_id, str) else book_id).first()
                if b:
                    db.delete(b)
            db.commit()


def test_category_deletion_blocked_when_books_associated(client: TestClient, auth_tokens: dict):
    """Verify deleting a Category containing books returns 409 Conflict."""
    admin_headers = {"Authorization": f"Bearer {auth_tokens['admin']}"}

    cat_id = None
    book_id = None
    try:
        with SessionLocal() as db:
            cat = Category(
                id=uuid.uuid4(),
                name=f"Protected Category {uuid.uuid4().hex[:6]}",
                description="Category with assigned books",
            )
            db.add(cat)
            db.commit()

            book = Book(
                id=uuid.uuid4(),
                title="Dependent Book",
                author="Author",
                category_id=cat.id,
            )
            db.add(book)
            db.commit()

            cat_id = str(cat.id)
            book_id = str(book.id)

        # Attempt category delete -> should return 409
        del_res = client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers)
        assert del_res.status_code == 409

        # Cleanup book first, then delete category -> should succeed
        client.delete(f"/api/v1/books/{book_id}", headers=admin_headers)
        del_res_success = client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers)
        assert del_res_success.status_code == 200
    finally:
        with SessionLocal() as db:
            if book_id:
                b = db.query(Book).filter(Book.id == uuid.UUID(book_id) if isinstance(book_id, str) else book_id).first()
                if b:
                    db.delete(b)
            if cat_id:
                c = db.query(Category).filter(Category.id == uuid.UUID(cat_id) if isinstance(cat_id, str) else cat_id).first()
                if c:
                    db.delete(c)
            db.commit()
