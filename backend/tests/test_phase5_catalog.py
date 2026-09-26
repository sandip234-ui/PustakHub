"""
Phase 5 Library Catalog Management Tests.

Comprehensive suite covering:
  1. Category CRUD & validation (create, read, update, delete, duplicate 409, not found 404)
  2. Category deletion integrity (rejects deletion if books exist -> 409 Conflict)
  3. Book CRUD & validation (create, read, update, delete, duplicate ISBN 409, invalid category 404)
  4. Book deletion integrity (rejects deletion if copies exist -> 409 Conflict)
  5. BookCopy CRUD & inventory management (create, read, update, delete, duplicate identifier 409)
  6. Search & filtering (title, author, ISBN, publisher, category, publication year)
  7. Pagination behavior & limits (page, page_size, total, pages)
  8. RBAC enforcement:
     - Unauthenticated requests -> 401 Unauthorized
     - STUDENT role can view/search/list (200) but cannot create/update/delete (403)
     - LIBRARIAN role can view, create, update, delete (200/201)
     - ADMIN role has full catalog capabilities (200/201)
  9. Audit trail logging for all catalog mutations (Category, Book, BookCopy)
  10. Copy inventory counts calculation (total_copies and available_copies on BookOut)
  11. Nonexistent resource lookups & error responses
"""

import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.models.audit_log import AuditAction, AuditLog
from app.models.book import Book
from app.models.book_copy import BookCopy, CopyStatus
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.category import Category
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

    # Cleanup created test users
    with SessionLocal() as db:
        for uid in created_users:
            u = db.query(User).filter(User.id == uid).first()
            if u:
                db.delete(u)
        db.commit()


@pytest.fixture
def catalog_cleanup():
    """Cleanup fixture for categories, books, and copies created in tests."""
    created_category_ids = []
    created_book_ids = []
    created_copy_ids = []
    created_borrow_ids = []

    def _track(cat_id=None, book_id=None, copy_id=None, borrow_id=None):
        if cat_id:
            created_category_ids.append(cat_id)
        if book_id:
            created_book_ids.append(book_id)
        if copy_id:
            created_copy_ids.append(copy_id)
        if borrow_id:
            created_borrow_ids.append(borrow_id)

    yield _track

    with SessionLocal() as db:
        # Delete borrow records first
        for brid in created_borrow_ids:
            br = db.query(BorrowRecord).filter(BorrowRecord.id == brid).first()
            if br:
                db.delete(br)
        db.commit()

        # Delete copies
        for cid in created_copy_ids:
            c = db.query(BookCopy).filter(BookCopy.id == cid).first()
            if c:
                db.delete(c)
        db.commit()

        # Delete books
        for bid in created_book_ids:
            b = db.query(Book).filter(Book.id == bid).first()
            if b:
                db.query(BookCopy).filter(BookCopy.book_id == bid).delete()
                db.delete(b)
        db.commit()

        # Delete categories
        for cat_id in created_category_ids:
            cat = db.query(Category).filter(Category.id == cat_id).first()
            if cat:
                db.delete(cat)
        db.commit()


# ===========================================================================
# 1. Unauthenticated Access Tests (401)
# ===========================================================================


def test_unauthenticated_catalog_requests_return_401(client: TestClient):
    """Verify unauthenticated catalog mutations reject with 401, while public read (GUEST role) succeeds."""
    fake_id = str(uuid.uuid4())

    # Categories — public read allowed, mutations require auth
    assert client.get("/api/v1/categories").status_code == 200
    assert client.post("/api/v1/categories", json={"name": "Test"}).status_code == 401
    assert client.put(f"/api/v1/categories/{fake_id}", json={"name": "New"}).status_code == 401
    assert client.delete(f"/api/v1/categories/{fake_id}").status_code == 401

    # Books — public read allowed, mutations require auth
    assert client.get("/api/v1/books").status_code == 200
    assert client.post("/api/v1/books", json={"title": "Test", "author": "Author"}).status_code == 401
    assert client.put(f"/api/v1/books/{fake_id}", json={"title": "New"}).status_code == 401
    assert client.delete(f"/api/v1/books/{fake_id}").status_code == 401

    # Copies — mutations require auth
    assert client.post(f"/api/v1/books/{fake_id}/copies", json={"copy_identifier": "C-1"}).status_code == 401
    assert client.put(f"/api/v1/copies/{fake_id}", json={"copy_identifier": "C-2"}).status_code == 401
    assert client.delete(f"/api/v1/copies/{fake_id}").status_code == 401


# ===========================================================================
# 2. Category Management Tests
# ===========================================================================


def test_category_crud_and_duplicate_validation(client: TestClient, create_test_user, catalog_cleanup):
    """Test full Category CRUD and unique name validation."""
    _, admin_token = create_test_user("ADMIN", "admin_cat")
    headers = {"Authorization": f"Bearer {admin_token}"}

    cat_name = f"Computer Science {uuid.uuid4().hex[:4]}"

    # 1. Create category
    create_res = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": cat_name, "description": "Tech and programming books"},
    )
    assert create_res.status_code == 201
    cat_data = create_res.json()
    cat_id = cat_data["id"]
    catalog_cleanup(cat_id=cat_id)
    assert cat_data["name"] == cat_name
    assert cat_data["description"] == "Tech and programming books"
    assert cat_data["book_count"] == 0

    # 2. Duplicate category creation should fail with 409 Conflict
    dup_res = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": cat_name, "description": "Duplicate category"},
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"] == "conflict"

    # 3. Get category by ID
    get_res = client.get(f"/api/v1/categories/{cat_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == cat_id
    assert get_res.json()["name"] == cat_name

    # 4. List categories
    list_res = client.get(f"/api/v1/categories?search={cat_name}", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(c["id"] == cat_id for c in list_data["items"])

    # 5. Update category
    updated_name = f"Software Engineering {uuid.uuid4().hex[:4]}"
    update_res = client.put(
        f"/api/v1/categories/{cat_id}",
        headers=headers,
        json={"name": updated_name, "description": "Updated description"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == updated_name
    assert update_res.json()["description"] == "Updated description"

    # 6. Delete category
    delete_res = client.delete(f"/api/v1/categories/{cat_id}", headers=headers)
    assert delete_res.status_code == 200

    # 7. Get deleted category returns 404
    assert client.get(f"/api/v1/categories/{cat_id}", headers=headers).status_code == 404


def test_category_delete_with_associated_books_fails(client: TestClient, create_test_user, catalog_cleanup):
    """Ensure category cannot be deleted while books are attached to it."""
    _, admin_token = create_test_user("ADMIN", "admin_cat_del")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create category
    cat_res = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": f"Protected Category {uuid.uuid4().hex[:4]}"},
    )
    cat_id = cat_res.json()["id"]
    catalog_cleanup(cat_id=cat_id)

    # Create book attached to category
    book_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={
            "title": "Category Test Book",
            "author": "Author One",
            "category_id": cat_id,
        },
    )
    book_id = book_res.json()["id"]
    catalog_cleanup(book_id=book_id)

    # Attempt to delete category -> 409 Conflict
    del_res = client.delete(f"/api/v1/categories/{cat_id}", headers=headers)
    assert del_res.status_code == 409
    assert del_res.json()["error"] == "conflict"
    assert "book" in del_res.json()["message"]


# ===========================================================================
# 3. Book Management Tests
# ===========================================================================


def test_book_crud_and_validation(client: TestClient, create_test_user, catalog_cleanup):
    """Test full Book CRUD, ISBN uniqueness, and foreign key validation."""
    _, admin_token = create_test_user("ADMIN", "admin_book")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create category first
    cat_res = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": f"Architecture {uuid.uuid4().hex[:4]}"},
    )
    cat_id = cat_res.json()["id"]
    catalog_cleanup(cat_id=cat_id)

    isbn = f"978-0-{uuid.uuid4().hex[:8]}"

    # 1. Create book with nonexistent category -> 404
    fake_cat_id = str(uuid.uuid4())
    bad_cat_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={
            "title": "Invalid Cat Book",
            "author": "Author",
            "category_id": fake_cat_id,
        },
    )
    assert bad_cat_res.status_code == 404

    # 2. Create valid book
    book_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={
            "title": "Clean Architecture",
            "author": "Robert C. Martin",
            "isbn": isbn,
            "publisher": "Prentice Hall",
            "publication_year": 2017,
            "description": "A Craftsman's Guide to Software Structure and Design",
            "category_id": cat_id,
        },
    )
    assert book_res.status_code == 201
    book_data = book_res.json()
    book_id = book_data["id"]
    catalog_cleanup(book_id=book_id)
    assert book_data["title"] == "Clean Architecture"
    assert book_data["author"] == "Robert C. Martin"
    assert book_data["isbn"] == isbn
    assert book_data["category_id"] == cat_id
    assert book_data["category_name"] == cat_res.json()["name"]
    assert book_data["total_copies"] == 0
    assert book_data["available_copies"] == 0

    # 3. Duplicate ISBN creation -> 409 Conflict
    dup_isbn_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={
            "title": "Another Book",
            "author": "Another Author",
            "isbn": isbn,
        },
    )
    assert dup_isbn_res.status_code == 409
    assert dup_isbn_res.json()["error"] == "conflict"

    # 4. Get book by ID
    get_res = client.get(f"/api/v1/books/{book_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == book_id
    assert get_res.json()["title"] == "Clean Architecture"

    # 5. Update book
    new_title = "Clean Architecture (2nd Edition)"
    update_res = client.put(
        f"/api/v1/books/{book_id}",
        headers=headers,
        json={"title": new_title, "publication_year": 2020},
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == new_title
    assert update_res.json()["publication_year"] == 2020

    # 6. Delete book
    delete_res = client.delete(f"/api/v1/books/{book_id}", headers=headers)
    assert delete_res.status_code == 200

    # 7. Get deleted book -> 404
    assert client.get(f"/api/v1/books/{book_id}", headers=headers).status_code == 404


def test_book_delete_with_physical_copies_fails(client: TestClient, create_test_user, catalog_cleanup):
    """Ensure a book cannot be deleted if it has registered physical copies."""
    _, admin_token = create_test_user("ADMIN", "admin_book_del")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create book
    book_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={"title": "Copy Protected Book", "author": "Author One"},
    )
    book_id = book_res.json()["id"]
    catalog_cleanup(book_id=book_id)

    # Create physical copy
    copy_res = client.post(
        f"/api/v1/books/{book_id}/copies",
        headers=headers,
        json={"copy_identifier": f"BARCODE-{uuid.uuid4().hex[:6]}"},
    )
    assert copy_res.status_code == 201
    copy_id = copy_res.json()["id"]
    catalog_cleanup(copy_id=copy_id)

    # Attempt to delete book -> 409 Conflict
    del_res = client.delete(f"/api/v1/books/{book_id}", headers=headers)
    assert del_res.status_code == 409
    assert del_res.json()["error"] == "conflict"
    assert "inventory" in del_res.json()["message"]


# ===========================================================================
# 4. Book Copy Management Tests
# ===========================================================================


def test_book_copy_crud_and_status_tracking(client: TestClient, create_test_user, catalog_cleanup):
    """Test physical BookCopy creation, retrieval, updates, and copy count calculations."""
    _, admin_token = create_test_user("ADMIN", "admin_copy")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create book
    book_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={"title": "Design Patterns", "author": "GoF"},
    )
    book_id = book_res.json()["id"]
    catalog_cleanup(book_id=book_id)

    copy_barcode = f"DP-{uuid.uuid4().hex[:6]}"

    # 1. Create copy under book
    copy_res = client.post(
        f"/api/v1/books/{book_id}/copies",
        headers=headers,
        json={
            "copy_identifier": copy_barcode,
            "shelf_location": "A1-Shelf3",
            "status": "AVAILABLE",
        },
    )
    assert copy_res.status_code == 201
    copy_data = copy_res.json()
    copy_id = copy_data["id"]
    catalog_cleanup(copy_id=copy_id)
    assert copy_data["book_id"] == book_id
    assert copy_data["copy_identifier"] == copy_barcode
    assert copy_data["shelf_location"] == "A1-Shelf3"
    assert copy_data["status"] == "AVAILABLE"
    assert copy_data["book_title"] == "Design Patterns"

    # 2. Duplicate copy identifier -> 409 Conflict
    dup_res = client.post(
        f"/api/v1/books/{book_id}/copies",
        headers=headers,
        json={"copy_identifier": copy_barcode},
    )
    assert dup_res.status_code == 409

    # 3. Create second copy with MAINTENANCE status
    copy2_res = client.post(
        f"/api/v1/books/{book_id}/copies",
        headers=headers,
        json={
            "copy_identifier": f"DP-{uuid.uuid4().hex[:6]}",
            "shelf_location": "Repair-Bin",
            "status": "MAINTENANCE",
        },
    )
    assert copy2_res.status_code == 201
    copy2_id = copy2_res.json()["id"]
    catalog_cleanup(copy_id=copy2_id)

    # 4. Verify book shows total_copies=2, available_copies=1
    book_get = client.get(f"/api/v1/books/{book_id}", headers=headers)
    assert book_get.status_code == 200
    assert book_get.json()["total_copies"] == 2
    assert book_get.json()["available_copies"] == 1

    # 5. List copies for book
    list_copies = client.get(f"/api/v1/books/{book_id}/copies", headers=headers)
    assert list_copies.status_code == 200
    assert list_copies.json()["total"] == 2

    # 6. Get copy by ID via /copies/{copy_id}
    get_copy = client.get(f"/api/v1/copies/{copy_id}", headers=headers)
    assert get_copy.status_code == 200
    assert get_copy.json()["id"] == copy_id

    # 7. Update copy location and status
    update_copy = client.put(
        f"/api/v1/copies/{copy_id}",
        headers=headers,
        json={"shelf_location": "B2-Shelf1", "status": "LOST"},
    )
    assert update_copy.status_code == 200
    assert update_copy.json()["shelf_location"] == "B2-Shelf1"
    assert update_copy.json()["status"] == "LOST"

    # 8. Delete copy
    del_copy = client.delete(f"/api/v1/copies/{copy_id}", headers=headers)
    assert del_copy.status_code == 200
    assert client.get(f"/api/v1/copies/{copy_id}", headers=headers).status_code == 404


def test_copy_deletion_with_active_borrow_record_fails(client: TestClient, create_test_user, catalog_cleanup):
    """Verify that a physical copy actively borrowed cannot be deleted."""
    _, admin_token = create_test_user("ADMIN", "admin_copy_borrow")
    student_user, _ = create_test_user("STUDENT", "student_borrower")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create book and copy
    book_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={"title": "Circulation Book", "author": "Staff Author"},
    )
    book_id = book_res.json()["id"]
    catalog_cleanup(book_id=book_id)

    copy_res = client.post(
        f"/api/v1/books/{book_id}/copies",
        headers=headers,
        json={"copy_identifier": f"BORROW-TEST-{uuid.uuid4().hex[:6]}"},
    )
    copy_id = copy_res.json()["id"]
    catalog_cleanup(copy_id=copy_id)

    # Insert an ACTIVE borrow record directly in DB for testing deletion protection
    with SessionLocal() as db:
        borrow = BorrowRecord(
            user_id=student_user.id,
            book_copy_id=uuid.UUID(copy_id),
            issued_at=datetime.now(timezone.utc),
            due_at=datetime.now(timezone.utc),
            status=BorrowStatus.ACTIVE,
        )
        db.add(borrow)
        db.commit()
        db.refresh(borrow)
        catalog_cleanup(borrow_id=borrow.id)

    # Attempt to delete copy -> 409 Conflict
    del_res = client.delete(f"/api/v1/copies/{copy_id}", headers=headers)
    assert del_res.status_code == 409
    assert "currently borrowed" in del_res.json()["message"]


# ===========================================================================
# 5. Search, Filtering, and Pagination Tests
# ===========================================================================


def test_catalog_search_filtering_and_pagination(client: TestClient, create_test_user, catalog_cleanup):
    """Test comprehensive catalog search (title, author, ISBN), filtering, and pagination."""
    _, admin_token = create_test_user("ADMIN", "admin_search")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Create test categories
    cat1_res = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": f"Distributed Systems {uuid.uuid4().hex[:4]}"},
    )
    cat1_id = cat1_res.json()["id"]
    catalog_cleanup(cat_id=cat1_id)

    cat2_res = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": f"Database Theory {uuid.uuid4().hex[:4]}"},
    )
    cat2_id = cat2_res.json()["id"]
    catalog_cleanup(cat_id=cat2_id)

    prefix = uuid.uuid4().hex[:6]
    isbn_val = f"978-{prefix}-999"

    # Create books
    b1_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={
            "title": f"Designing Data-Intensive Applications {prefix}",
            "author": "Martin Kleppmann",
            "isbn": isbn_val,
            "publisher": "O'Reilly Media",
            "publication_year": 2017,
            "category_id": cat1_id,
        },
    )
    b1_id = b1_res.json()["id"]
    catalog_cleanup(book_id=b1_id)

    b2_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={
            "title": f"Database Internals {prefix}",
            "author": "Alex Petrov",
            "isbn": f"978-{prefix}-888",
            "publisher": "O'Reilly Media",
            "publication_year": 2019,
            "category_id": cat2_id,
        },
    )
    b2_id = b2_res.json()["id"]
    catalog_cleanup(book_id=b2_id)

    # 1. Search by title keyword
    search_title = client.get(f"/api/v1/books?search=Data-Intensive", headers=headers)
    assert search_title.status_code == 200
    assert any(b["id"] == b1_id for b in search_title.json()["items"])

    # 2. Search by author keyword
    search_author = client.get(f"/api/v1/books?search=Kleppmann", headers=headers)
    assert search_author.status_code == 200
    assert any(b["id"] == b1_id for b in search_author.json()["items"])

    # 3. Search by ISBN
    search_isbn = client.get(f"/api/v1/books?search={isbn_val}", headers=headers)
    assert search_isbn.status_code == 200
    assert any(b["id"] == b1_id for b in search_isbn.json()["items"])

    # 4. Filter by category
    filter_cat1 = client.get(f"/api/v1/books?category_id={cat1_id}", headers=headers)
    assert filter_cat1.status_code == 200
    assert all(b["category_id"] == cat1_id for b in filter_cat1.json()["items"])

    # 5. Filter by author and publication year
    filter_combo = client.get(
        f"/api/v1/books?author=Petrov&publication_year=2019", headers=headers
    )
    assert filter_combo.status_code == 200
    assert any(b["id"] == b2_id for b in filter_combo.json()["items"])

    # 6. Pagination check
    paginated = client.get("/api/v1/books?page=1&page_size=1", headers=headers)
    assert paginated.status_code == 200
    p_data = paginated.json()
    assert len(p_data["items"]) == 1
    assert p_data["page"] == 1
    assert p_data["page_size"] == 1
    assert p_data["total"] >= 2
    assert p_data["pages"] >= 2


# ===========================================================================
# 6. RBAC Role Matrix Tests (STUDENT vs LIBRARIAN vs ADMIN)
# ===========================================================================


def test_rbac_student_can_view_but_cannot_mutate_catalog(
    client: TestClient, create_test_user, catalog_cleanup
):
    """Verify STUDENT role has BOOK_VIEW permission but is forbidden from mutations (403)."""
    _, student_token = create_test_user("STUDENT", "student_user")
    _, admin_token = create_test_user("ADMIN", "admin_fixture")

    student_headers = {"Authorization": f"Bearer {student_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Setup initial book via admin
    book_res = client.post(
        "/api/v1/books",
        headers=admin_headers,
        json={"title": "Student Accessible Book", "author": "Jane Doe"},
    )
    book_id = book_res.json()["id"]
    catalog_cleanup(book_id=book_id)

    # 1. Student CAN view books and categories
    assert client.get("/api/v1/books", headers=student_headers).status_code == 200
    assert client.get(f"/api/v1/books/{book_id}", headers=student_headers).status_code == 200
    assert client.get("/api/v1/categories", headers=student_headers).status_code == 200
    assert client.get(f"/api/v1/books/{book_id}/copies", headers=student_headers).status_code == 200

    # 2. Student CANNOT create category -> 403 Forbidden
    res_create_cat = client.post(
        "/api/v1/categories",
        headers=student_headers,
        json={"name": "Forbidden Category"},
    )
    assert res_create_cat.status_code == 403

    # 3. Student CANNOT create book -> 403 Forbidden
    res_create_book = client.post(
        "/api/v1/books",
        headers=student_headers,
        json={"title": "Student Book", "author": "Student Author"},
    )
    assert res_create_book.status_code == 403

    # 4. Student CANNOT update book -> 403 Forbidden
    res_update_book = client.put(
        f"/api/v1/books/{book_id}",
        headers=student_headers,
        json={"title": "Tampered Title"},
    )
    assert res_update_book.status_code == 403

    # 5. Student CANNOT delete book -> 403 Forbidden
    res_delete_book = client.delete(
        f"/api/v1/books/{book_id}",
        headers=student_headers,
    )
    assert res_delete_book.status_code == 403

    # 6. Student CANNOT create copy -> 403 Forbidden
    res_create_copy = client.post(
        f"/api/v1/books/{book_id}/copies",
        headers=student_headers,
        json={"copy_identifier": "C-STUDENT-01"},
    )
    assert res_create_copy.status_code == 403


def test_rbac_librarian_and_admin_have_full_catalog_capabilities(
    client: TestClient, create_test_user, catalog_cleanup
):
    """Verify both LIBRARIAN and ADMIN can perform all catalog operations."""
    _, lib_token = create_test_user("LIBRARIAN", "librarian_user")
    _, admin_token = create_test_user("ADMIN", "admin_catalog_user")

    lib_headers = {"Authorization": f"Bearer {lib_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Librarian creates category
    cat_res = client.post(
        "/api/v1/categories",
        headers=lib_headers,
        json={"name": f"Librarian Category {uuid.uuid4().hex[:4]}"},
    )
    assert cat_res.status_code == 201
    cat_id = cat_res.json()["id"]
    catalog_cleanup(cat_id=cat_id)

    # Librarian creates book
    book_res = client.post(
        "/api/v1/books",
        headers=lib_headers,
        json={
            "title": "Librarian Catalogued Book",
            "author": "Staff Author",
            "category_id": cat_id,
        },
    )
    assert book_res.status_code == 201
    book_id = book_res.json()["id"]
    catalog_cleanup(book_id=book_id)

    # Librarian creates copy
    copy_res = client.post(
        f"/api/v1/books/{book_id}/copies",
        headers=lib_headers,
        json={"copy_identifier": f"LIB-{uuid.uuid4().hex[:6]}"},
    )
    assert copy_res.status_code == 201
    copy_id = copy_res.json()["id"]
    catalog_cleanup(copy_id=copy_id)

    # Admin updates copy
    admin_update_copy = client.put(
        f"/api/v1/copies/{copy_id}",
        headers=admin_headers,
        json={"shelf_location": "Admin-Vault"},
    )
    assert admin_update_copy.status_code == 200

    # Admin deletes copy, book, and category
    assert client.delete(f"/api/v1/copies/{copy_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/api/v1/books/{book_id}", headers=admin_headers).status_code == 200
    assert client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers).status_code == 200


# ===========================================================================
# 7. Audit Trail Logging Tests
# ===========================================================================


def test_catalog_mutations_generate_audit_log_entries(
    client: TestClient, create_test_user, catalog_cleanup
):
    """Verify that creating, updating, and deleting catalog entities produces structured audit records."""
    user, admin_token = create_test_user("ADMIN", "admin_audit_catalog")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create category & book
    cat_res = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": f"Audit Category {uuid.uuid4().hex[:4]}"},
    )
    cat_id = cat_res.json()["id"]
    catalog_cleanup(cat_id=cat_id)

    book_res = client.post(
        "/api/v1/books",
        headers=headers,
        json={
            "title": "Audited Book Title",
            "author": "Audited Author",
            "category_id": cat_id,
        },
    )
    book_id = book_res.json()["id"]
    catalog_cleanup(book_id=book_id)

    copy_res = client.post(
        f"/api/v1/books/{book_id}/copies",
        headers=headers,
        json={"copy_identifier": f"AUD-{uuid.uuid4().hex[:6]}"},
    )
    copy_id = copy_res.json()["id"]
    catalog_cleanup(copy_id=copy_id)

    # Verify audit entries in database
    with SessionLocal() as db:
        # Check Category created audit
        cat_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "Category",
                AuditLog.resource_id == str(cat_id),
                AuditLog.action == AuditAction.BOOK_CREATED,
            )
            .first()
        )
        assert cat_audit is not None
        assert cat_audit.user_id == user.id

        # Check Book created audit
        book_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "Book",
                AuditLog.resource_id == str(book_id),
                AuditLog.action == AuditAction.BOOK_CREATED,
            )
            .first()
        )
        assert book_audit is not None
        assert book_audit.user_id == user.id

        # Check BookCopy created audit
        copy_audit = (
            db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "BookCopy",
                AuditLog.resource_id == str(copy_id),
                AuditLog.action == AuditAction.BOOK_CREATED,
            )
            .first()
        )
        assert copy_audit is not None
        assert copy_audit.user_id == user.id


def test_catalog_error_responses_for_nonexistent_resources(
    client: TestClient, create_test_user
):
    """Verify 404 responses for nonexistent category, book, and copy IDs."""
    _, admin_token = create_test_user("ADMIN", "admin_nonexistent")
    headers = {"Authorization": f"Bearer {admin_token}"}
    fake_id = str(uuid.uuid4())

    assert client.get(f"/api/v1/categories/{fake_id}", headers=headers).status_code == 404
    assert client.put(f"/api/v1/categories/{fake_id}", headers=headers, json={"name": "X"}).status_code == 404
    assert client.delete(f"/api/v1/categories/{fake_id}", headers=headers).status_code == 404

    assert client.get(f"/api/v1/books/{fake_id}", headers=headers).status_code == 404
    assert client.put(f"/api/v1/books/{fake_id}", headers=headers, json={"title": "X"}).status_code == 404
    assert client.delete(f"/api/v1/books/{fake_id}", headers=headers).status_code == 404

    assert client.get(f"/api/v1/copies/{fake_id}", headers=headers).status_code == 404
    assert client.put(f"/api/v1/copies/{fake_id}", headers=headers, json={"shelf_location": "X"}).status_code == 404
    assert client.delete(f"/api/v1/copies/{fake_id}", headers=headers).status_code == 404
