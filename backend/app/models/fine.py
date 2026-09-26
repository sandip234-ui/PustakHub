"""
Fine model.

A financial penalty associated with a BorrowRecord (e.g., overdue or lost copy).

Fine calculation policy belongs to a later phase.
This model only establishes the schema and relationships.
"""

import enum
import uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FineStatus(str, enum.Enum):
    """Payment state of a fine."""

    PENDING = "PENDING"
    PAID = "PAID"
    WAIVED = "WAIVED"


class FineReason(str, enum.Enum):
    """Why the fine was issued."""

    OVERDUE = "OVERDUE"      # Returned after due date
    LOST = "LOST"            # Copy declared lost
    DAMAGED = "DAMAGED"      # Copy returned in damaged condition


class Fine(Base, TimestampMixin):
    """Financial penalty record for a borrowing transaction."""

    __tablename__ = "fines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # One-to-one: each BorrowRecord can have at most one Fine.
    borrow_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("borrow_records.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        comment="The borrow transaction that generated this fine",
    )

    # Amount in the library's base currency. NUMERIC(10,2) → up to 99,999,999.99
    amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Fine amount in base currency",
    )

    reason: Mapped[FineReason] = mapped_column(
        Enum(FineReason, name="fine_reason_enum", create_constraint=True),
        nullable=False,
    )

    status: Mapped[FineStatus] = mapped_column(
        Enum(FineStatus, name="fine_status_enum", create_constraint=True),
        nullable=False,
        default=FineStatus.PENDING,
        server_default=FineStatus.PENDING.value,
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    borrow_record: Mapped["BorrowRecord"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "BorrowRecord",
        back_populates="fine",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        # Amount must be non-negative
        CheckConstraint("amount >= 0", name="ck_fines_amount_non_negative"),
        Index("ix_fines_borrow_record_id", "borrow_record_id"),
        Index("ix_fines_status", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<Fine id={self.id} amount={self.amount} "
            f"status={self.status} reason={self.reason}>"
        )
