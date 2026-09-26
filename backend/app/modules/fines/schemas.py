"""
Pydantic schemas for the Fines module.

Covers:
  - FineOut
  - FineListResponse
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.fine import FineReason, FineStatus


class FineOut(BaseModel):
    """Response payload for a library fine."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    borrow_record_id: uuid.UUID
    user_id: Optional[uuid.UUID] = Field(None, description="Borrower UUID")
    user_email: Optional[str] = Field(None, description="Borrower email")
    user_name: Optional[str] = Field(None, description="Borrower full name")
    book_title: Optional[str] = Field(None, description="Title of the associated book")
    copy_identifier: Optional[str] = Field(None, description="Identifier of the physical copy")
    amount: Decimal = Field(..., description="Fine amount in base currency")
    reason: FineReason = Field(..., description="Reason fine was issued (OVERDUE, LOST, DAMAGED)")
    status: FineStatus = Field(..., description="Payment status (PENDING, PAID, WAIVED)")
    notes: Optional[str] = Field(None, description="Staff notes or explanation")
    created_at: datetime
    updated_at: datetime


class FineListResponse(BaseModel):
    """Paginated list response for fine records."""

    items: List[FineOut]
    total: int
    page: int
    page_size: int
    pages: int
