"""
Pydantic schemas for the Circulation and Borrowing module.

Covers:
  - BorrowIssueRequest
  - BorrowReturnRequest
  - BorrowRecordOut
  - BorrowRecordListResponse
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.models.borrow_record import BorrowStatus


class BorrowIssueRequest(BaseModel):
    """Request payload for issuing a physical book copy to a user."""

    user_id: uuid.UUID = Field(
        ...,
        description="UUID of the borrower (library member)",
    )
    book_copy_id: uuid.UUID = Field(
        ...,
        description="UUID of the specific physical book copy to issue",
    )
    loan_period_days: Optional[int] = Field(
        None,
        ge=1,
        le=90,
        description="Optional custom loan duration in days (defaults to system setting)",
    )


class BorrowReturnRequest(BaseModel):
    """Request payload for checking in / returning a borrowed copy."""

    returned_at: Optional[datetime] = Field(
        None,
        description="Optional explicit timestamp when the copy was returned (defaults to current time)",
    )


class BorrowRecordOut(BaseModel):
    """Response payload representing a single borrowing transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    user_email: Optional[str] = Field(None, description="Email of the borrower")
    user_name: Optional[str] = Field(None, description="Full name of the borrower")
    book_copy_id: uuid.UUID
    copy_identifier: Optional[str] = Field(None, description="Physical copy barcode / label")
    book_id: Optional[uuid.UUID] = Field(None, description="Parent Book UUID")
    book_title: Optional[str] = Field(None, description="Title of the borrowed book")
    issued_at: datetime
    due_at: datetime
    returned_at: Optional[datetime] = None
    status: BorrowStatus
    is_overdue: bool = Field(default=False, description="True if past due date and not returned on time")
    overdue_days: int = Field(default=0, description="Calculated number of overdue days")
    fine_amount: Optional[Decimal] = Field(None, description="Assessed fine amount if overdue")
    fine_status: Optional[str] = Field(None, description="Payment status of the fine (PENDING, PAID, WAIVED)")
    created_at: datetime
    updated_at: datetime


class BorrowRecordListResponse(BaseModel):
    """Paginated list response for borrowing history."""

    items: List[BorrowRecordOut]
    total: int
    page: int
    page_size: int
    pages: int
