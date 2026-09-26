"""
Pydantic schemas for the Library Catalog module.

Covers:
  - Categories: CategoryCreate, CategoryUpdate, CategoryOut, CategoryListResponse
  - Books: BookCreate, BookUpdate, BookOut, BookListResponse
  - Book Copies: BookCopyCreate, BookCopyUpdate, BookCopyOut, BookCopyListResponse
"""

from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.book_copy import CopyStatus


# ---------------------------------------------------------------------------
# Category Schemas
# ---------------------------------------------------------------------------


class CategoryBase(BaseModel):
    """Base fields for Category."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        description="Unique name of the category / genre (e.g., Fiction, Computer Science)",
    )
    description: Optional[str] = Field(
        None,
        description="Optional detailed description of the category",
    )


class CategoryCreate(CategoryBase):
    """Request payload for creating a new Category."""

    pass


class CategoryUpdate(BaseModel):
    """Request payload for updating an existing Category."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=150,
        description="New unique name of the category",
    )
    description: Optional[str] = Field(
        None,
        description="Updated description of the category",
    )


class CategoryOut(CategoryBase):
    """Response payload for Category entity."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    book_count: int = Field(
        default=0,
        description="Number of books categorized under this category",
    )
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    """Paginated response for Category listing."""

    items: List[CategoryOut]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# Book Schemas
# ---------------------------------------------------------------------------


class BookBase(BaseModel):
    """Base fields for Book."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Full title of the book",
    )
    author: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Primary author(s); multiple authors separated by semicolon",
    )
    isbn: Optional[str] = Field(
        None,
        max_length=20,
        description="Unique ISBN-10 or ISBN-13 identifier (optional)",
    )
    publisher: Optional[str] = Field(
        None,
        max_length=300,
        description="Publisher name",
    )
    publication_year: Optional[int] = Field(
        None,
        ge=1000,
        le=2100,
        description="4-digit publication year",
    )
    description: Optional[str] = Field(
        None,
        description="Summary / abstract of the book",
    )
    category_id: Optional[uuid.UUID] = Field(
        None,
        description="UUID of the associated Category",
    )


class BookCreate(BookBase):
    """Request payload for creating a new Book title."""

    pass


class BookUpdate(BaseModel):
    """Request payload for updating Book metadata."""

    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Updated title of the book",
    )
    author: Optional[str] = Field(
        None,
        min_length=1,
        max_length=500,
        description="Updated author(s)",
    )
    isbn: Optional[str] = Field(
        None,
        max_length=20,
        description="Updated ISBN-10 or ISBN-13 identifier",
    )
    publisher: Optional[str] = Field(
        None,
        max_length=300,
        description="Updated publisher name",
    )
    publication_year: Optional[int] = Field(
        None,
        ge=1000,
        le=2100,
        description="Updated publication year",
    )
    description: Optional[str] = Field(
        None,
        description="Updated book summary",
    )
    category_id: Optional[uuid.UUID] = Field(
        None,
        description="Updated category UUID",
    )


class BookOut(BookBase):
    """Response payload for Book entity."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_name: Optional[str] = Field(
        None,
        description="Name of the associated category",
    )
    total_copies: int = Field(
        default=0,
        description="Total physical copies in inventory",
    )
    available_copies: int = Field(
        default=0,
        description="Number of physical copies currently available for borrowing",
    )
    created_at: datetime
    updated_at: datetime


class BookListResponse(BaseModel):
    """Paginated response for Book catalog queries."""

    items: List[BookOut]
    total: int
    page: int
    page_size: int
    pages: int


# ---------------------------------------------------------------------------
# BookCopy Schemas
# ---------------------------------------------------------------------------


class BookCopyCreate(BaseModel):
    """Request payload for creating a physical BookCopy."""

    copy_identifier: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique barcode/label printed on the physical copy (e.g. 'CC-001')",
    )
    shelf_location: Optional[str] = Field(
        None,
        max_length=100,
        description="Physical shelf location (e.g. 'A3-Shelf2')",
    )
    status: Optional[CopyStatus] = Field(
        default=CopyStatus.AVAILABLE,
        description="Initial physical status of the copy",
    )


class BookCopyUpdate(BaseModel):
    """Request payload for updating an existing BookCopy."""

    copy_identifier: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated unique barcode / identifier",
    )
    shelf_location: Optional[str] = Field(
        None,
        max_length=100,
        description="Updated physical shelf location",
    )
    status: Optional[CopyStatus] = Field(
        None,
        description="Updated copy status (AVAILABLE, BORROWED, MAINTENANCE, LOST)",
    )


class BookCopyOut(BaseModel):
    """Response payload for BookCopy entity."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    book_id: uuid.UUID
    copy_identifier: str
    status: CopyStatus
    shelf_location: Optional[str] = None
    book_title: Optional[str] = Field(
        None,
        description="Title of the parent book record",
    )
    created_at: datetime
    updated_at: datetime


class BookCopyListResponse(BaseModel):
    """Paginated response for BookCopy queries."""

    items: List[BookCopyOut]
    total: int
    page: int
    page_size: int
    pages: int
