"""
Models package.

This __init__.py exists to ensure all SQLAlchemy models are imported
when the package is loaded. This is critical for Alembic autogenerate:
the metadata attached to Base must contain all table definitions before
Alembic inspects it.

Import order respects foreign-key dependencies:
  1. Base (no dependencies)
  2. Category, Role, Permission (no FK to other models)
  3. Book (FK → Category)
  4. User (after association tables defined in role.py)
  5. UserSession (FK → User)
  6. BookCopy (FK → Book)
  7. BorrowRecord (FK → User, BookCopy)
  8. Fine (FK → BorrowRecord)
  9. AuditLog (FK → User)

Do NOT use `Base.metadata.create_all()` here or anywhere else in the app.
Schema creation is exclusively managed by Alembic migrations.
"""

# Association tables (defined in role.py — must be imported before models
# that reference them via secondary=)
from app.models.role import Role, role_permissions, user_roles  # noqa: F401

from app.models.audit_log import AuditLog, AuditAction, AuditStatus  # noqa: F401
from app.models.base import Base, TimestampMixin  # noqa: F401
from app.models.book import Book  # noqa: F401
from app.models.book_copy import BookCopy, CopyStatus  # noqa: F401
from app.models.borrow_record import BorrowRecord, BorrowStatus  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.fine import Fine, FineReason, FineStatus  # noqa: F401
from app.models.permission import Permission  # noqa: F401
from app.models.session import UserSession  # noqa: F401
from app.models.user import AccountStatus, User  # noqa: F401

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    # Association tables
    "user_roles",
    "role_permissions",
    # Models
    "User",
    "AccountStatus",
    "Role",
    "Permission",
    "UserSession",
    "Category",
    "Book",
    "BookCopy",
    "CopyStatus",
    "BorrowRecord",
    "BorrowStatus",
    "Fine",
    "FineStatus",
    "FineReason",
    "AuditLog",
    "AuditAction",
    "AuditStatus",
]
