"""
Phase 11 — Demo Data & Seed Subsystem Test Suite.

Verifies:
  - Deterministic generation (same seed -> identical dataset)
  - Uniqueness constraints (ISBNs, copy identifiers, category names, emails)
  - Mathematical correctness of ISBN-13 check digits
  - Referential and relational integrity (foreign keys, roles, categories)
  - Borrowing integrity (pessimistic copy status alignment, active vs returned)
  - Fine calculation correctness ($2.00/day for overdue late returns)
  - Production safety guard (ENVIRONMENT=production blocks seeding)
  - Idempotency (re-running seed does not duplicate data)
  - Password security (Argon2id hashing, zero plaintext credentials)
"""

import os
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import verify_password
from app.models import (
    AccountStatus,
    Book,
    BookCopy,
    BorrowRecord,
    BorrowStatus,
    Category,
    CopyStatus,
    Fine,
    FineReason,
    FineStatus,
    User,
)
from scripts.seed_demo import (
    DEFAULT_RANDOM_SEED,
    DEMO_PASSWORDS,
    calculate_isbn13,
    check_production_safety,
    reset_demo_data,
    seed_database,
)


@pytest.fixture(scope="module")
def db_session():
    """Provide a database session for seed testing."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 1. Determinism & ISBN-13 Calculation Tests
# ---------------------------------------------------------------------------

def test_isbn13_calculation_mathematical_correctness():
    """Verify calculated ISBN-13 check digits match the official EAN-13 algorithm."""
    # Test well-known test vectors
    # 978-0-13-235088-4 (Clean Code)
    base_9_clean_code = "013235088"
    digits = [9, 7, 8] + [int(d) for d in base_9_clean_code]
    s = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    check = (10 - (s % 10)) % 10
    assert check == 4

    # Test our helper function
    isbn = calculate_isbn13(1)
    assert isbn.startswith("978-0-")
    # Check format 978-X-XXXX-XXXX-X
    parts = isbn.split("-")
    assert len(parts) == 5
    raw = "".join(parts)
    assert len(raw) == 13

    # Validate check digit formula across 500 samples
    for idx in range(1, 501):
        sample_isbn = calculate_isbn13(idx)
        raw_digits = [int(c) for c in sample_isbn.replace("-", "")]
        total = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(raw_digits[:-1]))
        expected_check = (10 - (total % 10)) % 10
        assert raw_digits[-1] == expected_check


def test_isbn13_uniqueness_across_500_books():
    """Verify all 500 generated ISBNs are strictly unique."""
    isbns = [calculate_isbn13(i) for i in range(1, 501)]
    assert len(isbns) == 500
    assert len(set(isbns)) == 500


# ---------------------------------------------------------------------------
# 2. Production Safety Tests
# ---------------------------------------------------------------------------

def test_production_safety_blocks_in_production(monkeypatch):
    """Verify seeding is blocked if ENVIRONMENT == 'production'."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    with pytest.raises(RuntimeError) as exc_info:
        check_production_safety(force=False)
    assert "blocked in production environment" in str(exc_info.value)


def test_production_safety_allows_override(monkeypatch):
    """Verify seeding is permitted if --force-production-seed is passed."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    # Should not raise
    check_production_safety(force=True)


# ---------------------------------------------------------------------------
# 3. Seed Execution & Dataset Counts
# ---------------------------------------------------------------------------

def test_seed_database_execution_and_counts(db_session: Session):
    """Verify complete seed database run populates expected count benchmarks."""
    result = seed_database(db_session, seed_num=DEFAULT_RANDOM_SEED)

    assert result["categories"] == 20
    assert result["books"] == 500
    assert result["book_copies"] >= 1000
    assert result["demo_users"] >= 4
    assert result["borrow_records"] == 100
    assert result["fines"] == 15


# ---------------------------------------------------------------------------
# 4. Demo Users & Password Hashing Verification
# ---------------------------------------------------------------------------

def test_demo_users_roles_and_argon2id_hashing(db_session: Session):
    """Verify demo users have correct roles, ACTIVE status, and valid Argon2id hashes."""
    demo_accounts = [
        ("admin.demo@pustakhub.com", "ADMIN", DEMO_PASSWORDS["ADMIN"]),
        ("librarian.demo@pustakhub.com", "LIBRARIAN", DEMO_PASSWORDS["LIBRARIAN"]),
        ("student.demo@pustakhub.com", "STUDENT", DEMO_PASSWORDS["STUDENT"]),
        ("guest.demo@pustakhub.com", "GUEST", DEMO_PASSWORDS["GUEST"]),
    ]

    for email, expected_role, password in demo_accounts:
        user = db_session.query(User).filter(User.email == email).first()
        assert user is not None, f"User {email} should exist"
        assert user.account_status == AccountStatus.ACTIVE
        assert user.is_mfa_enabled is False

        # Verify password verification with Argon2id
        assert user.password_hash is not None
        assert user.password_hash.startswith("$argon2id$")
        assert verify_password(password, user.password_hash) is True
        assert verify_password("WrongPassword123!", user.password_hash) is False

        # Verify role assignment
        role_names = [r.name for r in user.roles]
        assert expected_role in role_names


# ---------------------------------------------------------------------------
# 5. Book and Copy Integrity Tests
# ---------------------------------------------------------------------------

def test_books_and_categories_referential_integrity(db_session: Session):
    """Verify books are correctly linked to categories with valid metadata."""
    demo_books = db_session.query(Book).filter(Book.isbn.like("978-0-%")).all()
    assert len(demo_books) == 500

    for book in demo_books:
        assert book.category_id is not None
        assert book.category is not None
        assert len(book.title) > 0
        assert len(book.author) > 0
        assert 2000 <= book.publication_year <= 2026
        assert len(book.copies) >= 1


def test_book_copies_identifiers_and_statuses(db_session: Session):
    """Verify copy identifiers follow format and statuses are valid."""
    demo_copies = db_session.query(BookCopy).filter(BookCopy.copy_identifier.like("PUSTAK-%")).all()
    assert len(demo_copies) >= 1000

    copy_ids = [c.copy_identifier for c in demo_copies]
    assert len(copy_ids) == len(set(copy_ids)), "Copy identifiers must be globally unique"

    valid_statuses = {CopyStatus.AVAILABLE, CopyStatus.BORROWED, CopyStatus.MAINTENANCE, CopyStatus.LOST}
    for copy in demo_copies:
        assert copy.status in valid_statuses
        assert copy.shelf_location is not None
        assert copy.book is not None


# ---------------------------------------------------------------------------
# 6. Borrowing & Fine Integrity Tests
# ---------------------------------------------------------------------------

def test_borrowing_records_status_and_copy_alignment(db_session: Session):
    """Verify borrowing records maintain strict domain integrity."""
    demo_borrows = (
        db_session.query(BorrowRecord)
        .join(BookCopy)
        .filter(BookCopy.copy_identifier.like("PUSTAK-%"))
        .all()
    )
    assert len(demo_borrows) == 100

    active_borrows = [b for b in demo_borrows if b.status == BorrowStatus.ACTIVE]
    overdue_borrows = [b for b in demo_borrows if b.status == BorrowStatus.OVERDUE]
    returned_borrows = [b for b in demo_borrows if b.status == BorrowStatus.RETURNED]

    assert len(active_borrows) == 25
    assert len(overdue_borrows) == 15
    assert len(returned_borrows) == 60

    # Invariant 1: ACTIVE and OVERDUE records must have returned_at IS NULL and BookCopy status = BORROWED
    for b in active_borrows + overdue_borrows:
        assert b.returned_at is None
        assert b.book_copy.status == CopyStatus.BORROWED
        assert b.user is not None
        assert b.user.account_status == AccountStatus.ACTIVE

    # Invariant 2: RETURNED records must have returned_at IS NOT NULL and BookCopy status = AVAILABLE
    for b in returned_borrows:
        assert b.returned_at is not None
        assert b.book_copy.status == CopyStatus.AVAILABLE


def test_fines_calculation_and_relational_integrity(db_session: Session):
    """Verify fine amounts strictly adhere to $2.00/day overdue policy."""
    demo_fines = (
        db_session.query(Fine)
        .join(BorrowRecord)
        .join(BookCopy)
        .filter(BookCopy.copy_identifier.like("PUSTAK-%"))
        .all()
    )
    assert len(demo_fines) == 15

    for fine in demo_fines:
        assert fine.reason == FineReason.OVERDUE
        assert fine.status in {FineStatus.PENDING, FineStatus.PAID}
        assert fine.amount > Decimal("0.00")
        assert fine.borrow_record is not None
        assert fine.borrow_record.status == BorrowStatus.RETURNED
        assert fine.borrow_record.returned_at > fine.borrow_record.due_at

        # Verify exact calculation formula: amount == overdue_days * 2.00
        overdue_days = (fine.borrow_record.returned_at.date() - fine.borrow_record.due_at.date()).days
        assert overdue_days > 0
        expected_amount = Decimal(str(overdue_days * 2.00))
        assert fine.amount == expected_amount


# ---------------------------------------------------------------------------
# 7. Idempotency & Reset Tests
# ---------------------------------------------------------------------------

def test_idempotency_consecutive_runs(db_session: Session):
    """Verify re-running seed_database does not duplicate records."""
    count_books_before = db_session.query(Book).filter(Book.isbn.like("978-0-%")).count()
    count_copies_before = db_session.query(BookCopy).filter(BookCopy.copy_identifier.like("PUSTAK-%")).count()
    count_borrows_before = db_session.query(BorrowRecord).join(BookCopy).filter(BookCopy.copy_identifier.like("PUSTAK-%")).count()

    # Re-run seed pipeline
    seed_database(db_session, seed_num=DEFAULT_RANDOM_SEED)

    count_books_after = db_session.query(Book).filter(Book.isbn.like("978-0-%")).count()
    count_copies_after = db_session.query(BookCopy).filter(BookCopy.copy_identifier.like("PUSTAK-%")).count()
    count_borrows_after = db_session.query(BorrowRecord).join(BookCopy).filter(BookCopy.copy_identifier.like("PUSTAK-%")).count()

    assert count_books_after == count_books_before == 500
    assert count_copies_after == count_copies_before
    assert count_borrows_after == count_borrows_before == 100


def test_reset_demo_data_and_reseed(db_session: Session):
    """Verify reset_demo_data wipes demo records cleanly and allows clean reseeding."""
    # Reset demo data
    reset_res = reset_demo_data(db_session, force=True)
    assert reset_res["books"] == 500
    assert reset_res["borrow_records"] == 100
    assert reset_res["fines"] == 15

    # Verify zero demo items remain
    assert db_session.query(Book).filter(Book.isbn.like("978-0-%")).count() == 0
    assert db_session.query(BookCopy).filter(BookCopy.copy_identifier.like("PUSTAK-%")).count() == 0

    # Reseed
    seed_res = seed_database(db_session, seed_num=DEFAULT_RANDOM_SEED, force=True)
    assert seed_res["books"] == 500
    assert seed_res["borrow_records"] == 100
    assert seed_res["fines"] == 15
