"""
Category model.

A book category groups related books (e.g., Fiction, Computer Science, History).
One category can have many books.
"""

import uuid

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Category(Base, TimestampMixin):
    """Book category / genre."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
        comment="Category name — must be unique (e.g., Fiction, Computer Science)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    # One-to-many: Category → Books
    books: Mapped[list["Book"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Book",
        back_populates="category",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        UniqueConstraint("name", name="uq_categories_name"),
        Index("ix_categories_name", "name"),
    )

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name!r}>"
