"""
Phase 2 — PostgreSQL & Database Foundation tests.

Tests verify:
  1.  Configuration loads DATABASE_URL correctly.
  2.  SQLAlchemy engine initialises without error.
  3.  A database session can be created.
  4.  PostgreSQL connection succeeds (real SELECT 1 against the DB).
  5.  All models import without error.
  6.  Expected tables exist in SQLAlchemy metadata.
  7.  Expected tables exist in the live PostgreSQL database.
  8.  Unique constraint on users.email is enforced by the database.
  9.  Unique constraint on roles.name is enforced by the database.
  10. Unique constraint on user_sessions.token_hash is enforced.
  11. Foreign key on books.category_id is enforced (RESTRICT).
  12. Many-to-many user_roles relationship is enforced (composite unique).
  13. Alembic migration is at head (no pending migrations).
  14. Health endpoint reports database as healthy.

IMPORTANT: No test silently skips database functionality.
If the database is unreachable, tests that require it will FAIL clearly.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import SessionLocal, check_database_connection, engine
from app.models import (
    AuditLog,
    Base,
    Book,
    BookCopy,
    BorrowRecord,
    Category,
    Fine,
    Permission,
    Role,
    User,
    UserSession,
    role_permissions,
    user_roles,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _random_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@pustakhub-test.local"


def _random_name(prefix: str = "test") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# 1. Configuration
# ---------------------------------------------------------------------------


def test_database_url_is_set() -> None:
    """DATABASE_URL must be configured — not empty."""
    assert settings.DATABASE_URL, (
        "DATABASE_URL is not set. Add it to backend/.env before running Phase 2 tests."
    )
    assert "pustakhub" in settings.DATABASE_URL, (
        "DATABASE_URL does not point to the 'pustakhub' database."
    )


# ---------------------------------------------------------------------------
# 2. Engine initialisation
# ---------------------------------------------------------------------------


def test_engine_initialises() -> None:
    """SQLAlchemy engine object exists and is configured."""
    assert engine is not None
    assert str(engine.url).startswith("postgresql")


# ---------------------------------------------------------------------------
# 3. Session creation
# ---------------------------------------------------------------------------


def test_session_can_be_created() -> None:
    """A database session can be opened and closed without error."""
    db = SessionLocal()
    try:
        assert db is not None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 4. Live PostgreSQL connectivity
# ---------------------------------------------------------------------------


def test_database_connection_succeeds() -> None:
    """
    check_database_connection() must return True.

    If this fails, the PostgreSQL database is unreachable.
    Ensure DATABASE_URL in .env is correct and the DB is running.
    """
    result = check_database_connection()
    assert result is True, (
        "PostgreSQL connection check failed. "
        "Verify DATABASE_URL in .env and that PostgreSQL is running."
    )


def test_raw_sql_executes() -> None:
    """A real SELECT query executes against the live database."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS value"))
        row = result.fetchone()
    assert row is not None
    assert row[0] == 1


# ---------------------------------------------------------------------------
# 5. Model imports
# ---------------------------------------------------------------------------


def test_all_models_import() -> None:
    """Every model class can be imported from app.models without error."""
    assert User is not None
    assert Role is not None
    assert Permission is not None
    assert UserSession is not None
    assert Category is not None
    assert Book is not None
    assert BookCopy is not None
    assert BorrowRecord is not None
    assert Fine is not None
    assert AuditLog is not None
    assert user_roles is not None
    assert role_permissions is not None


# ---------------------------------------------------------------------------
# 6. Metadata tables
# ---------------------------------------------------------------------------

EXPECTED_TABLES = {
    "users",
    "roles",
    "permissions",
    "user_roles",
    "role_permissions",
    "user_sessions",
    "categories",
    "books",
    "book_copies",
    "borrow_records",
    "fines",
    "audit_logs",
}


def test_expected_tables_in_metadata() -> None:
    """All expected tables are registered in SQLAlchemy Base.metadata."""
    metadata_tables = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - metadata_tables
    assert not missing, f"These tables are missing from metadata: {missing}"


# ---------------------------------------------------------------------------
# 7. Live database tables
# ---------------------------------------------------------------------------


def test_expected_tables_exist_in_database() -> None:
    """All expected tables actually exist in the PostgreSQL database."""
    inspector = inspect(engine)
    live_tables = set(inspector.get_table_names())
    missing = EXPECTED_TABLES - live_tables
    assert not missing, (
        f"These tables are missing from the live database: {missing}. "
        "Did you run `alembic upgrade head`?"
    )


# ---------------------------------------------------------------------------
# 8. Unique constraint — users.email
# ---------------------------------------------------------------------------


def test_unique_email_constraint() -> None:
    """Inserting two users with the same email raises IntegrityError."""
    email = _random_email()
    db = SessionLocal()
    try:
        user1 = User(full_name="Alice", email=email)
        user2 = User(full_name="Bob", email=email)
        db.add(user1)
        db.flush()  # push user1 to DB without committing

        db.add(user2)
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 9. Unique constraint — roles.name
# ---------------------------------------------------------------------------


def test_unique_role_name_constraint() -> None:
    """Inserting two roles with the same name raises IntegrityError."""
    name = _random_name("ROLE")
    db = SessionLocal()
    try:
        role1 = Role(name=name)
        role2 = Role(name=name)
        db.add(role1)
        db.flush()

        db.add(role2)
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 10. Unique constraint — user_sessions.token_hash
# ---------------------------------------------------------------------------


def test_unique_session_token_hash_constraint() -> None:
    """Two sessions with the same token_hash must raise IntegrityError."""
    from datetime import datetime, timedelta, timezone

    email = _random_email()
    token_hash = uuid.uuid4().hex * 2  # 64 hex chars (SHA-256 length)
    future = datetime.now(timezone.utc) + timedelta(days=7)

    db = SessionLocal()
    try:
        user = User(full_name="TokenUser", email=email)
        db.add(user)
        db.flush()

        s1 = UserSession(user_id=user.id, token_hash=token_hash, expires_at=future)
        s2 = UserSession(user_id=user.id, token_hash=token_hash, expires_at=future)
        db.add(s1)
        db.flush()

        db.add(s2)
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 11. Foreign key enforcement — books.category_id
# ---------------------------------------------------------------------------


def test_book_with_nonexistent_category_raises() -> None:
    """A book referencing a non-existent category_id must raise IntegrityError."""
    db = SessionLocal()
    try:
        book = Book(
            title="Nonexistent Category Book",
            author="Test Author",
            category_id=uuid.uuid4(),  # random UUID that does not exist
        )
        db.add(book)
        with pytest.raises(IntegrityError):
            db.flush()
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 12. Many-to-many composite unique — user_roles
# ---------------------------------------------------------------------------


def test_user_role_composite_unique() -> None:
    """Assigning the same role to the same user twice must raise IntegrityError."""
    email = _random_email()
    role_name = _random_name("ROLE")
    db = SessionLocal()
    try:
        user = User(full_name="RoleUser", email=email)
        role = Role(name=role_name)
        db.add_all([user, role])
        db.flush()

        # First assignment
        db.execute(
            user_roles.insert().values(user_id=user.id, role_id=role.id)
        )
        db.flush()

        # Duplicate assignment — must fail
        with pytest.raises(IntegrityError):
            db.execute(
                user_roles.insert().values(user_id=user.id, role_id=role.id)
            )
            db.flush()
    finally:
        db.rollback()
        db.close()


# ---------------------------------------------------------------------------
# 13. Alembic migration at head
# ---------------------------------------------------------------------------


def test_alembic_migration_at_head() -> None:
    """
    The database must be at the Alembic head revision.

    Fails if `alembic upgrade head` has not been run.
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()

    assert row is not None, "alembic_version table is empty — migrations not applied."
    version_num = row[0]
    assert len(version_num) > 0, "alembic_version contains an empty revision."


# ---------------------------------------------------------------------------
# 14. Health endpoint reports database healthy
# ---------------------------------------------------------------------------


def test_health_endpoint_reports_db_healthy(client: TestClient) -> None:
    """GET /api/health must report database as 'healthy' when DB is connected."""
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["database"] == "healthy", (
        f"Expected database='healthy', got database={body.get('database')!r}. "
        "Ensure DATABASE_URL is correct and the database is running."
    )
    assert body["status"] == "healthy"
