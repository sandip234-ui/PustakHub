"""
Audit Logs HTTP Router.

Endpoints:
  - GET /api/v1/audit/logs - Query system audit trails with pagination & filters (requires audit_log:view)
  - GET /api/v1/audit/logs/{audit_id} - Retrieve single audit log by ID (requires audit_log:view)
  - GET /api/v1/audit/actions - List canonical audit actions and categories (requires audit_log:view)
"""

from datetime import datetime
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.audit_log import AuditAction, AuditLog, AuditStatus
from app.modules.audit.schemas import (
    AuditActionInfo,
    AuditActionsResponse,
    AuditLogListResponse,
    AuditLogOut,
)
from app.modules.audit.service import audit_service
from app.modules.permissions.constants import AppPermission
from app.modules.permissions.dependencies import require_permission

router = APIRouter(prefix="/audit", tags=["audit"])


def _to_audit_out(item: AuditLog) -> AuditLogOut:
    return AuditLogOut(
        id=item.id,
        user_id=item.user_id,
        user_email=item.user.email if item.user else None,
        user_name=item.user.full_name if item.user else None,
        action=item.action,
        resource_type=item.resource_type,
        resource_id=item.resource_id,
        status=item.status,
        timestamp=item.timestamp,
        ip_address=item.ip_address,
        user_agent=item.user_agent,
    )


# Centralized categorization of canonical audit action enum values
ACTION_CATEGORY_MAP = {
    # Authentication
    AuditAction.LOGIN_SUCCESS: ("Authentication", "User successfully authenticated with credentials"),
    AuditAction.LOGIN_FAILURE: ("Authentication", "Failed authentication attempt"),
    AuditAction.LOGOUT: ("Authentication", "User terminated active session"),
    AuditAction.TOKEN_REFRESH: ("Authentication", "Session access token refreshed"),
    AuditAction.PASSWORD_CHANGE: ("Authentication", "Account password updated"),
    AuditAction.ACCOUNT_LOCKED: ("Authentication", "Account temporarily locked due to failed attempts"),
    AuditAction.PASSWORD_RESET_REQUESTED: ("Authentication", "Password reset link/token requested"),
    AuditAction.PASSWORD_RESET_COMPLETED: ("Authentication", "Password successfully reset with token"),
    AuditAction.PASSWORD_RESET_FAILED: ("Authentication", "Failed attempt to reset password"),
    # Multi-Factor Authentication
    AuditAction.MFA_ENROLLMENT_STARTED: ("MFA / Security", "MFA enrollment initiated with TOTP key"),
    AuditAction.MFA_ENABLED: ("MFA / Security", "MFA successfully verified and activated"),
    AuditAction.MFA_VERIFICATION_FAILED: ("MFA / Security", "Invalid TOTP code provided during challenge"),
    AuditAction.MFA_RECOVERY_USED: ("MFA / Security", "Emergency single-use recovery code consumed"),
    AuditAction.MFA_DISABLED: ("MFA / Security", "MFA disabled for user account"),
    # User Management & IAM
    AuditAction.USER_CREATED: ("User & IAM", "New user account created"),
    AuditAction.USER_UPDATED: ("User & IAM", "User account profile or status updated"),
    AuditAction.USER_SUSPENDED: ("User & IAM", "User account temporarily suspended"),
    AuditAction.USER_DEACTIVATED: ("User & IAM", "User account deactivated"),
    AuditAction.ROLE_ASSIGNED: ("User & IAM", "Security role granted to user"),
    AuditAction.ROLE_REVOKED: ("User & IAM", "Security role revoked from user"),
    # Library Catalog
    AuditAction.BOOK_CREATED: ("Catalog", "New bibliographic book title added to catalog"),
    AuditAction.BOOK_UPDATED: ("Catalog", "Catalog book bibliographic metadata updated"),
    AuditAction.BOOK_DELETED: ("Catalog", "Book title removed from catalog"),
    # Circulation & Fines
    AuditAction.COPY_ISSUED: ("Circulation", "Physical copy issued/checked out to patron"),
    AuditAction.COPY_RETURNED: ("Circulation", "Physical copy returned and checked in"),
    AuditAction.FINE_ISSUED: ("Circulation", "Late return overdue penalty fine assessed"),
    AuditAction.FINE_WAIVED: ("Circulation", "Outstanding overdue fine waived or adjusted"),
    # System & Permissions
    AuditAction.PERMISSION_GRANTED: ("System / IAM", "Fine-grained permission assigned to role"),
    AuditAction.PERMISSION_REVOKED: ("System / IAM", "Fine-grained permission revoked from role"),
}


@router.get(
    "/actions",
    response_model=AuditActionsResponse,
    status_code=status.HTTP_200_OK,
    summary="List audit action types",
    description="Returns all canonical audit actions and categories. Requires 'audit_log:view' permission.",
    dependencies=[Depends(require_permission(AppPermission.AUDIT_LOG_VIEW.value))],
)
def get_audit_actions() -> AuditActionsResponse:
    action_items: List[AuditActionInfo] = []
    categories_set = set()

    for action in AuditAction:
        cat, desc = ACTION_CATEGORY_MAP.get(action, ("General", "Security or operational event"))
        categories_set.add(cat)
        action_items.append(
            AuditActionInfo(
                action=action.value,
                category=cat,
                description=desc,
            )
        )

    return AuditActionsResponse(
        actions=action_items,
        categories=sorted(list(categories_set)),
    )


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="Query audit logs",
    description=(
        "Retrieves a paginated list of security and operational audit logs. "
        "Supports filtering by search query, user ID, action, outcome status, resource type, and time range. "
        "Requires 'audit_log:view' permission."
    ),
    dependencies=[Depends(require_permission(AppPermission.AUDIT_LOG_VIEW.value))],
)
def get_audit_logs(
    search: Optional[str] = Query(None, description="Search keyword in resource, IP, user name/email"),
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID"),
    action: Optional[AuditAction] = Query(None, description="Filter by action category"),
    audit_status: Optional[AuditStatus] = Query(None, alias="status", description="Filter by outcome status"),
    status: Optional[AuditStatus] = Query(None, description="Alias for outcome status"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g. User, Book, BookCopy)"),
    start_time: Optional[datetime] = Query(None, description="Filter from timestamp (ISO-8601)"),
    end_time: Optional[datetime] = Query(None, description="Filter to timestamp (ISO-8601)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
) -> AuditLogListResponse:
    effective_status = audit_status or status
    items, total = audit_service.query_logs(
        db=db,
        user_id=user_id,
        action=action,
        status=effective_status,
        resource_type=resource_type,
        search=search,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )
    return AuditLogListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_audit_out(item) for item in items],
    )


@router.get(
    "/logs/{audit_id}",
    response_model=AuditLogOut,
    status_code=status.HTTP_200_OK,
    summary="Get single audit log entry",
    description="Retrieves a single audit log record by UUID. Requires 'audit_log:view' permission.",
    dependencies=[Depends(require_permission(AppPermission.AUDIT_LOG_VIEW.value))],
)
def get_audit_log_by_id(
    audit_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> AuditLogOut:
    log = audit_service.get_log_by_id(db=db, audit_id=audit_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log entry with ID '{audit_id}' was not found.",
        )
    return _to_audit_out(log)
