"""
Fines Service Layer.

Provides data access and formatting for library fines.
"""

from math import ceil
from typing import List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.book import Book
from app.models.book_copy import BookCopy
from app.models.borrow_record import BorrowRecord
from app.models.fine import Fine, FineReason, FineStatus
from app.modules.fines.schemas import FineOut

logger = get_logger(__name__)


class FineService:
    """Business service for querying and managing fines."""

    @staticmethod
    def _format_fine(fine: Fine) -> FineOut:
        """Helper to format a Fine entity into a detailed Pydantic response."""
        user_id = None
        user_email = None
        user_name = None
        book_title = None
        copy_identifier = None

        if fine.borrow_record:
            user_id = fine.borrow_record.user_id
            if fine.borrow_record.user:
                user_email = fine.borrow_record.user.email
                user_name = fine.borrow_record.user.full_name
            if fine.borrow_record.book_copy:
                copy_identifier = fine.borrow_record.book_copy.copy_identifier
                if fine.borrow_record.book_copy.book:
                    book_title = fine.borrow_record.book_copy.book.title

        return FineOut(
            id=fine.id,
            borrow_record_id=fine.borrow_record_id,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            book_title=book_title,
            copy_identifier=copy_identifier,
            amount=fine.amount,
            reason=fine.reason,
            status=fine.status,
            notes=fine.notes,
            created_at=fine.created_at,
            updated_at=fine.updated_at,
        )

    @staticmethod
    def get_fine_by_id(db: Session, fine_id: uuid.UUID) -> FineOut:
        """
        Retrieve a single Fine record by ID.
        Raises NotFoundError if not found.
        """
        fine = (
            db.query(Fine)
            .options(
                joinedload(Fine.borrow_record).joinedload(BorrowRecord.user),
                joinedload(Fine.borrow_record)
                .joinedload(BorrowRecord.book_copy)
                .joinedload(BookCopy.book),
            )
            .filter(Fine.id == fine_id)
            .first()
        )
        if not fine:
            raise NotFoundError(f"Fine with ID '{fine_id}' not found.")

        return FineService._format_fine(fine)

    @staticmethod
    def list_fines(
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        status: Optional[FineStatus] = None,
        reason: Optional[FineReason] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[FineOut], int, int]:
        """
        List fines with filtering and pagination.
        Returns: (items, total_count, total_pages)
        """
        query = (
            db.query(Fine)
            .join(Fine.borrow_record)
            .options(
                joinedload(Fine.borrow_record).joinedload(BorrowRecord.user),
                joinedload(Fine.borrow_record)
                .joinedload(BorrowRecord.book_copy)
                .joinedload(BookCopy.book),
            )
        )

        if user_id is not None:
            query = query.filter(BorrowRecord.user_id == user_id)
        if status is not None:
            query = query.filter(Fine.status == status)
        if reason is not None:
            query = query.filter(Fine.reason == reason)

        total = query.count()
        pages = ceil(total / page_size) if total > 0 else 1
        offset = max(0, (page - 1) * page_size)

        fines = (
            query.order_by(Fine.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        items = [FineService._format_fine(f) for f in fines]
        return items, total, pages


fine_service = FineService()
