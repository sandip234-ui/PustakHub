"""
BorrowRecord model.

Captures a borrowing transaction between a User and a BookCopy.

One row is created when a copy is issued. `returned_at` is populated
when the copy is returned. Fine records reference the borrow record.

Borrowing service logic belongs to a later phase.
This model establishes the schema and relationships only.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BorrowStatus(str, enum.Enum):
    """Current state of a borrow transaction."""

    ACTIVE = "ACTIVE"        # Copy is currently borrowed
    RETURNED = "RETURNED"    # Copy has been returned on time
    OVERDUE = "OVERDUE"      # Past due date and not yet returned
    LOST = "LOST"            # Copy declared lost by the user or librarian


class BorrowRecord(Base, TimestampMixin):
    """Single borrowing transaction record."""

    __tablename__ = "borrow_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # FK → users.id
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="User who borrowed the copy",
    )

    # FK → book_copies.id
    book_copy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("book_copies.id", ondelete="RESTRICT"),
        nullable=False,
        comment="The specific physical copy that was borrowed",
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when the copy was issued",
    )
    due_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp by which the copy must be returned",
    )
    returned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the copy was actually returned; NULL if still borrowed",
    )

    status: Mapped[BorrowStatus] = mapped_column(
        Enum(BorrowStatus, name="borrow_status_enum", create_constraint=True),
        nullable=False,
        default=BorrowStatus.ACTIVE,
        server_default=BorrowStatus.ACTIVE.value,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    user: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User",
        back_populates="borrow_records",
        lazy="select",
    )

    book_copy: Mapped["BookCopy"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "BookCopy",
        back_populates="borrow_records",
        lazy="select",
    )

    # One-to-one (at most): BorrowRecord → Fine
    fine: Mapped[Optional["Fine"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Fine",
        back_populates="borrow_record",
        uselist=False,
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        Index("ix_borrow_records_user_id", "user_id"),
        Index("ix_borrow_records_book_copy_id", "book_copy_id"),
        Index("ix_borrow_records_status", "status"),
        Index("ix_borrow_records_due_at", "due_at"),
        # Composite: find active borrows for a specific copy quickly
        Index("ix_borrow_records_book_copy_id_status", "book_copy_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<BorrowRecord id={self.id} user_id={self.user_id} "
            f"copy_id={self.book_copy_id} status={self.status}>"
        )
