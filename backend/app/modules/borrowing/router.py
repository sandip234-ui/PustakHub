"""
Circulation and Borrowing HTTP Router.

Provides endpoints for:
  - Issuing copies: POST /borrow and POST /borrowings
  - Returning copies: POST /borrow/{borrow_id}/return and POST /borrowings/{borrow_id}/return
  - Borrowing history: GET /borrowings, GET /borrowings/{borrow_id}, GET /users/{user_id}/borrowings

AUTHORIZATION:
  - Issue requires `book:issue` (AppPermission.BOOK_ISSUE)
  - Return requires `book:return` (AppPermission.BOOK_RETURN)
  - History view requires `book:view` (AppPermission.BOOK_VIEW) with strict resource-level scoping
"""

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.borrow_record import BorrowStatus
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.borrowing.schemas import (
    BorrowIssueRequest,
    BorrowRecordListResponse,
    BorrowRecordOut,
    BorrowReturnRequest,
)
from app.modules.borrowing.service import borrowing_service
from app.modules.permissions.constants import AppPermission
from app.modules.permissions.dependencies import require_permission
from app.modules.permissions.service import permission_service

router = APIRouter(tags=["circulation"])


def _extract_request_meta(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and User-Agent from request context."""
    ip = getattr(request.state, "client_ip", None) or (
        request.client.host if request.client else None
    )
    ua = getattr(request.state, "user_agent", None) or request.headers.get("user-agent")
    return ip, ua


def _is_staff_user(user: User, db: Session) -> bool:
    """Determine if user holds circulation staff permissions."""
    perms = permission_service.get_user_permissions(user, db)
    return (
        AppPermission.BOOK_ISSUE.value in perms
        or AppPermission.USER_VIEW.value in perms
        or "BOOK_ISSUE" in perms
        or "USER_VIEW" in perms
    )


# ---------------------------------------------------------------------------
# ISSUE ENDPOINTS
# ---------------------------------------------------------------------------


@router.post(
    "/borrow",
    response_model=BorrowRecordOut,
    status_code=status.HTTP_201_CREATED,
    summary="Issue book copy",
    description="Issues an available physical book copy to an active library user. Requires 'book:issue'.",
)
@router.post(
    "/borrowings",
    response_model=BorrowRecordOut,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def issue_book(
    data: BorrowIssueRequest,
    request: Request,
    current_user: User = Depends(require_permission(AppPermission.BOOK_ISSUE.value)),
    db: Session = Depends(get_db),
) -> BorrowRecordOut:
    ip, ua = _extract_request_meta(request)
    return borrowing_service.issue_book_copy(
        db=db,
        user_id=data.user_id,
        book_copy_id=data.book_copy_id,
        loan_period_days=data.loan_period_days,
        actor_user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


# ---------------------------------------------------------------------------
# RETURN ENDPOINTS
# ---------------------------------------------------------------------------


@router.post(
    "/borrow/{borrow_id}/return",
    response_model=BorrowRecordOut,
    status_code=status.HTTP_200_OK,
    summary="Return borrowed book copy",
    description="Checks in a borrowed book copy, calculates overdue fine if applicable, and updates inventory. Requires 'book:return'.",
)
@router.post(
    "/borrowings/{borrow_id}/return",
    response_model=BorrowRecordOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def return_book(
    borrow_id: uuid.UUID,
    request: Request,
    data: Optional[BorrowReturnRequest] = None,
    current_user: User = Depends(require_permission(AppPermission.BOOK_RETURN.value)),
    db: Session = Depends(get_db),
) -> BorrowRecordOut:
    ip, ua = _extract_request_meta(request)
    returned_at = data.returned_at if data else None
    return borrowing_service.return_book_copy(
        db=db,
        borrow_id=borrow_id,
        returned_at=returned_at,
        actor_user_id=current_user.id,
        ip_address=ip,
        user_agent=ua,
    )


# ---------------------------------------------------------------------------
# QUERY & HISTORY ENDPOINTS
# ---------------------------------------------------------------------------


@router.get(
    "/borrowings",
    response_model=BorrowRecordListResponse,
    status_code=status.HTTP_200_OK,
    summary="List borrowing transactions",
    description="Retrieves paginated borrowing records. Students see only their own history; staff can filter by user. Requires 'book:view'.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def list_borrowings(
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user UUID (staff only)"),
    book_copy_id: Optional[uuid.UUID] = Query(None, description="Filter by physical copy UUID"),
    borrow_status: Optional[BorrowStatus] = Query(None, alias="status", description="Filter by status (ACTIVE, RETURNED, OVERDUE, LOST)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BorrowRecordListResponse:
    is_staff = _is_staff_user(current_user, db)

    target_user_id = user_id
    if not is_staff:
        # Enforce IDOR defense for students: only view own borrowings
        if user_id is not None and user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have permission to inspect another user's borrowing history.",
            )
        target_user_id = current_user.id

    items, total, pages = borrowing_service.list_borrowings(
        db=db,
        user_id=target_user_id,
        book_copy_id=book_copy_id,
        status=borrow_status,
        page=page,
        page_size=page_size,
    )
    return BorrowRecordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/borrowings/{borrow_id}",
    response_model=BorrowRecordOut,
    status_code=status.HTTP_200_OK,
    summary="Get single borrowing record",
    description="Retrieves a single borrowing record by ID. Enforces resource ownership. Requires 'book:view'.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def get_borrowing(
    borrow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BorrowRecordOut:
    record = borrowing_service.get_borrow_record_by_id(db=db, borrow_id=borrow_id)

    is_staff = _is_staff_user(current_user, db)
    if not is_staff and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view this borrowing record.",
        )

    return record


@router.get(
    "/users/{user_id}/borrowings",
    response_model=BorrowRecordListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user borrowing history",
    description="Lists borrowing history for a specific user. Requires ownership or staff permissions.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def get_user_borrowings(
    user_id: uuid.UUID,
    borrow_status: Optional[BorrowStatus] = Query(None, alias="status", description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BorrowRecordListResponse:
    is_staff = _is_staff_user(current_user, db)
    if not is_staff and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access another user's borrowing records.",
        )

    items, total, pages = borrowing_service.list_borrowings(
        db=db,
        user_id=user_id,
        status=borrow_status,
        page=page,
        page_size=page_size,
    )
    return BorrowRecordListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
