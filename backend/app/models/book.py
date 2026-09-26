"""
Book model.

Represents a book title in the library catalogue.
A book title is distinct from a physical copy (see BookCopy).

Example:
    "Clean Code" (Book) → Copy 001, Copy 002, Copy 003 (BookCopy)
"""

import uuid
from typing import Optional

from sqlalchemy import ForeignKey, Index, Integer, SmallInteger, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Book(Base, TimestampMixin):
    """Book title record in the library catalogue."""

    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Full title of the book",
    )
    author: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Primary author(s); multiple authors separated by semicolon",
    )
    # ISBN strategy:
    #   - ISBN-13 is preferred (13 chars + optional hyphens).
    #   - Unique but nullable: not all library books have an ISBN
    #     (e.g., old/rare books, pamphlets).
    isbn: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        comment="ISBN-13 (preferred) or ISBN-10. Nullable for books without an ISBN.",
    )
    publisher: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    publication_year: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        comment="4-digit publication year",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # FK → categories.id — nullable: a book may be uncategorised.
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    category: Mapped[Optional["Category"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Category",
        back_populates="books",
        lazy="select",
    )

    # One-to-many: Book → BookCopy
    copies: Mapped[list["BookCopy"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "BookCopy",
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # ------------------------------------------------------------------
    # Indexes
    # ------------------------------------------------------------------

    __table_args__ = (
        # Full text search helpers — title and author are the primary search fields.
        Index("ix_books_title", "title"),
        Index("ix_books_author", "author"),
        Index("ix_books_isbn", "isbn"),
        Index("ix_books_category_id", "category_id"),
        Index("ix_books_publication_year", "publication_year"),
    )

    def __repr__(self) -> str:
        return f"<Book id={self.id} title={self.title!r} isbn={self.isbn!r}>"
