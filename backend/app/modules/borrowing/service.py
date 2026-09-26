"""
Circulation and Borrowing Service Layer.

Provides business logic and transaction safety for:
  - Issuing physical book copies with concurrency locking (SELECT FOR UPDATE)
  - Returning physical book copies and calculating return timestamps
  - Overdue detection and automatic Fine generation
  - Querying borrowing transactions and member circulation history
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import ceil
from typing import List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.models.audit_log import AuditAction, AuditStatus
from app.models.book_copy import BookCopy, CopyStatus
from app.models.borrow_record import BorrowRecord, BorrowStatus
from app.models.fine import Fine, FineReason, FineStatus
from app.models.user import AccountStatus, User
from app.modules.audit.service import audit_service
from app.modules.borrowing.schemas import BorrowRecordOut

logger = get_logger(__name__)


class BorrowingService:
    """Business service handling library circulation transactions."""

    @staticmethod
    def _format_record(borrow: BorrowRecord) -> BorrowRecordOut:
        """Helper to transform a BorrowRecord entity into a detailed Pydantic response."""
        now = datetime.now(timezone.utc)
        is_overdue = False
        overdue_days = 0

        if borrow.returned_at is not None:
            if borrow.returned_at > borrow.due_at:
                is_overdue = True
                delta = borrow.returned_at - borrow.due_at
                overdue_days = max(1, ceil(delta.total_seconds() / 86400))
        else:
            if now > borrow.due_at:
                is_overdue = True
                delta = now - borrow.due_at
                overdue_days = max(1, ceil(delta.total_seconds() / 86400))

        fine_amount = None
        fine_status = None
        if borrow.fine:
            fine_amount = borrow.fine.amount
            fine_status = borrow.fine.status.value

        user_email = borrow.user.email if borrow.user else None
        user_name = borrow.user.full_name if borrow.user else None
        copy_identifier = borrow.book_copy.copy_identifier if borrow.book_copy else None
        book_id = borrow.book_copy.book_id if borrow.book_copy else None
        book_title = (
            borrow.book_copy.book.title
            if (borrow.book_copy and borrow.book_copy.book)
            else None
        )

        return BorrowRecordOut(
            id=borrow.id,
            user_id=borrow.user_id,
            user_email=user_email,
            user_name=user_name,
            book_copy_id=borrow.book_copy_id,
            copy_identifier=copy_identifier,
            book_id=book_id,
            book_title=book_title,
            issued_at=borrow.issued_at,
            due_at=borrow.due_at,
            returned_at=borrow.returned_at,
            status=borrow.status,
            is_overdue=is_overdue,
            overdue_days=overdue_days,
            fine_amount=fine_amount,
            fine_status=fine_status,
            created_at=borrow.created_at,
            updated_at=borrow.updated_at,
        )

    @staticmethod
    def issue_book_copy(
        db: Session,
        user_id: uuid.UUID,
        book_copy_id: uuid.UUID,
        loan_period_days: Optional[int] = None,
        actor_user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> BorrowRecordOut:
        """
        Issue a physical book copy to a user.

        CONCURRENCY & INTEGRITY:
          - Acquires row-level exclusive lock on BookCopy (`SELECT ... FOR UPDATE`)
          - Validates borrower account is ACTIVE
          - Validates BookCopy status is AVAILABLE
          - Rejects if an active BorrowRecord already exists for this copy
          - Sets BookCopy status to BORROWED atomically
          - Records audit log event `COPY_ISSUED`
        """
        # 1. Resolve borrower
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundError(f"User with ID '{user_id}' not found.")

        if user.account_status != AccountStatus.ACTIVE:
            raise ConflictError(
                f"User account '{user.email}' is {user.account_status.value} and cannot borrow books."
            )

        # 2. Acquire row-level lock on the physical copy
        copy = (
            db.query(BookCopy)
            .filter(BookCopy.id == book_copy_id)
            .with_for_update()
            .first()
        )
        if not copy:
            raise NotFoundError(f"Book copy with ID '{book_copy_id}' not found.")

        if copy.status != CopyStatus.AVAILABLE:
            if copy.status == CopyStatus.BORROWED:
                raise ConflictError(
                    f"Book copy '{copy.copy_identifier}' is already borrowed."
                )
            elif copy.status == CopyStatus.MAINTENANCE:
                raise ConflictError(
                    f"Book copy '{copy.copy_identifier}' is under maintenance and cannot be issued."
                )
            elif copy.status == CopyStatus.LOST:
                raise ConflictError(
                    f"Book copy '{copy.copy_identifier}' is marked as lost and cannot be issued."
                )
            else:
                raise ConflictError(
                    f"Book copy '{copy.copy_identifier}' is unavailable (status: {copy.status.value})."
                )

        # 3. Check for any existing active borrow record for this copy
        active_borrow = (
            db.query(BorrowRecord)
            .filter(
                BorrowRecord.book_copy_id == copy.id,
                BorrowRecord.status == BorrowStatus.ACTIVE,
            )
            .first()
        )
        if active_borrow:
            raise ConflictError(
                f"Book copy '{copy.copy_identifier}' already has an active borrow record."
            )

        # 4. Calculate loan dates
        loan_days = loan_period_days or settings.DEFAULT_LOAN_PERIOD_DAYS
        issued_at = datetime.now(timezone.utc)
        due_at = issued_at + timedelta(days=loan_days)

        # 5. Create BorrowRecord and update copy status atomically
        borrow = BorrowRecord(
            user_id=user.id,
            book_copy_id=copy.id,
            issued_at=issued_at,
            due_at=due_at,
            status=BorrowStatus.ACTIVE,
        )
        copy.status = CopyStatus.BORROWED

        db.add(borrow)
        db.commit()
        db.refresh(borrow)

        # 6. Audit Trail Logging
        audit_service.log(
            db=db,
            action=AuditAction.COPY_ISSUED,
            user_id=actor_user_id or user.id,
            resource_type="BorrowRecord",
            resource_id=str(borrow.id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Broadcast realtime COPY_ISSUED event
        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.COPY_ISSUED,
                resource_type="BorrowRecord",
                resource_id=str(borrow.id),
                actor_user_id=actor_user_id or user.id,
                target_user_id=user.id,
                data={
                    "book_id": str(copy.book_id),
                    "book_copy_id": str(copy.id),
                    "copy_identifier": copy.copy_identifier,
                    "status": borrow.status.value,
                },
            )
        except Exception as rt_exc:
            logger.debug("Realtime dispatch failed in issue_book_copy: %s", rt_exc)

        return BorrowingService._format_record(borrow)

    @staticmethod
    def return_book_copy(
        db: Session,
        borrow_id: uuid.UUID,
        returned_at: Optional[datetime] = None,
        actor_user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> BorrowRecordOut:
        """
        Process the return / check-in of a borrowed physical copy.

        WORKFLOW:
          - Acquires row-level lock on BorrowRecord (`SELECT ... FOR UPDATE`)
          - Verifies the transaction is currently ACTIVE
          - Computes overdue duration and calculates late fine if applicable
          - Creates Fine record if overdue
          - Marks BookCopy as AVAILABLE
          - Commits atomically and writes audit logs (`COPY_RETURNED`, `FINE_ISSUED`)
        """
        # 1. Lock borrow record
        borrow = (
            db.query(BorrowRecord)
            .filter(BorrowRecord.id == borrow_id)
            .with_for_update()
            .first()
        )
        if not borrow:
            raise NotFoundError(f"Borrow record with ID '{borrow_id}' not found.")

        if borrow.status != BorrowStatus.ACTIVE or borrow.returned_at is not None:
            raise ConflictError(
                f"Borrow record '{borrow_id}' is already closed with status '{borrow.status.value}'."
            )

        # 2. Lock physical copy
        copy = (
            db.query(BookCopy)
            .filter(BookCopy.id == borrow.book_copy_id)
            .with_for_update()
            .first()
        )

        # 3. Determine return timestamp
        return_time = returned_at or datetime.now(timezone.utc)
        borrow.returned_at = return_time

        # 4. Determine overdue status and calculate fine
        fine_record = None
        if return_time > borrow.due_at:
            borrow.status = BorrowStatus.OVERDUE
            delta = return_time - borrow.due_at
            overdue_days = max(1, ceil(delta.total_seconds() / 86400))
            fine_amount = Decimal(str(overdue_days * settings.DAILY_FINE_RATE)).quantize(
                Decimal("0.01")
            )

            # Create Fine record
            fine_record = Fine(
                borrow_record_id=borrow.id,
                amount=fine_amount,
                reason=FineReason.OVERDUE,
                status=FineStatus.PENDING,
                notes=f"Overdue by {overdue_days} day(s) at rate of {settings.DAILY_FINE_RATE}/day.",
            )
            db.add(fine_record)
        else:
            borrow.status = BorrowStatus.RETURNED

        # 5. Mark physical copy available
        if copy:
            copy.status = CopyStatus.AVAILABLE

        db.commit()
        db.refresh(borrow)

        # 6. Audit Trail Logging
        audit_service.log(
            db=db,
            action=AuditAction.COPY_RETURNED,
            user_id=actor_user_id or borrow.user_id,
            resource_type="BorrowRecord",
            resource_id=str(borrow.id),
            status=AuditStatus.SUCCESS,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Broadcast realtime COPY_RETURNED event
        try:
            from app.modules.realtime.events import RealtimeEventType
            from app.modules.realtime.publisher import publish_realtime_event

            publish_realtime_event(
                event_type=RealtimeEventType.COPY_RETURNED,
                resource_type="BorrowRecord",
                resource_id=str(borrow.id),
                actor_user_id=actor_user_id or borrow.user_id,
                target_user_id=borrow.user_id,
                data={
                    "book_copy_id": str(borrow.book_copy_id),
                    "copy_identifier": copy.copy_identifier if copy else None,
                    "status": borrow.status.value,
                },
            )
        except Exception as rt_exc:
            logger.debug("Realtime dispatch failed in return_book_copy: %s", rt_exc)

        if fine_record is not None:
            audit_service.log(
                db=db,
                action=AuditAction.FINE_ISSUED,
                user_id=actor_user_id or borrow.user_id,
                resource_type="Fine",
                resource_id=str(fine_record.id),
                status=AuditStatus.SUCCESS,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            try:
                from app.modules.realtime.events import RealtimeEventType
                from app.modules.realtime.publisher import publish_realtime_event

                publish_realtime_event(
                    event_type=RealtimeEventType.FINE_ISSUED,
                    resource_type="Fine",
                    resource_id=str(fine_record.id),
                    actor_user_id=actor_user_id or borrow.user_id,
                    target_user_id=borrow.user_id,
                    data={
                        "borrow_record_id": str(borrow.id),
                        "amount": str(fine_record.amount),
                        "status": fine_record.status.value,
                    },
                )
            except Exception as rt_exc:
                logger.debug("Realtime dispatch failed for fine_issued: %s", rt_exc)

        return BorrowingService._format_record(borrow)

    @staticmethod
    def get_borrow_record_by_id(db: Session, borrow_id: uuid.UUID) -> BorrowRecordOut:
        """
        Retrieve a single BorrowRecord by ID.
        Raises NotFoundError if not found.
        """
        borrow = (
            db.query(BorrowRecord)
            .options(
                joinedload(BorrowRecord.user),
                joinedload(BorrowRecord.book_copy).joinedload(BookCopy.book),
                joinedload(BorrowRecord.fine),
            )
            .filter(BorrowRecord.id == borrow_id)
            .first()
        )
        if not borrow:
            raise NotFoundError(f"Borrow record with ID '{borrow_id}' not found.")

        return BorrowingService._format_record(borrow)

    @staticmethod
    def list_borrowings(
        db: Session,
        user_id: Optional[uuid.UUID] = None,
        book_copy_id: Optional[uuid.UUID] = None,
        status: Optional[BorrowStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[BorrowRecordOut], int, int]:
        """
        List borrowing transactions with filtering and pagination.
        Returns: (items, total_count, total_pages)
        """
        query = db.query(BorrowRecord).options(
            joinedload(BorrowRecord.user),
            joinedload(BorrowRecord.book_copy).joinedload(BookCopy.book),
            joinedload(BorrowRecord.fine),
        )

        if user_id is not None:
            query = query.filter(BorrowRecord.user_id == user_id)
        if book_copy_id is not None:
            query = query.filter(BorrowRecord.book_copy_id == book_copy_id)
        if status is not None:
            query = query.filter(BorrowRecord.status == status)

        total = query.count()
        pages = ceil(total / page_size) if total > 0 else 1
        offset = max(0, (page - 1) * page_size)

        records = (
            query.order_by(BorrowRecord.issued_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        items = [BorrowingService._format_record(r) for r in records]
        return items, total, pages


borrowing_service = BorrowingService()
