"""
BookCopy model.

A physical copy of a book title.

Example relationship:
    Book: "Clean Code"
    ├── BookCopy: copy_identifier="CC-001", status=AVAILABLE
    ├── BookCopy: copy_identifier="CC-002", status=BORROWED
    └── BookCopy: copy_identifier="CC-003", status=MAINTENANCE
"""

import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class CopyStatus(str, enum.Enum):
    """Physical availability status of a book copy."""

    AVAILABLE = "AVAILABLE"
    BORROWED = "BORROWED"
    MAINTENANCE = "MAINTENANCE"
    LOST = "LOST"


class BookCopy(Base, TimestampMixin):
    """Physical copy of a book title."""

    __tablename__ = "book_copies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # FK → books.id — delete copies when parent book is deleted
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Human-readable identifier printed on the physical copy (e.g., "CC-001")
    copy_identifier: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Human-readable barcode/label on the physical copy",
    )

    status: Mapped[CopyStatus] = mapped_column(
        Enum(CopyStatus, name="copy_status_enum", create_constraint=True),
        nullable=False,
        default=CopyStatus.AVAILABLE,
        server_default=CopyStatus.AVAILABLE.value,
    )

    shelf_location: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Physical shelf location, e.g. 'A3-Shelf2'",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    book: Mapped["Book"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Book",
        back_populates="copies",
        lazy="select",
    )

    borrow_records: Mapped[list["BorrowRecord"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "BorrowRecord",
        back_populates="book_copy",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        UniqueConstraint("copy_identifier", name="uq_book_copies_copy_identifier"),
        Index("ix_book_copies_book_id", "book_id"),
        Index("ix_book_copies_status", "status"),
        # Composite: find available copies of a specific book quickly
        Index("ix_book_copies_book_id_status", "book_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<BookCopy id={self.id} identifier={self.copy_identifier!r} "
            f"status={self.status}>"
        )
