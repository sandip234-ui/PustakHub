"""
Fines HTTP Router.

Provides endpoints for:
  - GET /fines
  - GET /fines/{fine_id}
  - GET /users/{user_id}/fines

AUTHORIZATION:
  - Reading fines requires `book:view` (AppPermission.BOOK_VIEW)
  - Students are restricted to viewing only their own fines (IDOR / BOLA defense)
  - Staff (holding `book:issue` or `user:view`) may view and query all fines
"""

from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.fine import FineReason, FineStatus
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.fines.schemas import FineListResponse, FineOut
from app.modules.fines.service import fine_service
from app.modules.permissions.constants import AppPermission
from app.modules.permissions.dependencies import require_permission
from app.modules.permissions.service import permission_service

router = APIRouter(tags=["fines"])


def _is_staff_user(user: User, db: Session) -> bool:
    """Determine if user holds administrative/staff circulation permissions."""
    perms = permission_service.get_user_permissions(user, db)
    return (
        AppPermission.BOOK_ISSUE.value in perms
        or AppPermission.USER_VIEW.value in perms
        or "BOOK_ISSUE" in perms
        or "USER_VIEW" in perms
    )


@router.get(
    "/fines",
    response_model=FineListResponse,
    status_code=status.HTTP_200_OK,
    summary="List fine records",
    description="Retrieves paginated fine records. Students see only their own fines; staff can filter by user. Requires 'book:view'.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def list_fines(
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user UUID (staff only)"),
    fine_status: Optional[FineStatus] = Query(None, alias="status", description="Filter by payment status (PENDING, PAID, WAIVED)"),
    reason: Optional[FineReason] = Query(None, description="Filter by reason (OVERDUE, LOST, DAMAGED)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FineListResponse:
    is_staff = _is_staff_user(current_user, db)

    target_user_id = user_id
    if not is_staff:
        if user_id is not None and user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You do not have permission to inspect another user's fines.",
            )
        target_user_id = current_user.id

    items, total, pages = fine_service.list_fines(
        db=db,
        user_id=target_user_id,
        status=fine_status,
        reason=reason,
        page=page,
        page_size=page_size,
    )
    return FineListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/fines/{fine_id}",
    response_model=FineOut,
    status_code=status.HTTP_200_OK,
    summary="Get fine by ID",
    description="Retrieves a single fine record by UUID. Enforces resource ownership. Requires 'book:view'.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def get_fine(
    fine_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FineOut:
    fine = fine_service.get_fine_by_id(db=db, fine_id=fine_id)

    is_staff = _is_staff_user(current_user, db)
    if not is_staff and fine.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view this fine record.",
        )

    return fine


@router.get(
    "/users/{user_id}/fines",
    response_model=FineListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user fine history",
    description="Lists fines for a specific user. Requires ownership or staff permissions.",
    dependencies=[Depends(require_permission(AppPermission.BOOK_VIEW.value))],
)
def get_user_fines(
    user_id: uuid.UUID,
    fine_status: Optional[FineStatus] = Query(None, alias="status", description="Filter by payment status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FineListResponse:
    is_staff = _is_staff_user(current_user, db)
    if not is_staff and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access another user's fine records.",
        )

    items, total, pages = fine_service.list_fines(
        db=db,
        user_id=user_id,
        status=fine_status,
        page=page,
        page_size=page_size,
    )
    return FineListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )
